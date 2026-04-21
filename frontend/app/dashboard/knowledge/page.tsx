"use client";

import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  BookOpen, 
  Upload, 
  Link as LinkIcon, 
  MoreVertical,
  Trash2,
  FileText,
  AlertCircle,
  CheckCircle2,
  Clock,
  Loader2
} from 'lucide-react';
import { apiFetch } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
}

interface KnowledgeDocument {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
}

interface RAGStats {
  total_vectors: number;
  embedding_dim: number | null;
  total_documents: number;
  embedding_model: string;
}

export default function KnowledgePage() {
  const [bases, setBases] = useState<KnowledgeBase[]>([]);
  const [selectedBaseId, setSelectedBaseId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [search, setSearch] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [baseToDelete, setBaseToDelete] = useState<KnowledgeBase | null>(null);
  const [deletingBase, setDeletingBase] = useState(false);

  useEffect(() => {
    void fetchBases();
    void fetchStats();
  }, []);

  useEffect(() => {
    if (selectedBaseId) {
      void fetchDocuments(selectedBaseId);
    }
  }, [selectedBaseId]);

  const fetchBases = async () => {
    try {
      setError('');
      const resp = await apiFetch('/knowledge/bases');
      if (!resp.ok) {
        throw new Error(await resp.text());
      }
      const data: KnowledgeBase[] = await resp.json();
      setBases(data);
      if (!selectedBaseId && data.length > 0) {
        setSelectedBaseId(data[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load knowledge bases');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (baseId: string) => {
    try {
      setDocsLoading(true);
      const resp = await apiFetch(`/knowledge/bases/${baseId}/documents`);
      if (!resp.ok) {
        throw new Error(await resp.text());
      }
      const data: KnowledgeDocument[] = await resp.json();
      setDocuments(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load documents');
    } finally {
      setDocsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const resp = await apiFetch('/knowledge/stats');
      if (!resp.ok) {
        return;
      }
      const data: RAGStats = await resp.json();
      setStats(data);
    } catch {
      // Non-blocking for page usage
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      setError('');
      const resp = await apiFetch('/knowledge/bases', {
        method: 'POST',
        body: JSON.stringify({ name: newName, description: newDesc })
      });
      if (!resp.ok) {
        throw new Error(await resp.text());
      }

      const created: KnowledgeBase = await resp.json();
      setIsCreating(false);
      setNewName('');
      setNewDesc('');
      setSelectedBaseId(created.id);
      setSuccess('Knowledge base created successfully.');
      await fetchBases();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create knowledge base');
    }
  };

  const handleUploadFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedBaseId) return;

    try {
      setUploading(true);
      setError('');

      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/knowledge/bases/${selectedBaseId}/documents/upload`, {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setSuccess('Document uploaded and indexed successfully.');
      await fetchDocuments(selectedBaseId);
      await fetchBases();
      await fetchStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to upload document');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleAddUrl = async () => {
    if (!selectedBaseId || !urlInput.trim()) return;

    try {
      setUploading(true);
      setError('');
      const resp = await apiFetch(`/knowledge/bases/${selectedBaseId}/documents/url`, {
        method: 'POST',
        body: JSON.stringify({
          url: urlInput,
          knowledge_base_id: selectedBaseId,
        }),
      });

      if (!resp.ok) {
        throw new Error(await resp.text());
      }

      setUrlInput('');
      setSuccess('URL imported and indexed successfully.');
      await fetchDocuments(selectedBaseId);
      await fetchBases();
      await fetchStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add URL');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!selectedBaseId) return;
    try {
      setError('');
      const resp = await apiFetch(`/knowledge/documents/${docId}`, {
        method: 'DELETE',
      });
      if (!resp.ok) {
        throw new Error(await resp.text());
      }
      setSuccess('Document deleted successfully.');
      await fetchDocuments(selectedBaseId);
      await fetchBases();
      await fetchStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete document');
    }
  };

  const handleDeleteBase = async (baseId: string) => {
    try {
      setDeletingBase(true);
      setError('');
      const resp = await apiFetch(`/knowledge/bases/${baseId}`, { method: 'DELETE' });
      if (!resp.ok && resp.status !== 204) {
        throw new Error(await resp.text());
      }
      setSuccess('Knowledge base deleted successfully.');
      setBaseToDelete(null);
      if (selectedBaseId === baseId) {
        setSelectedBaseId(null);
        setDocuments([]);
      }
      await fetchBases();
      await fetchStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete base');
    } finally {
      setDeletingBase(false);
    }
  };

  const handleRebuildIndex = async () => {
    try {
      setRebuilding(true);
      setError('');
      const resp = await apiFetch('/knowledge/rebuild-index', { method: 'POST' });
      if (!resp.ok) {
        throw new Error(await resp.text());
      }
      setSuccess('Vector index rebuilt successfully.');
      await fetchStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to rebuild index');
    } finally {
      setRebuilding(false);
    }
  };

  const filteredBases = bases.filter((base) => {
    const term = search.toLowerCase();
    return base.name.toLowerCase().includes(term) || (base.description || '').toLowerCase().includes(term);
  });

  const selectedBase = bases.find((base) => base.id === selectedBaseId) || null;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-end justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Knowledge Bases</h1>
          <p className="text-white/50 text-sm">Manage the documents and URLs that power your AI assistant.</p>
        </div>
        <button 
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-2 px-5 py-3 bg-primary hover:bg-primary/90 text-white font-bold rounded-xl shadow-lg transition-all active:scale-[0.98]"
        >
          <Plus className="w-5 h-5" />
          Create New Base
        </button>
      </div>

      {(error || success) && (
        <div className="space-y-3">
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-300">
              <AlertCircle className="w-5 h-5" />
              <p className="text-sm">{error}</p>
            </div>
          )}
          {success && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center gap-3 text-emerald-300">
              <CheckCircle2 className="w-5 h-5" />
              <p className="text-sm">{success}</p>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-white/50 uppercase tracking-wider">Knowledge Bases</p>
          <p className="text-2xl font-black text-white mt-2">{bases.length}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-white/50 uppercase tracking-wider">Indexed Docs</p>
          <p className="text-2xl font-black text-white mt-2">{stats?.total_documents ?? 0}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-white/50 uppercase tracking-wider">Vectors</p>
          <p className="text-2xl font-black text-white mt-2">{stats?.total_vectors ?? 0}</p>
        </div>
        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-white/50 uppercase tracking-wider">Embedding</p>
          <p className="text-xs font-bold text-white/80 mt-3 truncate">{stats?.embedding_model ?? 'N/A'}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 py-2">
        <div className="flex-1 relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search knowledge bases..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm font-medium"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1,2,3].map(i => (
            <div key={i} className="h-64 glass-card rounded-2xl border border-white/5 animate-pulse" />
          ))}
        </div>
      ) : bases.length === 0 && !isCreating ? (
        <div className="py-32 flex flex-col items-center justify-center text-center space-y-6 flex-1">
          <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/10">
            <BookOpen className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <h4 className="text-xl font-bold text-white tracking-tight">No knowledge bases yet</h4>
            <p className="text-sm text-white/40 max-w-sm">Create your first knowledge base to start indexing documents for your AI.</p>
          </div>
          <button 
            onClick={() => setIsCreating(true)}
            className="text-primary font-bold hover:underline transition-all"
          >
            Create New Base →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          {isCreating && (
            <div className="glass-card p-6 rounded-2xl border-2 border-primary/50 flex flex-col gap-4 animate-in zoom-in-95 duration-200">
              <h3 className="text-lg font-bold text-white">Create New Base</h3>
              <div className="space-y-4">
                <input 
                  autoFocus
                  placeholder="Base Name (e.g. Sales SOPs)"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary transition-all font-bold placeholder:font-normal"
                />
                <textarea 
                  placeholder="Short description..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary transition-all h-20"
                />
              </div>
              <div className="flex gap-2 mt-2">
                <button 
                  onClick={handleCreate}
                  disabled={!newName.trim()}
                  className="flex-1 py-2.5 bg-primary text-white text-xs font-black rounded-lg hover:bg-primary/90 transition-all disabled:opacity-50"
                >
                  Confirm Create
                </button>
                <button 
                  onClick={() => setIsCreating(false)}
                  className="flex-1 py-2.5 bg-white/5 text-white/50 text-xs font-bold rounded-lg hover:bg-white/10 border border-white/10 transition-all font-bold"
                >
                 Cancel
                </button>
              </div>
            </div>
          )}

          {filteredBases.map((base) => (
            <div
              key={base.id}
              className={`glass-card p-6 rounded-2xl border flex flex-col group relative transition-all hover:translate-y-[-2px] duration-300 ${selectedBaseId === base.id ? 'border-primary/50' : 'border-white/5 hover:border-white/10'}`}
            >
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500">
                  <BookOpen className="w-6 h-6" />
                </div>
                <button
                  onClick={() => setBaseToDelete(base)}
                  className="p-2 text-white/20 hover:text-red-300 transition-colors"
                  title="Delete knowledge base"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-8 flex-1">
                <h3 className="text-lg font-black text-white group-hover:text-primary transition-colors duration-300 tracking-tight">{base.name}</h3>
                <p className="text-xs text-white/40 mt-1.5 leading-relaxed line-clamp-2 min-h-[32px]">{base.description}</p>
              </div>

              <div className="mt-8 pt-8 border-t border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-white/20" />
                  <span className="text-[10px] font-black text-white tracking-widest uppercase">{base.document_count} Documents</span>
                </div>
                <button
                  onClick={() => setSelectedBaseId(base.id)}
                  className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[10px] font-black text-white transition-all uppercase tracking-widest"
                >
                  Manage →
                </button>
              </div>
            </div>
          ))}
          </div>

          <div className="glass-card p-6 rounded-2xl border border-white/5 h-fit space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-black text-white">Base Manager</h3>
              <button
                onClick={() => void handleRebuildIndex()}
                disabled={rebuilding}
                className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 disabled:opacity-50"
              >
                {rebuilding ? 'Rebuilding...' : 'Rebuild Index'}
              </button>
            </div>

            {!selectedBase ? (
              <p className="text-sm text-white/50">Select a knowledge base to manage documents.</p>
            ) : (
              <>
                <div className="space-y-2">
                  <p className="text-xs text-white/50 uppercase tracking-wider">Selected Base</p>
                  <p className="text-sm font-bold text-white">{selectedBase.name}</p>
                </div>

                <div className="space-y-3">
                  <label className="text-xs text-white/50 uppercase tracking-wider">Upload file</label>
                  <label className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 border border-white/10 rounded-lg cursor-pointer hover:bg-white/10 text-sm text-white">
                    {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                    <span>{uploading ? 'Uploading...' : 'Choose file (.pdf, .txt, .md, .docx, .html)'}</span>
                    <input type="file" className="hidden" onChange={handleUploadFile} disabled={uploading} />
                  </label>
                </div>

                <div className="space-y-3">
                  <label className="text-xs text-white/50 uppercase tracking-wider">Add URL</label>
                  <div className="flex gap-2">
                    <input
                      value={urlInput}
                      onChange={(e) => setUrlInput(e.target.value)}
                      placeholder="https://example.com/doc"
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30"
                    />
                    <button
                      onClick={() => void handleAddUrl()}
                      disabled={uploading || !urlInput.trim()}
                      className="px-3 py-2 bg-primary rounded-lg text-white text-sm font-bold disabled:opacity-50"
                    >
                      <LinkIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-xs text-white/50 uppercase tracking-wider">Documents</p>
                  {docsLoading ? (
                    <div className="flex items-center gap-2 text-white/50 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading documents...
                    </div>
                  ) : documents.length === 0 ? (
                    <p className="text-sm text-white/40">No documents in this base yet.</p>
                  ) : (
                    <div className="space-y-2 max-h-72 overflow-auto pr-1">
                      {documents.map((doc) => (
                        <div key={doc.id} className="p-3 bg-white/5 border border-white/10 rounded-lg flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <p className="text-sm text-white truncate">{doc.filename}</p>
                            <p className="text-xs text-white/40">{doc.chunk_count} chunks • {doc.file_type}</p>
                          </div>
                          <button
                            onClick={() => void handleDeleteDocument(doc.id)}
                            className="p-2 text-white/30 hover:text-red-300"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {baseToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !deletingBase && setBaseToDelete(null)}
            aria-label="Close delete confirmation"
          />
          <div className="relative w-full max-w-md glass-card rounded-2xl border border-white/10 p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-300" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Delete Knowledge Base</h3>
                <p className="text-xs text-white/50">This action cannot be undone.</p>
              </div>
            </div>

            <div className="text-sm text-white/80">
              Are you sure you want to delete <span className="font-bold text-white">{baseToDelete.name}</span>?
              All documents in this base will be removed.
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setBaseToDelete(null)}
                disabled={deletingBase}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/80 hover:bg-white/10 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={() => void handleDeleteBase(baseToDelete.id)}
                disabled={deletingBase}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold disabled:opacity-50 flex items-center gap-2"
              >
                {deletingBase ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Delete Base
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
