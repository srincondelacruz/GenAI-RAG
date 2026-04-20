import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Upload, FileText, Trash2, File, CheckCircle } from 'lucide-react';
import {
  getAssistant,
  getDocuments,
  uploadDocument,
  deleteDocument,
} from '../api/client';

export default function Documents() {
  const { id: assistantId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [assistant, setAssistant] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragover, setDragover] = useState(false);

  useEffect(() => {
    loadData();
  }, [assistantId]);

  async function loadData() {
    try {
      const [a, docs] = await Promise.all([
        getAssistant(assistantId),
        getDocuments(assistantId),
      ]);
      setAssistant(a);
      setDocuments(docs);
    } catch (err) {
      console.error(err);
      alert('Error cargando datos: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file) {
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(assistantId, file);
      await loadData();
    } catch (err) {
      alert('Error subiendo documento: ' + err.message);
    } finally {
      setUploading(false);
    }
  }

  function onFileSelect(e) {
    handleUpload(e.target.files[0]);
    e.target.value = '';
  }

  function onDrop(e) {
    e.preventDefault();
    setDragover(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  }

  async function handleDelete(docId) {
    if (!confirm('¿Eliminar este documento y sus chunks del vector store?')) return;
    try {
      await deleteDocument(assistantId, docId);
      await loadData();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <button
          className="btn btn-secondary"
          onClick={() => navigate('/')}
          style={{ marginBottom: '1rem' }}
        >
          <ArrowLeft size={16} />
          Volver a asistentes
        </button>
        <h1 className="page-title">
          Documentos de <span>{assistant?.name}</span>
        </h1>
        <p className="page-subtitle">
          Sube archivos PDF o TXT para alimentar a este asistente
        </p>
      </div>

      {/* Zona de subida */}
      <div
        className={`upload-zone ${dragover ? 'dragover' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragover(true);
        }}
        onDragLeave={() => setDragover(false)}
        onDrop={onDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          style={{ display: 'none' }}
          onChange={onFileSelect}
        />
        {uploading ? (
          <>
            <div className="loading-dots" style={{ marginBottom: '1rem' }}>
              <span></span><span></span><span></span>
            </div>
            <p>Procesando documento...</p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
              Extrayendo texto, generando chunks y embeddings
            </p>
          </>
        ) : (
          <>
            <Upload />
            <p style={{ fontWeight: 500, fontSize: '1rem' }}>
              Arrastra un archivo aquí o haz clic para seleccionar
            </p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
              Soporta PDF y TXT
            </p>
          </>
        )}
      </div>

      {/* Lista de documentos */}
      {documents.length === 0 ? (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <FileText size={64} />
          <h3>Sin documentos</h3>
          <p>Sube tu primer documento para empezar</p>
        </div>
      ) : (
        <div className="doc-list">
          {documents.map((doc) => (
            <div key={doc.id} className="doc-item">
              <div className="doc-info">
                <div className="doc-icon">
                  <File size={20} />
                </div>
                <div className="doc-details">
                  <h4>{doc.filename}</h4>
                  <p>
                    {formatSize(doc.file_size)} · {doc.chunk_count} chunks ·{' '}
                    {new Date(doc.created_at).toLocaleDateString('es-ES')}
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-success">
                  <CheckCircle size={10} />
                  Indexado
                </span>
                <button
                  className="btn-icon danger"
                  onClick={() => handleDelete(doc.id)}
                  title="Eliminar documento"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
