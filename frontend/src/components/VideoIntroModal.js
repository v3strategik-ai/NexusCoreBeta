import React, { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';

const VideoIntroModal = ({ isOpen, onClose, autoClose = false }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasEnded, setHasEnded] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const videoRef = useRef(null);

  useEffect(() => {
    if (isOpen && videoRef.current) {
      // Reset video state when modal opens
      setHasEnded(false);
      setIsPlaying(false);
      
      // Fallback timeout - auto-close after 10 seconds if video doesn't load/end
      const fallbackTimeout = setTimeout(() => {
        console.log("Video intro fallback timeout - auto-closing");
        handleVideoEnd();
      }, 10000);
      
      // Small delay to ensure modal is fully rendered
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
          const playPromise = videoRef.current.play();
          
          if (playPromise !== undefined) {
            playPromise.then(() => {
              setIsPlaying(true);
            }).catch((error) => {
              console.log("Video autoplay failed:", error);
              // Auto-close if video can't play
              setTimeout(() => {
                handleVideoEnd();
              }, 3000);
            });
          }
        }
      }, 100);
      
      // Cleanup timeout if component unmounts or isOpen changes
      return () => clearTimeout(fallbackTimeout);
    }
  }, [isOpen]);

  const handleVideoEnd = () => {
    setIsPlaying(false);
    setHasEnded(true);
    
    if (autoClose) {
      // Start fade out transition
      setIsClosing(true);
      // Auto-close after fade animation
      setTimeout(() => {
        onClose();
      }, 800);
    }
  };

  const handleReplay = () => {
    if (videoRef.current) {
      setHasEnded(false);
      videoRef.current.currentTime = 0;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleClose = () => {
    if (videoRef.current) {
      videoRef.current.pause();
    }
    setIsPlaying(false);
    onClose();
  };

  // Add keyboard escape handler
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      className={`fixed inset-0 z-[100] bg-black transition-opacity duration-800 ${isClosing ? 'opacity-0' : 'opacity-100'}`}
      onClick={handleClose}
    >
      {/* Fullscreen Video Container - No Modal Background */}
      <div className="relative w-full h-full flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          onEnded={handleVideoEnd}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          playsInline
          muted
          preload="auto"
        >
          <source src="/videos/nexus_core_logo_animation.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>

        {/* Subtle close option for manual replays only */}
        {!autoClose && (
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-white/30 hover:text-white/80 transition-colors duration-200 z-20"
          >
            <X className="h-6 w-6" />
          </button>
        )}

        {/* Clean end overlay - minimal for seamless flow */}
        {hasEnded && !autoClose && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <button
              onClick={handleReplay}
              className="text-white/60 hover:text-white transition-all duration-300 text-4xl"
              title="Replay Animation"
            >
              ↻
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Hook for managing intro video state
export const useVideoIntro = () => {
  const [hasSeenIntro, setHasSeenIntro] = useState(() => {
    // Check if user has seen the intro in this session
    return sessionStorage.getItem('nexus-intro-seen') === 'true';
  });
  
  const [showIntro, setShowIntro] = useState(false);

  useEffect(() => {
    // Show intro on first visit to the site in this session
    if (!hasSeenIntro) {
      // Immediate show for seamless experience - no white flash
      setShowIntro(true);
    }
  }, [hasSeenIntro]);

  const handleIntroClose = () => {
    setShowIntro(false);
    setHasSeenIntro(true);
    sessionStorage.setItem('nexus-intro-seen', 'true');
  };

  const replayIntro = () => {
    setShowIntro(true);
  };

  return {
    showIntro,
    replayIntro,
    handleIntroClose
  };
};

export default VideoIntroModal;