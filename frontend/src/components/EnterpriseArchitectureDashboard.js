import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { TrendingUp, BarChart3, Shield, Target, Users, Activity, AlertTriangle, CheckCircle, XCircle, Lock, Eye, Zap } from 'lucide-react';

const EnterpriseArchitectureDashboard = () => {
  const [activeTab, setActiveTab] = useState('forecasting');
  const [forecastingData, setForecastingData] = useState(null);
  const [securityData, setSecurityData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Backend URL from environment variables
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Fetch data for all systems
  const fetchEnterpriseData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch forecasting health and insights
      const forecastingHealthResponse = await fetch(`${backendUrl}/api/forecasting/health`);
      const forecastingHealth = await forecastingHealthResponse.json();
      
      // Fetch security overview
      const securityHealthResponse = await fetch(`${backendUrl}/api/advanced-security/health`);
      const securityHealth = await securityHealthResponse.json();
      
      // Fetch analytics health
      const analyticsHealthResponse = await fetch(`${backendUrl}/api/comparative-analytics/health`);
      const analyticsHealth = await analyticsHealthResponse.json();
      
      setForecastingData(forecastingHealth);
      setSecurityData(securityHealth);
      setAnalyticsData(analyticsHealth);
      setError(null);
      
    } catch (error) {
      console.error('Error fetching enterprise data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    fetchEnterpriseData();
  }, [fetchEnterpriseData]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50';
      case 'degraded': return 'text-yellow-600 bg-yellow-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <Activity className="h-5 w-5 text-muted-foreground" />;
    }
  };

  // Advanced Forecasting Component
  const ForecastingDashboard = () => {
    const [forecastType, setForecastType] = useState('revenue');
    const [forecastResults, setForecastResults] = useState(null);
    const [forecastLoading, setForecastLoading] = useState(false);

    const generateForecast = async () => {
      try {
        setForecastLoading(true);
        const response = await fetch(`${backendUrl}/api/forecasting/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            forecast_type: forecastType,
            period: 'monthly',
            horizon_months: 6,
            include_confidence: true,
            include_factors: true
          })
        });
        
        if (response.ok) {
          const results = await response.json();
          setForecastResults(results);
        }
      } catch (error) {
        console.error('Error generating forecast:', error);
      } finally {
        setForecastLoading(false);
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <TrendingUp className="h-5 w-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-semibold text-foreground">AI-Powered Business Forecasting</h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm ${getStatusColor(forecastingData?.status || 'unknown')}`}>
              {forecastingData?.status || 'Unknown'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">Supported Forecasts</h4>
              <p className="text-sm text-blue-700 mt-1">
                {forecastingData?.supported_forecasts?.length || 0} forecast types available
              </p>
              <div className="mt-2 text-xs text-blue-600">
                {forecastingData?.supported_forecasts?.slice(0, 3).join(', ')}
              </div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-900">AI Analytics</h4>
              <p className="text-sm text-green-700 mt-1">
                {forecastingData?.components?.ai_engine === 'healthy' ? 'Operational' : 'Unavailable'}
              </p>
              <div className="mt-2 text-xs text-green-600">
                GPT-4o powered predictions
              </div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-900">Forecast Periods</h4>
              <p className="text-sm text-purple-700 mt-1">
                {forecastingData?.supported_periods?.length || 0} time periods
              </p>
              <div className="mt-2 text-xs text-purple-600">
                Weekly to yearly forecasts
              </div>
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center space-x-4 mb-4">
              <select
                value={forecastType}
                onChange={(e) => setForecastType(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="revenue">Revenue Forecasting</option>
                <option value="lead_conversion">Lead Conversion</option>
                <option value="agent_performance">Agent Performance</option>
                <option value="seasonal_analysis">Seasonal Analysis</option>
                <option value="resource_planning">Resource Planning</option>
                <option value="market_trends">Market Trends</option>
              </select>
              
              <button
                onClick={generateForecast}
                disabled={forecastLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md disabled:opacity-50 flex items-center"
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                {forecastLoading ? 'Generating...' : 'Generate Forecast'}
              </button>
            </div>

            {forecastResults && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium mb-2">Forecast Results</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Confidence Score</p>
                    <p className="text-lg font-semibold text-green-600">
                      {(forecastResults.confidence_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Forecast Period</p>
                    <p className="text-lg font-semibold text-foreground">{forecastResults.period}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-muted-foreground mb-2">Key Recommendations:</p>
                  <ul className="text-sm space-y-1">
                    {forecastResults.recommendations?.slice(0, 3).map((rec, idx) => (
                      <li key={idx} className="flex items-start">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Advanced Security Component
  const SecurityDashboard = () => {
    const [mfaSetup, setMfaSetup] = useState(false);
    const [securityOverview, setSecurityOverview] = useState(null);

    const setupMFA = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/advanced-security/mfa/setup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 'demo_user',
            method: 'mfa_totp'
          })
        });
        
        if (response.ok) {
          const mfaData = await response.json();
          setMfaSetup(mfaData);
        }
      } catch (error) {
        console.error('Error setting up MFA:', error);
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-red-500 mr-2" />
              <h3 className="text-lg font-semibold text-foreground">Advanced Security Management</h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm ${getStatusColor(securityData?.status || 'unknown')}`}>
              {securityData?.status || 'Unknown'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-red-50 rounded-lg">
              <div className="flex items-center">
                <Lock className="h-5 w-5 text-red-500 mr-2" />
                <h4 className="font-medium text-red-900">MFA Service</h4>
              </div>
              <p className="text-sm text-red-700 mt-1">
                {securityData?.components?.mfa_service === 'healthy' ? 'Active' : 'Inactive'}
              </p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-center">
                <Eye className="h-5 w-5 text-yellow-500 mr-2" />
                <h4 className="font-medium text-yellow-900">Threat Detection</h4>
              </div>
              <p className="text-sm text-yellow-700 mt-1">
                {securityData?.components?.threat_detection === 'healthy' ? 'Monitoring' : 'Offline'}
              </p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <Users className="h-5 w-5 text-blue-500 mr-2" />
                <h4 className="font-medium text-blue-900">Password Policies</h4>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                {securityData?.components?.password_policies === 'healthy' ? 'Configured' : 'Not Set'}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                <h4 className="font-medium text-green-900">JWT Service</h4>
              </div>
              <p className="text-sm text-green-700 mt-1">
                {securityData?.components?.jwt_service === 'healthy' ? 'Active' : 'Inactive'}
              </p>
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex flex-wrap gap-4 mb-4">
              <button
                onClick={setupMFA}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md flex items-center"
              >
                <Shield className="h-4 w-4 mr-2" />
                Setup MFA Demo
              </button>
              
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center">
                <Lock className="h-4 w-4 mr-2" />
                Configure Policies
              </button>
              
              <button className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md flex items-center">
                <Eye className="h-4 w-4 mr-2" />
                Security Audit
              </button>
            </div>

            {mfaSetup && (
              <div className="bg-red-50 rounded-lg p-4">
                <h4 className="font-medium text-red-900 mb-2">MFA Setup Complete</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-red-600">User ID</p>
                    <p className="font-mono text-sm">{mfaSetup.user_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-red-600">Method</p>
                    <p className="font-semibold">{mfaSetup.method}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-red-600 mb-2">Backup Codes Generated:</p>
                  <p className="text-xs text-red-700">
                    {mfaSetup.backup_codes?.length || 0} codes available for account recovery
                  </p>
                </div>
              </div>
            )}

            {securityData?.supported_auth_methods && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Supported Authentication Methods</h4>
                <div className="flex flex-wrap gap-2">
                  {securityData.supported_auth_methods.map((method, idx) => (
                    <span key={idx} className="px-2 py-1 bg-muted text-foreground rounded-full text-sm">
                      {method.replace('_', ' ').toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Comparative Analytics Component
  const AnalyticsDashboard = () => {
    const [benchmarkResults, setBenchmarkResults] = useState(null);
    const [benchmarkLoading, setBenchmarkLoading] = useState(false);
    const [selectedIndustry, setSelectedIndustry] = useState('general');

    const generateBenchmark = async () => {
      try {
        setBenchmarkLoading(true);
        const response = await fetch(`${backendUrl}/api/comparative-analytics/benchmark`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tenant_id: 'demo_tenant',
            benchmark_types: ['performance', 'revenue'],
            industry: selectedIndustry,
            period: 'quarterly',
            include_anonymized_comparison: true,
            include_recommendations: true
          })
        });
        
        if (response.ok) {
          const results = await response.json();
          setBenchmarkResults(results);
        }
      } catch (error) {
        console.error('Error generating benchmark:', error);
      } finally {
        setBenchmarkLoading(false);
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <BarChart3 className="h-5 w-5 text-purple-500 mr-2" />
              <h3 className="text-lg font-semibold">Comparative Analytics & Benchmarking</h3>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm ${getStatusColor(analyticsData?.status || 'unknown')}`}>
              {analyticsData?.status || 'Unknown'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-900">Benchmark Types</h4>
              <p className="text-sm text-purple-700 mt-1">
                {analyticsData?.supported_benchmarks?.length || 0} benchmark categories
              </p>
              <div className="mt-2 text-xs text-purple-600">
                {analyticsData?.supported_benchmarks?.slice(0, 3).join(', ')}
              </div>
            </div>
            <div className="p-4 bg-indigo-50 rounded-lg">
              <h4 className="font-medium text-indigo-900">Industries</h4>
              <p className="text-sm text-indigo-700 mt-1">
                {analyticsData?.supported_industries?.length || 0} industry verticals
              </p>
              <div className="mt-2 text-xs text-indigo-600">
                Technology, Finance, Healthcare +
              </div>
            </div>
            <div className="p-4 bg-pink-50 rounded-lg">
              <h4 className="font-medium text-pink-900">AI Analytics</h4>
              <p className="text-sm text-pink-700 mt-1">
                {analyticsData?.components?.ai_analytics_engine === 'healthy' ? 'Active' : 'Inactive'}
              </p>
              <div className="mt-2 text-xs text-pink-600">
                Cross-tenant comparisons
              </div>
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center space-x-4 mb-4">
              <select
                value={selectedIndustry}
                onChange={(e) => setSelectedIndustry(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2"
              >
                {analyticsData?.supported_industries?.map(industry => (
                  <option key={industry} value={industry}>
                    {industry.charAt(0).toUpperCase() + industry.slice(1)}
                  </option>
                )) || <option value="general">General</option>}
              </select>
              
              <button
                onClick={generateBenchmark}
                disabled={benchmarkLoading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md disabled:opacity-50 flex items-center"
              >
                <Target className="h-4 w-4 mr-2" />
                {benchmarkLoading ? 'Analyzing...' : 'Generate Benchmark'}
              </button>
            </div>

            {benchmarkResults && (
              <div className="bg-muted rounded-lg p-4">
                <h4 className="font-medium text-foreground mb-4">Benchmark Analysis Results</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Industry</p>
                    <p className="text-lg font-semibold text-foreground capitalize">{benchmarkResults.industry}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Confidence Score</p>
                    <p className="text-lg font-semibold text-purple-600">
                      {(benchmarkResults.confidence_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {benchmarkResults.benchmark_results && benchmarkResults.benchmark_results.length > 0 && (
                  <div className="space-y-3">
                    <h5 className="font-medium text-foreground">Performance Metrics</h5>
                    {benchmarkResults.benchmark_results.map((result, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-card rounded border border-border">
                        <div>
                          <p className="font-medium text-foreground">{result.metric}</p>
                          <p className="text-sm text-muted-foreground">
                            Your: {typeof result.tenant_value === 'number' ? result.tenant_value.toFixed(1) : result.tenant_value} | 
                            Industry Avg: {typeof result.industry_average === 'number' ? result.industry_average.toFixed(1) : result.industry_average}
                          </p>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs ${
                          result.performance === 'above' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {result.performance === 'above' ? '↗ Above Avg' : '↘ Below Avg'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-4">
                  <p className="text-sm text-muted-foreground mb-2">Key Recommendations:</p>
                  <ul className="text-sm space-y-1">
                    {benchmarkResults.recommendations?.slice(0, 3).map((rec, idx) => (
                      <li key={idx} className="flex items-start">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading && !forecastingData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Zap className="h-8 w-8 animate-spin text-purple-500 mx-auto mb-4" />
            <p className="text-muted-foreground">Loading Enterprise Architecture systems...</p>
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
            <h3 className="text-red-800 font-medium">Enterprise Systems Error</h3>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={fetchEnterpriseData}
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
        <h1 className="text-2xl font-bold text-foreground">Enterprise Architecture Dashboard</h1>
        <p className="text-muted-foreground mt-1">Advanced forecasting, security management, and comparative analytics</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-border mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('forecasting')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'forecasting'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <TrendingUp className="h-4 w-4 inline mr-2" />
            Advanced Forecasting
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'security'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <Shield className="h-4 w-4 inline mr-2" />
            Advanced Security
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analytics'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <BarChart3 className="h-4 w-4 inline mr-2" />
            Comparative Analytics
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'forecasting' && <ForecastingDashboard />}
        {activeTab === 'security' && <SecurityDashboard />}
        {activeTab === 'analytics' && <AnalyticsDashboard />}
      </div>

      {/* Enterprise Overview */}
      <div className="mt-8 bg-card rounded-lg p-6 border border-border">
        <h3 className="text-lg font-semibold text-foreground mb-4">Enterprise Systems Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-card rounded border border-border">
            <div className="flex items-center">
              <TrendingUp className="h-5 w-5 text-blue-500 mr-3" />
              <div>
                <p className="font-medium text-foreground">Forecasting Engine</p>
                <p className="text-sm text-muted-foreground">AI-powered predictions</p>
              </div>
            </div>
            {getStatusIcon(forecastingData?.status || 'unknown')}
          </div>
          
          <div className="flex items-center justify-between p-4 bg-card rounded border border-border">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-red-500 mr-3" />
              <div>
                <p className="font-medium text-foreground">Security Manager</p>
                <p className="text-sm text-muted-foreground">Enterprise security</p>
              </div>
            </div>
            {getStatusIcon(securityData?.status || 'unknown')}
          </div>
          
          <div className="flex items-center justify-between p-4 bg-card rounded border border-border">
            <div className="flex items-center">
              <BarChart3 className="h-5 w-5 text-purple-500 mr-3" />
              <div>
                <p className="font-medium text-foreground">Analytics Engine</p>
                <p className="text-sm text-muted-foreground">Comparative insights</p>
              </div>
            </div>
            {getStatusIcon(analyticsData?.status || 'unknown')}
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(EnterpriseArchitectureDashboard);