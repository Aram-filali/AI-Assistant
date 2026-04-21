"use client";

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  MessageSquare,
  Users,
  Target,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';

interface Analytics {
  total_leads: number;
  leads_with_email: number;
  leads_with_phone?: number;
  conversion_rate: number;
  funnel?: {
    engaged: number;
    qualified: number;
    contacted: number;
    converted: number;
  };
  by_status: Record<string, number>;
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token } = useAuthStore();

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('http://localhost:8001/admin/analytics/leads', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('Analytics response status:', response.status);
      console.log('Analytics response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Analytics error response:', errorText);
        throw new Error(`Failed to fetch analytics (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      console.log('Analytics data:', data);
      setAnalytics(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error loading analytics';
      setError(message);
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchAnalytics();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const stats = [
    { 
      label: 'Total Leads', 
      value: analytics?.total_leads?.toString() || '0', 
      icon: Users, 
      color: 'text-blue-400' 
    },
    { 
      label: 'With Email', 
      value: analytics?.leads_with_email?.toString() || '0', 
      icon: MessageSquare, 
      color: 'text-green-400' 
    },
    {
      label: 'With Phone',
      value: analytics?.leads_with_phone?.toString() || '0',
      icon: MessageSquare,
      color: 'text-cyan-400'
    },
    { 
      label: 'Conversion Rate', 
      value: `${(analytics?.conversion_rate || 0).toFixed(1)}%`, 
      icon: Target, 
      color: 'text-orange-400' 
    },
  ];

  const statusEntries = Object.entries(analytics?.by_status || {});
  const maxStatus = Math.max(...statusEntries.map(([, count]) => count), 1);

  const funnel = analytics?.funnel || {
    engaged: 0,
    qualified: 0,
    contacted: 0,
    converted: 0,
  };

  const funnelSteps = [
    { key: 'Engaged', value: funnel.engaged },
    { key: 'Qualified', value: funnel.qualified },
    { key: 'Contacted', value: funnel.contacted },
    { key: 'Converted', value: funnel.converted },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Dashboard</h1>
          <p className="text-white/50 text-sm">Real-time lead analytics</p>
        </div>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-all disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="glass-card p-6 rounded-2xl border border-white/5 relative overflow-hidden group">
            <div className="flex items-start justify-between">
              <div className={`p-2.5 rounded-xl bg-white/5 border border-white/10 ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </div>
            </div>
            
            <div className="mt-4 space-y-1">
              <h3 className="text-2xl font-black text-white">{stat.value}</h3>
              <p className="text-xs text-white/40 font-medium uppercase tracking-widest">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="glass-card p-8 rounded-2xl border border-white/5">
          <h2 className="text-xl font-bold text-white mb-6">Status Distribution</h2>
          <div className="space-y-4">
            {statusEntries.map(([status, count]) => {
              const percent = Math.round((count / maxStatus) * 100);
              return (
                <div key={status} className="space-y-2">
                  <div className="flex justify-between text-xs text-white/60 uppercase tracking-wider">
                    <span>{status}</span>
                    <span>{count}</span>
                  </div>
                  <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-card p-8 rounded-2xl border border-white/5">
          <h2 className="text-xl font-bold text-white mb-6">Conversion Funnel</h2>
          <div className="space-y-4">
            {funnelSteps.map((step, idx) => {
              const base = step.value || 0;
              const prev = idx === 0 ? (analytics?.total_leads || 0) : (funnelSteps[idx - 1].value || 0);
              const rate = prev > 0 ? (base / prev) * 100 : 0;
              return (
                <div key={step.key} className="p-4 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-white/50 uppercase tracking-widest">{step.key}</p>
                    <p className="text-xs text-white/60">{rate.toFixed(1)}%</p>
                  </div>
                  <p className="text-2xl font-bold text-white mt-2">{base}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
