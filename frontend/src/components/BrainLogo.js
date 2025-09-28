import React from 'react';

const BrainLogo = ({ className = "", onClick = null, size = "32" }) => {
  const isClickable = !!onClick;
  
  return (
    <div 
      className={`inline-flex items-center justify-center ${isClickable ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      <svg 
        width={size} 
        height={size} 
        viewBox="0 0 100 100" 
        className={`${isClickable ? 'quantum-pulse hover:scale-110 transition-transform duration-200' : 'quantum-pulse'}`}
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Gradient for the brain */}
          <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="1" />
            <stop offset="50%" stopColor="#1d4ed8" stopOpacity="1" />
            <stop offset="100%" stopColor="#1e40af" stopOpacity="1" />
          </linearGradient>
          
          {/* Glow effect */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          
          {/* Animated pulse filter */}
          <filter id="pulse">
            <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {/* Main brain structure */}
        <path 
          d="M25 45 C25 30, 35 20, 50 20 C65 20, 75 30, 75 45 C75 35, 65 30, 55 35 C60 25, 70 25, 75 35 C80 40, 80 50, 75 55 C75 65, 65 75, 50 75 C35 75, 25 65, 25 55 C20 50, 20 40, 25 45 Z" 
          fill="url(#brainGradient)" 
          stroke="#60a5fa" 
          strokeWidth="1.5"
          filter="url(#glow)"
        />
        
        {/* Left brain hemisphere detail */}
        <path 
          d="M30 40 C35 35, 40 40, 45 38 C50 36, 48 45, 45 50 C40 55, 35 50, 30 52"
          fill="none" 
          stroke="#93c5fd" 
          strokeWidth="1"
          opacity="0.8"
        />
        
        {/* Right brain hemisphere detail */}
        <path 
          d="M55 38 C60 40, 65 35, 70 40 C70 45, 65 50, 60 52 C55 50, 52 45, 55 38"
          fill="none" 
          stroke="#93c5fd" 
          strokeWidth="1"
          opacity="0.8"
        />
        
        {/* Central connection */}
        <line 
          x1="50" y1="35" 
          x2="50" y2="65" 
          stroke="#60a5fa" 
          strokeWidth="1"
          opacity="0.6"
        />
        
        {/* Neural connections - animated */}
        <g className="animate-pulse">
          <circle cx="35" cy="45" r="1.5" fill="#3b82f6" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite" />
          </circle>
          <circle cx="50" cy="40" r="1.5" fill="#1d4ed8" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="65" cy="45" r="1.5" fill="#3b82f6" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle cx="40" cy="55" r="1.5" fill="#1e40af" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2.2s" repeatCount="indefinite" />
          </circle>
          <circle cx="60" cy="55" r="1.5" fill="#3b82f6" opacity="0.8">
            <animate attributeName="opacity" values="0.4;1;0.4" dur="2.8s" repeatCount="indefinite" />
          </circle>
        </g>
        
        {/* Connection lines between neurons */}
        <g opacity="0.3" className="animate-pulse">
          <line x1="35" y1="45" x2="50" y2="40" stroke="#60a5fa" strokeWidth="0.5" />
          <line x1="50" y1="40" x2="65" y2="45" stroke="#60a5fa" strokeWidth="0.5" />
          <line x1="35" y1="45" x2="40" y2="55" stroke="#60a5fa" strokeWidth="0.5" />
          <line x1="65" y1="45" x2="60" y2="55" stroke="#60a5fa" strokeWidth="0.5" />
          <line x1="40" y1="55" x2="60" y2="55" stroke="#60a5fa" strokeWidth="0.5" />
        </g>
        
        {isClickable && (
          <text 
            x="50" 
            y="90" 
            textAnchor="middle" 
            className="text-xs fill-current text-blue-400 opacity-0 hover:opacity-100 transition-opacity duration-200"
            style={{ fontSize: '8px', fontFamily: 'system-ui' }}
          >
            Click to replay
          </text>
        )}
      </svg>
    </div>
  );
};

export default BrainLogo;