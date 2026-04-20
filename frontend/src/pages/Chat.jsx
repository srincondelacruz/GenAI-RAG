import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Bot, User, ArrowLeft, ChevronDown } from 'lucide-react';
import { getAssistants, getAssistant, sendMessage } from '../api/client';

export default function Chat() {
  const { assistantId } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const [assistants, setAssistants] = useState([]);
  const [selectedId, setSelectedId] = useState(assistantId || '');
  const [assistant, setAssistant] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  // Cargar lista de asistentes para el selector
  useEffect(() => {
    getAssistants()
      .then(setAssistants)
      .catch(console.error);
  }, []);

  // Cargar asistente seleccionado
  useEffect(() => {
    if (selectedId) {
      getAssistant(selectedId)
        .then(setAssistant)
        .catch(console.error);
    }
  }, [selectedId]);

  // Si viene por URL, preseleccionar
  useEffect(() => {
    if (assistantId) {
      setSelectedId(assistantId);
    }
  }, [assistantId]);

  // Scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || !selectedId || sending) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setSending(true);

    try {
      const response = await sendMessage(selectedId, userMessage);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ Error: ${err.message}`,
          sources: [],
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-layout">
      {/* Header del chat */}
      <div
        style={{
          padding: 'var(--space-md)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-md)',
        }}
      >
        <button className="btn-icon" onClick={() => navigate('/')} title="Volver">
          <ArrowLeft size={20} />
        </button>

        <div style={{ flex: 1 }}>
          {assistants.length > 0 ? (
            <div style={{ position: 'relative', display: 'inline-block' }}>
              <select
                id="chat-assistant-select"
                value={selectedId}
                onChange={(e) => {
                  setSelectedId(e.target.value);
                  setMessages([]);
                }}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  padding: '0.5rem 2rem 0.5rem 0.75rem',
                  fontSize: '0.9rem',
                  fontFamily: 'var(--font-family)',
                  cursor: 'pointer',
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 0.5rem center',
                }}
              >
                <option value="">Selecciona un asistente...</option>
                {assistants.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              No hay asistentes creados
            </span>
          )}
        </div>

        {assistant && (
          <span
            className="badge badge-accent"
            style={{ fontSize: '0.75rem' }}
          >
            {assistant.document_count} docs
          </span>
        )}
      </div>

      {/* Mensajes */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state" style={{ marginTop: '4rem' }}>
            <Bot size={64} />
            <h3>
              {selectedId
                ? `Chatea con ${assistant?.name || 'tu asistente'}`
                : 'Selecciona un asistente para empezar'}
            </h3>
            <p>
              {selectedId
                ? 'Haz una pregunta sobre los documentos cargados'
                : 'Elige un asistente del menú superior'}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}
          >
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
              {msg.role === 'assistant' && (
                <Bot
                  size={18}
                  style={{
                    color: 'var(--accent-primary)',
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                />
              )}
              <div style={{ flex: 1 }}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                {/* Fuentes */}
                {msg.sources && msg.sources.length > 0 && (
                  <details className="message-sources">
                    <summary>
                      📎 {msg.sources.length} fuentes consultadas
                    </summary>
                    {msg.sources.map((s, j) => (
                      <div key={j} className="source-item">
                        <strong>{s.document}</strong>{' '}
                        <span style={{ color: 'var(--accent-secondary)' }}>
                          ({(s.score * 100).toFixed(0)}% relevancia)
                        </span>
                        <p style={{ marginTop: 4 }}>
                          {s.text.substring(0, 200)}
                          {s.text.length > 200 ? '...' : ''}
                        </p>
                      </div>
                    ))}
                  </details>
                )}
              </div>
              {msg.role === 'user' && (
                <User
                  size={18}
                  style={{ flexShrink: 0, marginTop: 2, opacity: 0.7 }}
                />
              )}
            </div>
          </div>
        ))}

        {sending && (
          <div className="message message-assistant">
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <Bot size={18} style={{ color: 'var(--accent-primary)' }} />
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <form onSubmit={handleSend} className="chat-input-wrapper">
          <input
            id="chat-message-input"
            className="chat-input"
            type="text"
            placeholder={
              selectedId
                ? 'Escribe tu pregunta...'
                : 'Selecciona un asistente primero'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!selectedId || sending}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!input.trim() || !selectedId || sending}
            title="Enviar"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
