"use client";

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import Link from 'next/link';
import { 
  BarChart3, 
  MessageSquare, 
  BookOpen, 
  Settings, 
  LogOut,
  ChevronRight,
  TrendingUp,
  Zap,
  Activity,
  Users
} from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, hasHydrated, logout, user } = useAuthStore();
  const router = useRouter();
  const isAdmin = String(user?.role ?? '').toLowerCase() === 'admin';

  useEffect(() => {
    if (!hasHydrated) return;

    // Client-side guard: must be authenticated AND admin
    if (!isAuthenticated) {
      router.push('/login');
    } else if (!isAdmin) {
      router.push('/');  // Redirect non-admins to home
    }
  }, [hasHydrated, isAuthenticated, isAdmin, router]);

  if (!hasHydrated) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-white/[0.02] flex flex-col">
        <div className="p-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
              <Zap className="w-5 h-5 text-white fill-white" />
            </div>
            <span className="font-bold text-lg text-white tracking-tight">AI Assistant</span>
          </Link>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          {[
            { name: 'Analytics', icon: BarChart3, href: '/dashboard' },
            { name: 'Leads', icon: Users, href: '/dashboard/leads' },
            { name: 'Agent Chat', icon: MessageSquare, href: '/dashboard/chat' },
            { name: 'Knowledge', icon: BookOpen, href: '/dashboard/knowledge' },
            { name: 'Activity Logs', icon: Activity, href: '/dashboard/logs' },
          ].map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white hover:bg-white/5 transition-all"
            >
              <item.icon className="w-4 h-4" />
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5 mt-auto">
          <div className="flex items-center gap-3 px-3 py-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-bold">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-white/40 truncate">{user?.company_name}</p>
            </div>
          </div>
          
          <button
            onClick={() => {
              logout();
              router.push('/');
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-400/70 hover:text-red-400 hover:bg-red-400/10 transition-all"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 border-b border-white/5 px-8 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-white/40">Pages</span>
            <ChevronRight className="w-3 h-3 text-white/20" />
            <span className="text-white">Dashboard</span>
          </div>

          <div className="flex items-center gap-4">
            <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-xs font-bold text-white/70 hover:text-white transition-all">
              Update Knowledge
            </button>
            <div className="w-8 h-8 rounded-full bg-primary animate-pulse" />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {children}
        </div>
      </main>
    </div>
  );
}
