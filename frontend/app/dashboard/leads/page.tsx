"use client";

import React, { useState, useEffect } from 'react';
import { 
  Mail, 
  Phone, 
  Building2, 
  Calendar,
  Search,
  RefreshCw,
  AlertCircle,
  User,
  Trash2,
  Eye
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';

interface Lead {
  id: string;
  email: string | null;
  name: string | null;
  phone: string | null;
  company_name: string | null;
  status: 'NEW' | 'ENGAGED' | 'QUALIFIED' | 'CONTACTED' | 'CONVERTED' | 'ABANDONED';
  message_count: number;
  created_at: string;
  updated_at: string;
  contacted_at: string | null;
}

interface LeadsResponse {
  data: Lead[];
  total: number;
  skip: number;
  limit: number;
}

interface Analytics {
  total_leads: number;
  leads_with_email: number;
  conversion_rate: number;
  by_status: Record<string, number>;
}

const statusColors: Record<string, string> = {
  NEW: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  ENGAGED: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  QUALIFIED: 'bg-green-500/20 text-green-400 border-green-500/30',
  CONTACTED: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  CONVERTED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  ABANDONED: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const { token } = useAuthStore();

  const pageSize = 25;

  const fetchLeads = async () => {
    try {
      setLoading(true);
      setError('');

      const params = new URLSearchParams({
        skip: (page * pageSize).toString(),
        limit: pageSize.toString(),
      });

      if (search) params.append('search', search);
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`http://localhost:8001/admin/leads?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch leads (${response.status}): ${errorText}`);
      }

      const data: LeadsResponse = await response.json();
      setLeads(data.data);
      setTotal(data.total);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error loading leads';
      setError(message);
      console.error('Leads error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchLeads();
    }
  }, [token, page, search, statusFilter]);

  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(0);
  };

  const handleStatusFilter = (status: string) => {
    setStatusFilter(status);
    setPage(0);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Leads</h1>
          <p className="text-white/50 text-sm">
            Total: <span className="font-bold text-white">{total} leads</span>
          </p>
        </div>
        <button
          onClick={fetchLeads}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-all disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-bold text-white/70 mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-white/30" />
              <input
                type="text"
                placeholder="Search by email, name, or company..."
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-bold text-white/70 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => handleStatusFilter(e.target.value)}
              className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/70 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
            >
              <option value="">All Statuses</option>
              <option value="NEW">New</option>
              <option value="ENGAGED">Engaged</option>
              <option value="QUALIFIED">Qualified</option>
              <option value="CONTACTED">Contacted</option>
              <option value="CONVERTED">Converted</option>
              <option value="ABANDONED">Abandoned</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          {/* Leads Table */}
          <div className="glass-card rounded-2xl border border-white/5 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.02]">
                    <th className="px-6 py-4 text-left font-bold text-white/70">Name</th>
                    <th className="px-6 py-4 text-left font-bold text-white/70">Email</th>
                    <th className="px-6 py-4 text-left font-bold text-white/70">Phone</th>
                    <th className="px-6 py-4 text-left font-bold text-white/70">Company</th>
                    <th className="px-6 py-4 text-left font-bold text-white/70">Status</th>
                    <th className="px-6 py-4 text-left font-bold text-white/70">Created</th>
                    <th className="px-6 py-4 text-center font-bold text-white/70">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3 opacity-40">
                          <User className="w-8 h-8" />
                          <p className="text-sm text-white/50">No leads found</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    leads.map((lead) => (
                      <tr key={lead.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                        <td className="px-6 py-4">
                          <p className="font-bold text-white">{lead.name || '—'}</p>
                        </td>
                        <td className="px-6 py-4">
                          {lead.email ? (
                            <a
                              href={`mailto:${lead.email}`}
                              className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                            >
                              <Mail className="w-4 h-4" />
                              {lead.email}
                            </a>
                          ) : (
                            <span className="text-white/30">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {lead.phone ? (
                            <a
                              href={`tel:${lead.phone}`}
                              className="flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors"
                            >
                              <Phone className="w-4 h-4" />
                              {lead.phone}
                            </a>
                          ) : (
                            <span className="text-white/30">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {lead.company_name ? (
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-white/30" />
                              <span className="text-white/70">{lead.company_name}</span>
                            </div>
                          ) : (
                            <span className="text-white/30">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${statusColors[lead.status]}`}>
                            {lead.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-white/50 text-xs">
                            {new Date(lead.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: '2-digit'
                            })}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <button
                            onClick={() => setSelectedLead(lead)}
                            className="p-2 hover:bg-white/10 rounded-lg text-white/50 hover:text-white transition-all"
                            title="View details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-white/50">
                Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, total)} of {total} leads
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/70 hover:text-white disabled:opacity-50 transition-all"
                >
                  Previous
                </button>
                <div className="flex items-center gap-2 px-4 py-2">
                  <span className="text-sm text-white/70">
                    Page {page + 1} of {totalPages}
                  </span>
                </div>
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/70 hover:text-white disabled:opacity-50 transition-all"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Lead Details Modal */}
      {selectedLead && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card rounded-2xl border border-white/5 p-8 max-w-xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">{selectedLead.name || 'Unknown'}</h2>
              <button
                onClick={() => setSelectedLead(null)}
                className="text-white/50 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Contact Info */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest">Contact Information</h3>
                
                {selectedLead.email && (
                  <div className="flex items-start gap-3">
                    <Mail className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                      <p className="text-xs text-white/50">Email</p>
                      <a href={`mailto:${selectedLead.email}`} className="text-blue-400 hover:text-blue-300">
                        {selectedLead.email}
                      </a>
                    </div>
                  </div>
                )}

                {selectedLead.phone && (
                  <div className="flex items-start gap-3">
                    <Phone className="w-5 h-5 text-green-400 mt-0.5" />
                    <div>
                      <p className="text-xs text-white/50">Phone</p>
                      <a href={`tel:${selectedLead.phone}`} className="text-green-400 hover:text-green-300">
                        {selectedLead.phone}
                      </a>
                    </div>
                  </div>
                )}

                {selectedLead.company_name && (
                  <div className="flex items-start gap-3">
                    <Building2 className="w-5 h-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="text-xs text-white/50">Company</p>
                      <p className="text-white">{selectedLead.company_name}</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Status & Engagement */}
              <div className="space-y-3 pt-4 border-t border-white/5">
                <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest">Status & Engagement</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-white/50 mb-2">Status</p>
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${statusColors[selectedLead.status]}`}>
                      {selectedLead.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-white/50 mb-2">Messages</p>
                    <p className="text-2xl font-bold text-white">{selectedLead.message_count}</p>
                  </div>
                </div>
              </div>

              {/* Dates */}
              <div className="space-y-3 pt-4 border-t border-white/5">
                <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest">Timeline</h3>
                
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-white/30" />
                  <div>
                    <p className="text-xs text-white/50">Created</p>
                    <p className="text-white text-sm">
                      {new Date(selectedLead.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {selectedLead.contacted_at && (
                  <div className="flex items-center gap-3">
                    <Calendar className="w-5 h-5 text-emerald-400" />
                    <div>
                      <p className="text-xs text-white/50">Contacted</p>
                      <p className="text-white text-sm">
                        {new Date(selectedLead.contacted_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => setSelectedLead(null)}
              className="w-full mt-6 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/70 hover:text-white transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
