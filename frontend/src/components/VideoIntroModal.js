import React, { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';

const VideoIntroModal = ({ isOpen, onClose, autoClose = false }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasEnded, setHasEnded] = useState(false);
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/90 backdrop-blur-sm transition-opacity duration-300"
        onClick={handleClose}
      />
      
      {/* Modal Container */}
      <div className="relative z-10 max-w-4xl w-full mx-4">
        {/* Close Button */}
        <button
          onClick={handleClose}
          className="absolute -top-12 right-0 text-white/70 hover:text-white transition-colors duration-200 z-20"
        >
          <X className="h-8 w-8" />
        </button>

        {/* Video Container */}
        <div className="relative bg-black rounded-lg overflow-hidden shadow-2xl">
          <video
            ref={videoRef}
            className="w-full h-auto max-h-[80vh] object-contain"
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

          {/* Video Controls Overlay - Hidden for cleaner experience */}
          {hasEnded && autoClose && (
            <div className="absolute inset-0 bg-black/20">
              {/* Clean end - no visible controls for auto-close mode */}
            </div>
          )}
          
          {hasEnded && !autoClose && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
              <button
                onClick={handleReplay}
                className="bg-blue-600/80 hover:bg-blue-600 text-white px-6 py-2 rounded-full font-medium transition-all duration-200 opacity-0 hover:opacity-100"
                title="Replay Animation"
              >
                ↻
              </button>
            </div>
          )}
        </div>
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