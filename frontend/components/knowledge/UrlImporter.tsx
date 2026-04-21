"use client";

import React, { useState } from 'react';
import { Link as LinkIcon, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface UrlImporterProps {
  knowledgeBaseId: string;
  onSuccess?: () => void;
}

export default function UrlImporter({ knowledgeBaseId, onSuccess }: UrlImporterProps) {
  const [url, setUrl] = useState('');
  const [importing, setImporting] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleImport = async () => {
    if (!url.trim()) return;
    setImporting(true);
    setStatus('idle');

    try {
      const response = await apiFetch('/knowledge/documents/url', {
        method: 'POST',
        body: JSON.stringify({ url: url.trim(), knowledge_base_id: knowledgeBaseId })
      });

      if (!response.ok) throw new Error('Crawl failed');

      setStatus('success');
      setUrl('');
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message || 'Error processing URL');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
      <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
        <LinkIcon className="w-4 h-4 text-primary" />
        Import from Website
      </h3>
      
      <div className="space-y-4">
        <input 
          placeholder="https://docs.company.com/pages"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all font-medium placeholder:text-white/20"
        />

        {status === 'success' && (
          <div className="flex items-center gap-2 text-green-500 text-xs font-bold animate-in fade-in slide-in-from-top-1">
            <CheckCircle2 className="w-4 h-4" /> URL import started...
          </div>
        )}

        {status === 'error' && (
          <div className="flex items-center gap-2 text-red-500 text-xs font-bold animate-in fade-in slide-in-from-top-1">
            <AlertCircle className="w-4 h-4" /> {errorMsg}
          </div>
        )}

        <button
          disabled={!url.trim() || importing}
          onClick={handleImport}
          className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white text-xs font-black rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:grayscale active:scale-95 flex items-center justify-center gap-2"
        >
          {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
          {importing ? 'Crawling...' : 'Index URL'}
        </button>
      </div>
    </div>
  );
}
