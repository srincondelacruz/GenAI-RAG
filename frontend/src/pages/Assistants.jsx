import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Plus, Pencil, Trash2, FileText, MessageSquare, X } from 'lucide-react';
import {
  getAssistants,
  createAssistant,
  updateAssistant,
  deleteAssistant,
} from '../api/client';

export default function Assistants() {
  const navigate = useNavigate();
  const [assistants, setAssistants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', system_prompt: '' });

  useEffect(() => {
    loadAssistants();
  }, []);

  async function loadAssistants() {
    try {
      const data = await getAssistants();
      setAssistants(data);
    } catch (err) {
      console.error('Error cargando asistentes:', err);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditing(null);
    setForm({
      name: '',
      system_prompt:
        'Eres un asistente útil. Responde basándote en el contexto proporcionado.',
    });
    setShowModal(true);
  }

  function openEdit(assistant) {
    setEditing(assistant);
    setForm({
      name: assistant.name,
      system_prompt: assistant.system_prompt,
    });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      if (editing) {
        await updateAssistant(editing.id, form);
      } else {
        await createAssistant(form);
      }
      setShowModal(false);
      loadAssistants();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  async function handleDelete(id) {
    if (!confirm('¿Estás seguro de que quieres eliminar este asistente y todos sus documentos?')) {
      return;
    }
    try {
      await deleteAssistant(id);
      loadAssistants();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">
            Tus <span>Asistentes</span>
          </h1>
          <p className="page-subtitle">
            Crea y gestiona asistentes alimentados con tus documentos
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreate} id="btn-create-assistant">
          <Plus size={16} />
          Nuevo asistente
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      ) : assistants.length === 0 ? (
        <div className="empty-state">
          <Bot size={64} />
          <h3>No tienes asistentes aún</h3>
          <p>Crea tu primer asistente para empezar</p>
        </div>
      ) : (
        <div className="card-grid">
          {assistants.map((a) => (
            <div key={a.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 className="card-title">{a.name}</h3>
                  <div className="card-meta">
                    <span className="badge badge-accent">
                      <FileText size={10} />
                      {a.document_count} docs
                    </span>
                    <span>
                      {new Date(a.created_at).toLocaleDateString('es-ES')}
                    </span>
                  </div>
                </div>
              </div>
              <p
                style={{
                  marginTop: '0.75rem',
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {a.system_prompt}
              </p>
              <div className="card-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => navigate(`/assistants/${a.id}/documents`)}
                >
                  <FileText size={14} />
                  Documentos
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => navigate(`/chat/${a.id}`)}
                >
                  <MessageSquare size={14} />
                  Chat
                </button>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.25rem' }}>
                  <button className="btn-icon" onClick={() => openEdit(a)} title="Editar">
                    <Pencil size={16} />
                  </button>
                  <button className="btn-icon danger" onClick={() => handleDelete(a.id)} title="Eliminar">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal crear/editar */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="modal-title">
                {editing ? 'Editar asistente' : 'Nuevo asistente'}
              </h2>
              <button className="btn-icon" onClick={() => setShowModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="assistant-name">
                  Nombre
                </label>
                <input
                  id="assistant-name"
                  className="form-input"
                  type="text"
                  placeholder="Ej: Asistente legal, Soporte técnico..."
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="assistant-prompt">
                  System prompt
                </label>
                <textarea
                  id="assistant-prompt"
                  className="form-textarea"
                  placeholder="Define el comportamiento y personalidad del asistente..."
                  rows={4}
                  value={form.system_prompt}
                  onChange={(e) =>
                    setForm({ ...form, system_prompt: e.target.value })
                  }
                  required
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  {editing ? 'Guardar cambios' : 'Crear asistente'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
