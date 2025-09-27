import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AlertCircle, Zap, Database, Activity, RefreshCcw, TrendingUp, Settings, CheckCircle, XCircle, Clock } from 'lucide-react';

const PerformanceDashboard = () => {
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);

  // Backend URL from environment variables
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Memoized API call function
  const fetchPerformanceData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/performance/metrics`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPerformanceData(data);
      setError(null);
    } catch (error) {
      console.error('Error fetching performance data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  // Memoized refresh handler
  const handleRefresh = useCallback(() => {
    fetchPerformanceData();
  }, [fetchPerformanceData]);

  // Auto-refresh effect
  useEffect(() => {
    fetchPerformanceData();
  }, [fetchPerformanceData]);

  useEffect(() => {
    let interval;
    if (autoRefresh && refreshInterval > 0) {
      interval = setInterval(() => {
        fetchPerformanceData();
      }, refreshInterval * 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval, fetchPerformanceData]);

  // Memoized performance metrics calculation
  const performanceMetrics = useMemo(() => {
    if (!performanceData?.performance_metrics?.performance_summary) {
      return null;
    }

    const summary = performanceData.performance_metrics.performance_summary;
    const cachePerf = performanceData.performance_metrics.cache_performance || {};
    const systemRes = performanceData.performance_metrics.system_resources || {};

    return {
      responseTime: {
        value: summary.average_response_time || 0,
        status: (summary.average_response_time || 0) < 1 ? 'good' : (summary.average_response_time || 0) < 2 ? 'warning' : 'critical',
        unit: 'seconds'
      },
      slowRequests: {
        value: summary.slow_requests_percentage || 0,
        status: (summary.slow_requests_percentage || 0) < 5 ? 'good' : (summary.slow_requests_percentage || 0) < 15 ? 'warning' : 'critical',
        unit: '%'
      },
      cacheHitRate: {
        value: cachePerf.cache_hit_rate_percentage || 0,
        status: (cachePerf.cache_hit_rate_percentage || 0) > 70 ? 'good' : (cachePerf.cache_hit_rate_percentage || 0) > 50 ? 'warning' : 'critical',
        unit: '%'
      },
      memoryUsage: {
        value: systemRes.memory_usage_mb || 0,
        status: (systemRes.memory_usage_mb || 0) < 512 ? 'good' : (systemRes.memory_usage_mb || 0) < 1024 ? 'warning' : 'critical',
        unit: 'MB'
      }
    };
  }, [performanceData]);

  // Memoized cache statistics
  const cacheStats = useMemo(() => {
    if (!performanceData?.cache_statistics?.cache_stats) {
      return null;
    }
    return performanceData.cache_statistics.cache_stats;
  }, [performanceData]);

  // Memoized rate limit statistics
  const rateLimitStats = useMemo(() => {
    if (!performanceData?.rate_limit_statistics?.global_stats) {
      return null;
    }
    return performanceData.rate_limit_statistics.global_stats;
  }, [performanceData]);

  // Performance optimization trigger
  const runOptimization = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/performance/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          include_database: true,
          include_cache: true,
          include_memory: true,
          run_analysis: true
        })
      });
      
      if (!response.ok) {
        throw new Error(`Optimization failed: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Optimization result:', result);
      
      // Refresh data after optimization
      setTimeout(fetchPerformanceData, 2000);
    } catch (error) {
      console.error('Error running optimization:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'good': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'critical': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'text-green-600 bg-green-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading && !performanceData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCcw className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-600">Loading performance data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <XCircle className="h-5 w-5 text-red-500 mr-2" />
            <h3 className="text-red-800 font-medium">Performance Dashboard Error</h3>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-3 bg-red-100 hover:bg-red-200 text-red-800 px-4 py-2 rounded-md text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Performance Dashboard</h1>
            <p className="text-gray-600 mt-1">Monitor and optimize platform performance</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="autoRefresh" className="text-sm text-gray-700">Auto-refresh</label>
              {autoRefresh && (
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={10}>10s</option>
                  <option value={30}>30s</option>
                  <option value={60}>1m</option>
                  <option value={300}>5m</option>
                </select>
              )}
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            
            <button
              onClick={runOptimization}
              disabled={loading}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <Zap className="h-4 w-4" />
              <span>Optimize</span>
            </button>
          </div>
        </div>
      </div>

      {/* Performance Metrics Grid */}
      {performanceMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className={`p-6 rounded-lg border ${getStatusColor(performanceMetrics.responseTime.status)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Avg Response Time</p>
                <p className="text-2xl font-bold">{performanceMetrics.responseTime.value.toFixed(3)}{performanceMetrics.responseTime.unit}</p>
              </div>
              {getStatusIcon(performanceMetrics.responseTime.status)}
            </div>
          </div>

          <div className={`p-6 rounded-lg border ${getStatusColor(performanceMetrics.slowRequests.status)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Slow Requests</p>
                <p className="text-2xl font-bold">{performanceMetrics.slowRequests.value.toFixed(1)}{performanceMetrics.slowRequests.unit}</p>
              </div>
              {getStatusIcon(performanceMetrics.slowRequests.status)}
            </div>
          </div>

          <div className={`p-6 rounded-lg border ${getStatusColor(performanceMetrics.cacheHitRate.status)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Cache Hit Rate</p>
                <p className="text-2xl font-bold">{performanceMetrics.cacheHitRate.value.toFixed(1)}{performanceMetrics.cacheHitRate.unit}</p>
              </div>
              {getStatusIcon(performanceMetrics.cacheHitRate.status)}
            </div>
          </div>

          <div className={`p-6 rounded-lg border ${getStatusColor(performanceMetrics.memoryUsage.status)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">Memory Usage</p>
                <p className="text-2xl font-bold">{performanceMetrics.memoryUsage.value.toFixed(0)}{performanceMetrics.memoryUsage.unit}</p>
              </div>
              {getStatusIcon(performanceMetrics.memoryUsage.status)}
            </div>
          </div>
        </div>
      )}

      {/* Detailed Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cache Statistics */}
        {cacheStats && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Database className="h-5 w-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold">Cache Performance</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Hit Rate:</span>
                <span className="font-medium">{cacheStats.hit_rate_percent}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Hits:</span>
                <span className="font-medium">{cacheStats.hits.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Misses:</span>
                <span className="font-medium">{cacheStats.misses.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cache Size:</span>
                <span className="font-medium">{(cacheStats.estimated_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Sets:</span>
                <span className="font-medium">{cacheStats.sets.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Errors:</span>
                <span className="font-medium text-red-600">{cacheStats.errors.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* Rate Limiting Statistics */}
        {rateLimitStats && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center mb-4">
              <Activity className="h-5 w-5 text-green-500 mr-2" />
              <h3 className="text-lg font-semibold">Rate Limiting</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Storage Backend:</span>
                <span className="font-medium capitalize">{rateLimitStats.storage_backend || 'Memory'}</span>
              </div>
              
              {rateLimitStats.tier_configurations && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Rate Limits by Tier:</p>
                  <div className="space-y-2 text-sm">
                    {Object.entries(rateLimitStats.tier_configurations).map(([tier, config]) => (
                      <div key={tier} className="flex justify-between">
                        <span className="text-gray-600 capitalize">{tier}:</span>
                        <span className="font-medium">{config.requests_per_minute}/min</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {rateLimitStats.endpoint_costs && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">High-Cost Endpoints:</p>
                  <div className="space-y-1 text-sm">
                    {Object.entries(rateLimitStats.endpoint_costs)
                      .filter(([, cost]) => cost > 1)
                      .slice(0, 3)
                      .map(([endpoint, cost]) => (
                        <div key={endpoint} className="flex justify-between">
                          <span className="text-gray-600 truncate">{endpoint.replace('/api/', '')}</span>
                          <span className="font-medium">{cost}x</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {performanceData?.performance_metrics?.optimization_recommendations && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="h-5 w-5 text-blue-500 mr-2" />
            <h3 className="text-lg font-semibold text-blue-900">Optimization Recommendations</h3>
          </div>
          
          <div className="space-y-2">
            {performanceData.performance_metrics.optimization_recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <p className="text-blue-800">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(PerformanceDashboard);