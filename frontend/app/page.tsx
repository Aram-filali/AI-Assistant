import React from 'react';
import Navbar from './components/Navbar';
import ChatWidget from './components/ChatWidget';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden" style={{ backgroundColor: 'hsl(240 10% 3.9%)' }}>
      {/* Background gradient blobs */}
      <div style={{ position: 'fixed', top: '-10%', left: '-10%', width: '40%', height: '40%', borderRadius: '50%', background: 'rgba(99,102,241,0.15)', filter: 'blur(120px)', zIndex: 0 }} />
      <div style={{ position: 'fixed', bottom: '-10%', right: '-10%', width: '40%', height: '40%', borderRadius: '50%', background: 'rgba(79,70,229,0.1)', filter: 'blur(120px)', zIndex: 0 }} />

      <Navbar />

      <div style={{ position: 'relative', zIndex: 1, paddingTop: '96px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', alignItems: 'center', padding: '120px 64px 64px', maxWidth: '1400px', margin: '0 auto' }}>
        {/* LEFT: Hero copy */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>


          <h1 style={{ fontSize: '72px', fontWeight: 900, lineHeight: '0.95', letterSpacing: '-0.03em', color: 'white', margin: 0 }}>
            AI THAT{' '}
            <span style={{ color: 'hsl(250 84% 60%)', fontStyle: 'italic' }}>GETS STUFF</span>{' '}
            DONE.
          </h1>

          <p style={{ fontSize: '18px', color: 'rgba(255,255,255,0.5)', lineHeight: '1.7', maxWidth: '480px', margin: 0 }}>
            An automated sales assistant that doesn&apos;t just talk — it <strong style={{ color: 'rgba(255,255,255,0.8)' }}>acts</strong>.
            Emails, CRM updates, ticket creation, and lead scoring — all on autopilot.
          </p>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <Link href="/register" style={{ background: 'hsl(250 84% 60%)', color: 'white', border: 'none', padding: '16px 32px', borderRadius: '16px', fontSize: '16px', fontWeight: 700, cursor: 'pointer', boxShadow: '0 20px 40px -10px rgba(99,102,241,0.4)', textDecoration: 'none' }}>
              Get Started Free
            </Link>
            <button style={{ background: 'rgba(255,255,255,0.04)', color: 'white', border: '1px solid rgba(255,255,255,0.12)', padding: '16px 32px', borderRadius: '16px', fontSize: '16px', fontWeight: 700, cursor: 'pointer', backdropFilter: 'blur(8px)' }}>
              Watch Demo
            </button>
          </div>

        </div>

        {/* RIGHT: Chat demo */}
        <div style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', inset: '-4px', borderRadius: '24px', background: 'linear-gradient(135deg,rgba(99,102,241,0.3),transparent)', filter: 'blur(16px)', zIndex: 0 }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <ChatWidget />
          </div>
        </div>
      </div>
    </main>
  );
}
