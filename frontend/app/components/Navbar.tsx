import React from 'react';
import Link from 'next/link';
import Image from 'next/image';

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5 py-4 px-6 md:px-12 flex items-center justify-between backdrop-blur-3xl">
      <div className="flex items-center gap-2 group cursor-pointer">
        <Image 
          src="/logoai.png" 
          alt="AI Assistant Logo" 
          width={60} 
          height={60}
          className="rounded-xl group-hover:rotate-12 transition-transform duration-500"
        />
      </div>

      <Link href="/login" className="bg-primary hover:bg-primary/90 text-white px-5 py-2 rounded-full text-sm font-bold transition-all shadow-lg shadow-primary/20">
        Login
      </Link>
    </nav>
  );
}
