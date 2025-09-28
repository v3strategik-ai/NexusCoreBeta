import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Brain, Zap, BarChart3, Cpu, MessageCircle, TrendingUp, Settings, RefreshCw, Play, GitCompare, Activity, Clock, DollarSign, Star } from 'lucide-react';

const AIModelRouter = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [availableModels, setAvailableModels] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Chat state
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState(null);
  const [selectedTaskType, setSelectedTaskType] = useState('conversation');
  const [selectedModel, setSelectedModel] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Comparison state
  const [comparisonMessage, setComparisonMessage] = useState('');
  const [comparisonModels, setComparisonModels] = useState(['gpt-5', 'claude-4-sonnet-20250514']);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  // Backend URL from environment variables
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Task types for the dropdown
  const taskTypes = [
    { value: 'conversation', label: 'General Conversation', icon: MessageCircle },
    { value: 'reasoning', label: 'Complex Reasoning', icon: Brain },
    { value: 'creative', label: 'Creative Writing', icon: Zap },
    { value: 'analysis', label: 'Data Analysis', icon: BarChart3 },
    { value: 'coding', label: 'Programming', icon: Cpu },
    { value: 'forecasting', label: 'Business Forecasting', icon: TrendingUp },
    { value: 'summarization', label: 'Summarization', icon: Settings },
    { value: 'classification', label: 'Classification', icon: Activity }
  ];

  // Fetch AI models and performance data
  const fetchAIData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch available models
      const modelsResponse = await fetch(`${backendUrl}/api/ai-models/models`);
      const modelsData = await modelsResponse.json();
      setAvailableModels(modelsData);
      
      // Fetch performance metrics
      const performanceResponse = await fetch(`${backendUrl}/api/ai-models/performance`);
      const performanceData = await performanceResponse.json();
      setPerformanceMetrics(performanceData);
      
      setError(null);
    } catch (error) {
      console.error('Error fetching AI data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    fetchAIData();
  }, [fetchAIData]);

  // Send chat message
  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return;
    
    try {
      setChatLoading(true);
      const response = await fetch(`${backendUrl}/api/ai-models/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatMessage,
          task_type: selectedTaskType,
          preferred_model: selectedModel || null,
          temperature: 0.7
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setChatResponse(result);
        fetchAIData(); // Refresh performance data
      } else {
        throw new Error('Failed to get AI response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.message);
    } finally {
      setChatLoading(false);
    }
  };

  // Compare multiple models
  const handleCompareModels = async () => {
    if (!comparisonMessage.trim() || comparisonModels.length < 2) return;
    
    try {
      setComparisonLoading(true);
      const response = await fetch(`${backendUrl}/api/ai-models/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: comparisonMessage,
          task_type: selectedTaskType,
          models: comparisonModels,
          temperature: 0.7
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setComparisonResults(result);
        fetchAIData(); // Refresh performance data
      } else {
        throw new Error('Failed to compare models');
      }
    } catch (error) {
      console.error('Error comparing models:', error);
      setError(error.message);
    } finally {
      setComparisonLoading(false);
    }
  };

  // Get model recommendation
  const getModelRecommendation = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/ai-models/route?task_type=${selectedTaskType}&message_preview=${encodeURIComponent(chatMessage.substring(0, 100))}&consider_cost=false`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        setSelectedModel(result.recommended_model);
      }
    } catch (error) {
      console.error('Error getting recommendation:', error);
    }
  };

  const getProviderColor = (provider) => {
    switch (provider) {
      case 'openai': return 'text-green-600 bg-green-50';
      case 'anthropic': return 'text-orange-600 bg-orange-50';
      case 'google': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getTaskIcon = (taskType) => {
    const task = taskTypes.find(t => t.value === taskType);
    return task ? task.icon : MessageCircle;
  };

  if (loading && !availableModels) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Brain className="h-8 w-8 animate-pulse text-blue-500 mx-auto mb-4" />
            <p className="text-gray-600">Loading AI Model Router...</p>
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
            <Brain className="h-5 w-5 text-red-500 mr-2" />
            <h3 className="text-red-800 font-medium">AI Model Router Error</h3>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={fetchAIData}
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
            <h1 className="text-2xl font-bold text-foreground">AI Model Router</h1>
            <p className="text-muted-foreground mt-1">Multi-model AI integration with intelligent task routing</p>
          </div>
          
          <button
            onClick={fetchAIData}
            disabled={loading}
            className="flex items-center space-x-2 bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Models Overview */}
      {availableModels && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card rounded-lg border border-border p-4">
            <div className="flex items-center">
              <Brain className="h-5 w-5 text-blue-500 mr-2" />
              <div>
                <p className="font-medium text-foreground">Total Models</p>
                <p className="text-2xl font-bold text-primary">{availableModels.total_models}</p>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-4">
            <div className="flex items-center">
              <Activity className="h-5 w-5 text-green-500 mr-2" />
              <div>
                <p className="font-medium text-foreground">Providers</p>
                <p className="text-2xl font-bold text-primary">{availableModels.providers.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-4">
            <div className="flex items-center">
              <Settings className="h-5 w-5 text-purple-500 mr-2" />
              <div>
                <p className="font-medium text-foreground">Task Types</p>
                <p className="text-2xl font-bold text-primary">{taskTypes.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-4">
            <div className="flex items-center">
              <MessageCircle className="h-5 w-5 text-orange-500 mr-2" />
              <div>
                <p className="font-medium text-foreground">Total Requests</p>
                <p className="text-2xl font-bold text-primary">
                  {performanceMetrics?.total_requests || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-border mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('chat')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'chat'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <MessageCircle className="h-4 w-4 inline mr-2" />
            Smart Chat
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'compare'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <GitCompare className="h-4 w-4 inline mr-2" />
            Model Comparison
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'performance'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <BarChart3 className="h-4 w-4 inline mr-2" />
            Performance
          </button>
          <button
            onClick={() => setActiveTab('models')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'models'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            <Brain className="h-4 w-4 inline mr-2" />
            Models
          </button>
        </nav>
      </div>

      {/* Smart Chat Tab */}
      {activeTab === 'chat' && (
        <div className="space-y-6">
          <div className="bg-card rounded-lg border border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Smart AI Chat with Intelligent Routing</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Task Type</label>
                  <select
                    value={selectedTaskType}
                    onChange={(e) => setSelectedTaskType(e.target.value)}
                    className="w-full border border-border rounded-md px-3 py-2 bg-card text-foreground"
                  >
                    {taskTypes.map((task) => (
                      <option key={task.value} value={task.value}>
                        {task.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Preferred Model (Optional)</label>
                  <div className="flex space-x-2">
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="flex-1 border border-border rounded-md px-3 py-2 bg-card text-foreground"
                    >
                      <option value="">Auto-Route (Recommended)</option>
                      {availableModels && Object.keys(availableModels.available_models).map((model) => (
                        <option key={model} value={model}>
                          {model} ({availableModels.available_models[model].provider})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={getModelRecommendation}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-md text-sm"
                    >
                      <Brain className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Message</label>
                <textarea
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="Enter your message here..."
                  rows={4}
                  className="w-full border border-border rounded-md px-3 py-2 bg-card text-foreground"
                />
              </div>

              <button
                onClick={handleSendMessage}
                disabled={chatLoading || !chatMessage.trim()}
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-md disabled:opacity-50 flex items-center"
              >
                <Play className="h-4 w-4 mr-2" />
                {chatLoading ? 'Processing...' : 'Send Message'}
              </button>
            </div>

            {chatResponse && (
              <div className="mt-6 bg-muted/50 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${getProviderColor(chatResponse.provider)}`}>
                      {chatResponse.model_used}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {(chatResponse.processing_time * 1000).toFixed(0)}ms
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ~${chatResponse.cost_estimate?.toFixed(4) || '0.0000'}
                    </span>
                  </div>
                </div>
                <p className="text-foreground whitespace-pre-wrap">{chatResponse.response}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Model Comparison Tab */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <div className="bg-card rounded-lg border border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Compare Multiple AI Models</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Select Models to Compare</label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {availableModels && Object.keys(availableModels.available_models).map((model) => (
                    <label key={model} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={comparisonModels.includes(model)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setComparisonModels([...comparisonModels, model]);
                          } else {
                            setComparisonModels(comparisonModels.filter(m => m !== model));
                          }
                        }}
                        className="mr-2"
                      />
                      <span className="text-sm text-foreground">
                        {model} ({availableModels.available_models[model].provider})
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Message to Compare</label>
                <textarea
                  value={comparisonMessage}
                  onChange={(e) => setComparisonMessage(e.target.value)}
                  placeholder="Enter a message to send to all selected models..."
                  rows={3}
                  className="w-full border border-border rounded-md px-3 py-2 bg-card text-foreground"
                />
              </div>

              <button
                onClick={handleCompareModels}
                disabled={comparisonLoading || !comparisonMessage.trim() || comparisonModels.length < 2}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md disabled:opacity-50 flex items-center"
              >
                <GitCompare className="h-4 w-4 mr-2" />
                {comparisonLoading ? 'Comparing...' : `Compare ${comparisonModels.length} Models`}
              </button>
            </div>

            {comparisonResults && (
              <div className="mt-6 space-y-4">
                <h4 className="font-medium text-foreground">Comparison Results</h4>
                {comparisonResults.results.map((result, index) => (
                  <div key={index} className="bg-muted/50 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getProviderColor(result.provider)}`}>
                          {result.model}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {(result.processing_time * 1000).toFixed(0)}ms
                        </span>
                        <span className="text-xs text-muted-foreground">
                          <DollarSign className="h-3 w-3 inline mr-1" />
                          ${result.cost_estimate?.toFixed(4) || '0.0000'}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-foreground whitespace-pre-wrap">{result.response}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && performanceMetrics && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card rounded-lg border border-border p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Top Models by Usage</h3>
              <div className="space-y-3">
                {performanceMetrics.top_models_by_usage.slice(0, 5).map(([model, metrics], index) => (
                  <div key={model} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground">#{index + 1}</span>
                      <span className="ml-3 text-sm text-foreground">{model}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-foreground">{metrics.total_requests} requests</div>
                      <div className="text-xs text-muted-foreground">
                        {(metrics.avg_response_time * 1000).toFixed(0)}ms avg
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card rounded-lg border border-border p-6">
              <h3 className="text-lg font-semibold text-foreground mb-4">Performance Overview</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Analysis Period</span>
                    <span className="text-foreground">{performanceMetrics.analysis_period_days} days</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total Requests</span>
                    <span className="text-foreground">{performanceMetrics.total_requests}</span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Active Models</span>
                    <span className="text-foreground">{Object.keys(performanceMetrics.model_performance).length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && availableModels && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(availableModels.available_models).map(([model, info]) => (
              <div key={model} className="bg-card rounded-lg border border-border p-6">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-semibold text-foreground">{model}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs ${getProviderColor(info.provider)}`}>
                    {info.provider}
                  </span>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Reasoning</span>
                    <span className="text-foreground">{(info.capabilities.reasoning_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Creativity</span>
                    <span className="text-foreground">{(info.capabilities.creativity_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Speed</span>
                    <span className="text-foreground">{(info.capabilities.speed_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Cost Efficiency</span>
                    <span className="text-foreground">{(info.capabilities.cost_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="text-xs text-muted-foreground mb-2">Best for:</div>
                <div className="flex flex-wrap gap-1">
                  {info.recommended_for.slice(0, 3).map((task) => {
                    const TaskIcon = getTaskIcon(task);
                    return (
                      <span key={task} className="inline-flex items-center px-2 py-1 bg-muted rounded-full text-xs text-muted-foreground">
                        <TaskIcon className="h-3 w-3 mr-1" />
                        {task}
                      </span>
                    );
                  })}
                </div>

                {info.capabilities.multimodal && (
                  <div className="mt-2">
                    <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      <Star className="h-3 w-3 mr-1" />
                      Multimodal
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(AIModelRouter);