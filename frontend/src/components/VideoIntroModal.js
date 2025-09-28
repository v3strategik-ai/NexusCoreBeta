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
              // Fallback: show play button or handle gracefully
            });
          }
        }
      }, 100);
    }
  }, [isOpen]);

  const handleVideoEnd = () => {
    setIsPlaying(false);
    setHasEnded(true);
    
    if (autoClose) {
      // Auto-close after a brief pause to let the animation settle
      setTimeout(() => {
        onClose();
      }, 500);
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-black">
      {/* Fullscreen Video Container - No Modal Background */}
      <div className="relative w-full h-full flex items-center justify-center">
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
      // Small delay to let the page load
      const timer = setTimeout(() => {
        setShowIntro(true);
      }, 500);
      
      return () => clearTimeout(timer);
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