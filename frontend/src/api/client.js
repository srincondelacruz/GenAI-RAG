/**
 * client.js — Funciones para comunicarse con el backend FastAPI.
 */

const API_URL = import.meta.env.VITE_API_URL || '/api';

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Error en la petición');
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Asistentes ─────────────────────────────────────────────────

export async function getAssistants() {
  return request('/assistants');
}

export async function getAssistant(id) {
  return request(`/assistants/${id}`);
}

export async function createAssistant(data) {
  return request('/assistants', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAssistant(id, data) {
  return request(`/assistants/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAssistant(id) {
  return request(`/assistants/${id}`, { method: 'DELETE' });
}

// ── Documentos ─────────────────────────────────────────────────

export async function getDocuments(assistantId) {
  return request(`/documents/${assistantId}`);
}

export async function uploadDocument(assistantId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_URL}/documents/${assistantId}`;
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Error subiendo documento');
  }

  return res.json();
}

export async function deleteDocument(assistantId, documentId) {
  return request(`/documents/${assistantId}/${documentId}`, {
    method: 'DELETE',
  });
}

// ── Chat ───────────────────────────────────────────────────────

export async function sendMessage(assistantId, message) {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({
      assistant_id: assistantId,
      message,
    }),
  });
}
