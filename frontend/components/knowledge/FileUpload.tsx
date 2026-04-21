"use client";

import React, { useState } from 'react';
import { Upload, X, FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface FileUploadProps {
  knowledgeBaseId: string;
  onSuccess?: () => void;
}

export default function FileUpload({ knowledgeBaseId, onSuccess }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus('idle');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledge_base_id', knowledgeBaseId);

    try {
      // Note: We use raw fetch here because apiFetch handles headers automatically but for FormData we might need to be careful with Content-Type
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`http://localhost:8000/knowledge/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      setStatus('success');
      setFile(null);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message || 'Error uploading file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
      <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
        <Upload className="w-4 h-4 text-primary" />
        Upload Document
      </h3>
      
      {!file ? (
        <label className="border-2 border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all">
          <Upload className="w-8 h-8 text-white/20" />
          <p className="text-xs text-white/40 font-medium">Click or drag PDF, TXT, or DOCX</p>
          <input type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.txt,.docx" />
        </label>
      ) : (
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-primary" />
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate max-w-[150px]">{file.name}</p>
              <p className="text-[10px] text-white/40">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          <button onClick={() => setFile(null)} className="p-1 hover:bg-white/10 rounded-lg text-white/20 hover:text-white transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {status === 'success' && (
        <div className="flex items-center gap-2 text-green-500 text-xs font-bold animate-in fade-in slide-in-from-top-1">
          <CheckCircle2 className="w-4 h-4" /> Document uploaded and indexing...
        </div>
      )}

      {status === 'error' && (
        <div className="flex items-center gap-2 text-red-500 text-xs font-bold animate-in fade-in slide-in-from-top-1">
          <AlertCircle className="w-4 h-4" /> {errorMsg}
        </div>
      )}

      <button
        disabled={!file || uploading}
        onClick={handleUpload}
        className="w-full py-3 bg-primary hover:bg-primary/90 text-white text-xs font-black rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:grayscale active:scale-95 flex items-center justify-center gap-2"
      >
        {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
        {uploading ? 'Processing...' : 'Start Upload'}
      </button>
    </div>
  );
}
