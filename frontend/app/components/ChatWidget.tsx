"use client";

/**
 * Chat Widget Component
 * 
 * Interactive chat interface with:
 * - Real-time message streaming
 * - Lead capture form (name & company)
 * - Loading states and error handling
 * - Auto-scroll to latest messages
 * 
 * Used in: Dashboard and public chat pages
 */

import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface LeadInfo {
  lead_id: string;
  name_requested: boolean;
  email_detected: boolean;
  phone_detected: boolean;
}

export default function ChatWidget() {
  // ==================== STATE MANAGEMENT ====================
  const [messages, setMessages] = useState<Message[]>([]);     // Chat history
  const [input, setInput] = useState('');                      // User message input
  const [nameInput, setNameInput] = useState('');              // Lead name capture
  const [companyInput, setCompanyInput] = useState('');        // Lead company capture
  const [loading, setLoading] = useState(false);               // Request in progress
  const [leadInfo, setLeadInfo] = useState<LeadInfo | null>(null);  // Lead metadata from backend
  const scrollRef = useRef<HTMLDivElement>(null);              // Auto-scroll reference

  // ==================== AUTO-SCROLL TO LATEST MESSAGE ====================
  useEffect(() => {
    // Scroll chat to bottom when new messages arrive (smooth UX)
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // ==================== SEND MESSAGE HANDLER ====================
  const handleSend = async () => {
    // Prevent sending empty or duplicate messages while loading
    if (!input.trim() || loading) return;

    // 1. Add user message to chat immediately (optimistic update)
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');  // Clear input field
    setLoading(true);

    try {
      // 2. Send message to backend API
      const response = await fetch('http://localhost:8000/chat/ask-public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input,
        }),
      });

      const data = await response.json();
      
      // 3. Add AI response to chat
      const aiMsg: Message = { role: 'assistant', content: data.answer };
      setMessages(prev => [...prev, aiMsg]);
      
      // 4. Store lead info if backend detected potential lead
      // Used for name/company capture form
      if (data.lead_info) {
        setLeadInfo(data.lead_info);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      // 5. Show error message to user
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Désolé, une erreur est survenue lors de la communication avec l'IA." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ==================== LEAD CAPTURE HANDLER ====================
  const handleNameSubmit = async () => {
    // Validate inputs before sending
    if (!nameInput.trim() || !leadInfo?.lead_id) return;

    setLoading(true);
    try {
      // Send lead information to backend for CRM integration
      const response = await fetch(`http://localhost:8000/admin/leads/${leadInfo.lead_id}/name`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: nameInput,
          company_name: companyInput,
        }),
      });

      if (response.ok) {
        // Clear form after successful submission
        setNameInput('');
        setCompanyInput('');
        setLeadInfo(prev => prev ? { ...prev, name_requested: false } : null);
        
        // Add confirmation message tailored to what user provided
        const cleanName = nameInput.trim();
        const cleanCompany = companyInput.trim();
        const confirmMsg: Message = { 
          role: 'assistant', 
          content: cleanCompany
            ? `Merci ${cleanName}, c'est noté. J'ai aussi bien enregistré votre entreprise (${cleanCompany}). Souhaitez-vous recevoir un devis ou planifier une démo de 15 minutes ?`
            : `Merci ${cleanName}, c'est noté. Si vous voulez, vous pouvez aussi partager le nom de votre entreprise. Souhaitez-vous recevoir un devis ou planifier une démo de 15 minutes ?`
        };
        setMessages(prev => [...prev, confirmMsg]);
      } else {
        console.error('Error saving name:', response.status);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto glass-card rounded-2xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="p-6 border-b border-white/10 bg-white/5 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="font-bold text-lg text-white">AI Sales Assistant</h3>
            <p className="text-xs text-white/50">Online & Ready to Help</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-40">
            <div className="text-4xl">👋</div>
            <p className="text-sm max-w-xs">
              Posez une question sur nos produits ou demandez un devis pour démarrer.
            </p>
          </div>
        )}
        
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
          >
            <div className={`max-w-[85%] p-4 rounded-2xl ${
              msg.role === 'user' 
                ? 'bg-primary text-white rounded-tr-none shadow-lg' 
                : 'glass text-white/90 rounded-tl-none border border-white/10'
            }`}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start animate-pulse">
            <div className="glass p-4 rounded-2xl rounded-tl-none flex gap-1">
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-6 bg-white/5 border-t border-white/10 space-y-3">
        {/* Name capture form */}
        {leadInfo?.name_requested && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNameSubmit()}
                placeholder="Entrez votre nom..."
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all text-white placeholder:text-white/30"
                disabled={loading}
              />
              <input
                type="text"
                value={companyInput}
                onChange={(e) => setCompanyInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNameSubmit()}
                placeholder="Nom de l'entreprise (optionnel)..."
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all text-white placeholder:text-white/30"
                disabled={loading}
              />
            </div>
            <button
              onClick={handleNameSubmit}
              disabled={loading || !nameInput.trim()}
              className="w-full bg-green-600 hover:bg-green-700 text-white p-3 rounded-xl transition-all shadow-lg shadow-green-600/20 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        )}

        {/* Message input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-white placeholder:text-white/30"
            disabled={loading || (leadInfo?.name_requested ? true : false)}
          />
          <button
            onClick={handleSend}
            disabled={loading || (leadInfo?.name_requested ? true : false)}
            className="bg-primary hover:bg-primary/90 text-white p-3 rounded-xl transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
