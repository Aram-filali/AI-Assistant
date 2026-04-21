"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '@/lib/store';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Plus, 
  Search, 
  BookOpen, 
  Zap, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  actions?: any[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { token, user } = useAuthStore();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const requestBody = {
        question: input,
        ...(conversationId && { conversation_id: conversationId })
      };

      console.log('Sending chat request:', { url: 'http://localhost:8001/chat/ask', body: requestBody, hasToken: !!token });

      const response = await fetch('http://localhost:8001/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Chat response status:', response.status);
      console.log('Chat response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Chat error response:', errorText);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Chat response data:', data);
      
      // Update local storage/state with conversation history if needed
      setConversationId(data.conversation_id);
      
      const aiMsg: Message = { 
        role: 'assistant', 
        content: data.answer,
        sources: data.sources,
        actions: data.triggered_actions
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Désolé, une erreur est survenue lors de la communication avec l'IA. Vérifiez que le backend est lancé et que l'endpoint /chat/ask est disponible." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Search/Header area */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Agent Workspace</h1>
          <p className="text-xs text-white/40 font-bold uppercase tracking-widest">Active Session: {conversationId || 'New Chat'}</p>
        </div>
        <div className="flex gap-2">
          <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white/70 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all font-bold uppercase tracking-wider">
            <option>All Knowledge</option>
            <option>Sales Sop</option>
          </select>
          <button 
            onClick={() => {
              setMessages([]);
              setConversationId(null);
            }}
            className="p-1.5 rounded-lg bg-white/5 border border-white/10 text-white/40 hover:text-white transition-all"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 glass-card rounded-2xl border border-white/5 overflow-hidden">
        {/* Messages list */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-12 space-y-12 custom-scrollbar"
        >
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-8 animate-in fade-in duration-500">
              <div className="w-24 h-24 rounded-3xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary group-hover:scale-110 transition-transform duration-500 shadow-2xl shadow-primary/20">
                <Bot className="w-12 h-12" />
              </div>
              <div className="space-y-3">
                <h4 className="text-2xl font-black text-white tracking-tight">How can I help you today?</h4>
                <p className="text-sm text-white/40 max-w-sm font-medium">Ask about sales strategies, document summaries, or request the agent to perform an action.</p>
              </div>
              <div className="grid grid-cols-2 gap-4 w-full max-w-md mt-4">
                {[
                  "Summarize latest SOPs",
                  "Draft a followup email",
                  "Analyze lead sentiment",
                  "Update Pipedrive status"
                ].map(suggest => (
                  <button 
                    key={suggest}
                    onClick={() => setInput(suggest)}
                    className="p-4 bg-white/[0.03] border border-white/5 rounded-xl text-left text-xs font-bold text-white/60 hover:text-primary hover:border-primary/40 hover:bg-primary/5 transition-all active:scale-[0.98]"
                  >
                    {suggest}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div 
                key={i} 
                className={`flex gap-6 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-500`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 self-start shadow-xl shadow-primary/10">
                    <Bot className="w-5 h-5" />
                  </div>
                )}
                
                <div className={`flex flex-col gap-4 max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-6 rounded-3xl text-sm leading-relaxed shadow-2xl ${
                    msg.role === 'user' 
                      ? 'bg-primary text-white rounded-tr-none font-medium' 
                      : 'glass-card text-white/90 rounded-tl-none border border-white/5'
                  }`}>
                    {msg.content}
                  </div>

                  {/* Actions & Sources */}
                  {msg.role === 'assistant' && (msg.actions?.length || msg.sources?.length) && (
                    <div className="flex flex-wrap gap-2 mt-2">
                       {msg.actions?.map((act, idx) => (
                         <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-[10px] font-black text-green-500 uppercase tracking-widest animate-in zoom-in-95 duration-500 fill-mode-both" style={{animationDelay: `${idx * 150}ms`}}>
                           <Zap className="w-3 h-3 fill-green-500" />
                           Action: {act.type || 'Tool executed'}
                           <CheckCircle2 className="w-3 h-3" />
                         </div>
                       ))}
                       {msg.sources?.map((src, idx) => (
                         <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black text-blue-500 uppercase tracking-widest animate-in zoom-in-95 duration-500 fill-mode-both" style={{animationDelay: `${idx * 150}ms`}}>
                           <BookOpen className="w-3 h-3" />
                            Source: {src.filename || 'Doc'}
                         </div>
                       ))}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/40 shrink-0 self-start">
                    <User className="w-5 h-5" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex gap-6 justify-start animate-pulse">
              <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary/30 shrink-0 self-start">
                <Bot className="w-5 h-5" />
              </div>
              <div className="glass-card p-4 rounded-3xl rounded-tl-none border border-white/5 flex gap-2 w-20 justify-center">
                 <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                 <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
                 <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" />
              </div>
            </div>
          )}
        </div>

        {/* Improved Input Area */}
        <div className="p-8 bg-white/[0.01] border-t border-white/5">
          <div className="relative group">
            <div className="absolute inset-0 bg-primary/20 blur-2xl opacity-0 group-focus-within:opacity-30 transition-opacity duration-1000 -z-10" />
            
            <div className="flex gap-4 p-2 bg-white/5 border border-white/10 rounded-2xl focus-within:border-primary/50 transition-all shadow-xl">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Message your AI Sales Assistant..."
                className="flex-1 bg-transparent px-6 py-4 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-0 transition-all font-medium"
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="bg-primary hover:bg-primary/90 text-white p-4 rounded-xl transition-all shadow-xl shadow-primary/20 disabled:opacity-50 disabled:grayscale group-hover:scale-105 active:scale-95"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
            
            <p className="mt-3 text-[10px] text-center text-white/20 font-black uppercase tracking-[0.2em]">
              Autonomous Assistant • RAG V2 Enabled • Multi-tool Access
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
