import React from 'react';

interface FeatureCardProps {
  title: string;
  description: string;
  icon: string;
  color?: string;
  className?: string;
}

export default function FeatureCard({ title, description, icon, color = 'primary', className = '' }: FeatureCardProps) {
  return (
    <div className={`glass-card p-8 rounded-3xl group relative overflow-hidden ${className}`}>
      {/* Decorative Glow */}
      <div className={`absolute -top-12 -right-12 w-32 h-32 bg-${color}/10 blur-[60px] group-hover:bg-${color}/20 transition-all duration-500`} />
      
      <div className="relative z-10 space-y-6">
        <div className={`w-14 h-14 bg-${color}/10 rounded-2xl flex items-center justify-center border border-${color}/20 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-500`}>
          <span className="text-3xl">{icon}</span>
        </div>
        
        <div className="space-y-3">
          <h3 className="font-bold text-xl text-white group-hover:text-primary transition-colors">{title}</h3>
          <p className="text-sm text-white/50 leading-relaxed max-w-[280px]">
            {description}
          </p>
        </div>
        
        <div className="pt-4 flex items-center gap-2 text-xs font-semibold text-white/30 group-hover:text-white/60 transition-colors">
          <span>LEARN MORE</span>
          <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>
      </div>
    </div>
  );
}
