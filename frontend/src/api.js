import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
    baseURL: `${API_BASE}/api`,
    headers: { 'Content-Type': 'application/json' },
});

// ── Stats ──
export const getStats = () => api.get('/stats');

// ── Documents ──
export const getDocuments = (params) => api.get('/documents', { params });
export const getDocument = (id) => api.get(`/documents/${id}`);
export const getDocumentPages = (id) => api.get(`/documents/${id}/pages`);
export const getPageRenderUrl = (docId, pageNum) =>
    `${API_BASE}/api/documents/${docId}/pages/${pageNum}/render`;
export const getPdfUrl = (docId) => `${API_BASE}/api/documents/${docId}/pdf`;
export const searchChunks = (docId, search) =>
    api.get(`/documents/${docId}/chunks`, { params: { search } });

// ── Ingest ──
export const uploadDocuments = (files, onProgress) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    return api.post('/ingest', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: onProgress,
    });
};

// ── Admin ──
export const refreshDB = () => api.post('/admin/refresh');
export const removeDuplicates = () => api.post('/admin/remove-duplicates');
export const deleteAll = () => api.delete('/admin/delete-all');

// ── Chat ──
export const chatQuery = (data) => api.post('/chat/query', data);

// ── Graph ──
export const graphQuery = (data) => api.post('/graph/query', data);
export const listEntities = (params) => api.get('/entities', { params });

// ── Annotations ──
export const getAnnotations = (docId) =>
    api.get(`/documents/${docId}/annotations`);
export const createAnnotation = (data) => api.post('/annotations', data);
export const deleteAnnotation = (id) => api.delete(`/annotations/${id}`);

// ── Health ──
export const healthCheck = () => api.get('/health');

export default api;
