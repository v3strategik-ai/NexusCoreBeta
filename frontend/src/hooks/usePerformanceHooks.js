import { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Custom hook for API caching with React
export const useApiCache = (key, fetcher, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const cache = useRef(new Map());
  const { ttl = 300000, enabled = true } = options; // 5 minutes default TTL
  
  const fetchData = useCallback(async () => {
    if (!enabled) return;
    
    const cacheKey = typeof key === 'function' ? key() : key;
    const cached = cache.current.get(cacheKey);
    
    // Check if cached data is still valid
    if (cached && Date.now() - cached.timestamp < ttl) {
      setData(cached.data);
      setLoading(false);
      return cached.data;
    }
    
    try {
      setLoading(true);
      const result = await fetcher();
      
      // Cache the result
      cache.current.set(cacheKey, {
        data: result,
        timestamp: Date.now()
      });
      
      setData(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [key, fetcher, ttl, enabled]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  const invalidateCache = useCallback(() => {
    const cacheKey = typeof key === 'function' ? key() : key;
    cache.current.delete(cacheKey);
    fetchData();
  }, [key, fetchData]);
  
  const clearAllCache = useCallback(() => {
    cache.current.clear();
  }, []);
  
  return { data, loading, error, refetch: fetchData, invalidate: invalidateCache, clearCache: clearAllCache };
};

// Custom hook for debouncing values (performance optimization)
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
};

// Custom hook for throttling function calls
export const useThrottle = (callback, delay) => {
  const lastCall = useRef(0);
  
  return useCallback((...args) => {
    const now = Date.now();
    if (now - lastCall.current >= delay) {
      lastCall.current = now;
      callback(...args);
    }
  }, [callback, delay]);
};

// Custom hook for lazy loading data with intersection observer
export const useLazyLoad = (options = {}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const elementRef = useRef();
  
  const { threshold = 0.1, rootMargin = '0px', triggerOnce = true } = options;
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          if (!hasLoaded) {
            setHasLoaded(true);
          }
          if (triggerOnce) {
            observer.unobserve(entry.target);
          }
        } else if (!triggerOnce) {
          setIsVisible(false);
        }
      },
      { threshold, rootMargin }
    );
    
    if (elementRef.current) {
      observer.observe(elementRef.current);
    }
    
    return () => {
      if (elementRef.current) {
        observer.unobserve(elementRef.current);
      }
    };
  }, [threshold, rootMargin, triggerOnce, hasLoaded]);
  
  return { elementRef, isVisible, hasLoaded };
};

// Custom hook for managing component performance
export const usePerformanceMonitor = (componentName) => {
  const renderStartTime = useRef(Date.now());
  const renderCount = useRef(0);
  
  useEffect(() => {
    renderCount.current += 1;
    const renderTime = Date.now() - renderStartTime.current;
    
    if (renderTime > 100) { // Log slow renders > 100ms
      console.warn(`Slow render detected in ${componentName}: ${renderTime}ms (render #${renderCount.current})`);
    }
    
    renderStartTime.current = Date.now();
  });
  
  const logPerformance = useCallback((operation, startTime) => {
    const duration = Date.now() - startTime;
    console.log(`${componentName} - ${operation}: ${duration}ms`);
  }, [componentName]);
  
  return { renderCount: renderCount.current, logPerformance };
};

// Custom hook for batch API calls
export const useBatchApi = (batchSize = 10, delay = 100) => {
  const [queue, setQueue] = useState([]);
  const [processing, setProcessing] = useState(false);
  const timeoutRef = useRef();
  
  const addToQueue = useCallback((item) => {
    setQueue(prev => [...prev, item]);
  }, []);
  
  const processBatch = useCallback(async (batch) => {
    setProcessing(true);
    try {
      // Process all items in the batch
      const results = await Promise.allSettled(
        batch.map(item => item.promise())
      );
      
      // Resolve/reject each promise based on results
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          batch[index].resolve(result.value);
        } else {
          batch[index].reject(result.reason);
        }
      });
    } catch (error) {
      // Reject all promises in case of batch failure
      batch.forEach(item => item.reject(error));
    } finally {
      setProcessing(false);
    }
  }, []);
  
  useEffect(() => {
    if (queue.length === 0) return;
    
    const processingFunction = () => {
      const batch = queue.slice(0, batchSize);
      setQueue(prev => prev.slice(batchSize));
      
      if (batch.length > 0) {
        processBatch(batch);
      }
    };
    
    if (queue.length >= batchSize) {
      // Process immediately if we have a full batch
      processingFunction();
    } else {
      // Wait for delay before processing partial batch
      timeoutRef.current = setTimeout(processingFunction, delay);
    }
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [queue, batchSize, delay, processBatch]);
  
  const enqueue = useCallback((promiseFunction) => {
    return new Promise((resolve, reject) => {
      addToQueue({
        promise: promiseFunction,
        resolve,
        reject
      });
    });
  }, [addToQueue]);
  
  return { enqueue, queueSize: queue.length, processing };
};

// Custom hook for virtual scrolling
export const useVirtualScroll = (items, itemHeight, containerHeight) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleItems = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 1,
      items.length
    );
    
    return {
      items: items.slice(startIndex, endIndex),
      startIndex,
      endIndex,
      offsetY: startIndex * itemHeight
    };
  }, [items, itemHeight, containerHeight, scrollTop]);
  
  const totalHeight = items.length * itemHeight;
  
  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);
  
  return {
    visibleItems,
    totalHeight,
    handleScroll,
    scrollTop
  };
};

// Custom hook for connection monitoring
export const useConnectionMonitor = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [connectionType, setConnectionType] = useState('unknown');
  
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Check connection type if available
    if ('connection' in navigator) {
      const connection = navigator.connection;
      setConnectionType(connection.effectiveType || 'unknown');
      
      const handleConnectionChange = () => {
        setConnectionType(connection.effectiveType || 'unknown');
      };
      
      connection.addEventListener('change', handleConnectionChange);
      
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        connection.removeEventListener('change', handleConnectionChange);
      };
    }
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);
  
  return { isOnline, connectionType };
};

// Export all hooks
export default {
  useApiCache,
  useDebounce,
  useThrottle,
  useLazyLoad,
  usePerformanceMonitor,
  useBatchApi,
  useVirtualScroll,
  useConnectionMonitor
};