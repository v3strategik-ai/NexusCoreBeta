import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Progress } from './ui/progress'
import { 
  Activity, 
  Users, 
  Target, 
  FileText, 
  Zap,
  Wifi,
  WifiOff,
  Bell,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import io from 'socket.io-client'
import { toast } from 'react-toastify'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

export function RealTimeDashboard() {
  const [isConnected, setIsConnected] = useState(false)
  const [liveMetrics, setLiveMetrics] = useState(null)
  const [activityStream, setActivityStream] = useState([])
  const [agentStatuses, setAgentStatuses] = useState([])
  const [pipelineData, setPipelineData] = useState(null)
  const [systemAlerts, setSystemAlerts] = useState([])
  const [connectionStats, setConnectionStats] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const socketRef = useRef(null)
  const metricsHistoryRef = useRef([])

  useEffect(() => {
    initializeRealTime()
    loadInitialData()

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect()
      }
    }
  }, [])

  const initializeRealTime = () => {
    try {
      // Initialize Socket.IO connection
      socketRef.current = io(BACKEND_URL, {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        forceNew: true
      })

      // Connection event handlers
      socketRef.current.on('connect', () => {
        console.log('Connected to real-time server')
        setIsConnected(true)
        
        // Subscribe to channels
        socketRef.current.emit('subscribe', { channel: 'dashboard_metrics' })
        socketRef.current.emit('subscribe', { channel: 'activity_feed' })
        socketRef.current.emit('subscribe', { channel: 'agent_status' })
        socketRef.current.emit('subscribe', { channel: 'lead_updates' })
        socketRef.current.emit('subscribe', { channel: 'notifications' })

        toast.success('Connected to real-time updates', {
          position: 'top-right',
          autoClose: 3000
        })
      })

      socketRef.current.on('disconnect', () => {
        console.log('Disconnected from real-time server')
        setIsConnected(false)
        toast.warning('Real-time connection lost', {
          position: 'top-right',
          autoClose: 5000
        })
      })

      // Data event handlers
      socketRef.current.on('dashboard_update', (data) => {
        setLiveMetrics(data)
        setLastUpdate(new Date())
        
        // Add to metrics history for charts
        if (metricsHistoryRef.current.length >= 20) {
          metricsHistoryRef.current.shift()
        }
        metricsHistoryRef.current.push({
          timestamp: new Date().toLocaleTimeString(),
          leads: data.leads?.total || 0,
          pipeline: data.leads?.pipeline_value || 0,
          agents: data.agents?.active || 0
        })
      })

      socketRef.current.on('new_activity', (activity) => {
        setActivityStream(prev => [activity, ...prev.slice(0, 9)]) // Keep latest 10
      })

      socketRef.current.on('agent_status_update', (agentStatus) => {
        setAgentStatuses(prev => {
          const updated = prev.filter(agent => agent.agent_id !== agentStatus.agent_id)
          return [agentStatus, ...updated]
        })
      })

      socketRef.current.on('lead_update', (leadUpdate) => {
        // Show notification for hot leads
        if (leadUpdate.lead?.status === 'hot') {
          toast.success(`🔥 Hot Lead: ${leadUpdate.lead.name}`, {
            position: 'top-right',
            autoClose: 5000
          })
        }
      })

      socketRef.current.on('notification', (notification) => {
        const toastType = notification.type === 'error' ? 'error' : 
                         notification.type === 'warning' ? 'warning' :
                         notification.type === 'success' ? 'success' : 'info'
        
        toast[toastType](`${notification.title}: ${notification.message}`, {
          position: 'top-right',
          autoClose: 5000
        })
      })

      // Error handling
      socketRef.current.on('connect_error', (error) => {
        console.error('Socket connection error:', error)
        setIsConnected(false)
      })

    } catch (error) {
      console.error('Error initializing real-time connection:', error)
    }
  }

  const loadInitialData = async () => {
    try {
      setIsLoading(true)
      
      // Load initial metrics
      const metricsResponse = await fetch(`${BACKEND_URL}/api/realtime/metrics/live`)
      if (metricsResponse.ok) {
        const metrics = await metricsResponse.json()
        setLiveMetrics(metrics)
      }

      // Load activity stream
      const activityResponse = await fetch(`${BACKEND_URL}/api/realtime/activities/stream?limit=10`)
      if (activityResponse.ok) {
        const activity = await activityResponse.json()
        setActivityStream(activity.activities || [])
      }

      // Load agent statuses
      const agentsResponse = await fetch(`${BACKEND_URL}/api/realtime/agents/status`)
      if (agentsResponse.ok) {
        const agents = await agentsResponse.json()
        setAgentStatuses(agents.agents || [])
      }

      // Load pipeline data
      const pipelineResponse = await fetch(`${BACKEND_URL}/api/realtime/leads/pipeline`)
      if (pipelineResponse.ok) {
        const pipeline = await pipelineResponse.json()
        setPipelineData(pipeline)
      }

      // Load system alerts
      const alertsResponse = await fetch(`${BACKEND_URL}/api/realtime/system/alerts`)
      if (alertsResponse.ok) {
        const alerts = await alertsResponse.json()
        setSystemAlerts(alerts.alerts || [])
      }

      // Load WebSocket stats
      const statsResponse = await fetch(`${BACKEND_URL}/api/realtime/websocket/stats`)
      if (statsResponse.ok) {
        const stats = await statsResponse.json()
        setConnectionStats(stats.connections)
      }

      setLastUpdate(new Date())

    } catch (error) {
      console.error('Error loading initial data:', error)
      toast.error('Failed to load dashboard data', {
        position: 'top-right',
        autoClose: 5000
      })
    } finally {
      setIsLoading(false)
    }
  }

  const refreshData = () => {
    loadInitialData()
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit('subscribe', { channel: 'dashboard_metrics' })
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400'
      case 'inactive': return 'text-gray-400'
      case 'error': return 'text-red-400'
      default: return 'text-yellow-400'
    }
  }

  const getActivityTypeIcon = (type) => {
    switch (type) {
      case 'lead_created': return <Target className="w-4 h-4 text-blue-400" />
      case 'agent_updated': return <Users className="w-4 h-4 text-green-400" />
      case 'document_generated': return <FileText className="w-4 h-4 text-purple-400" />
      case 'email_sent': return <Bell className="w-4 h-4 text-orange-400" />
      case 'workflow_execution': return <Zap className="w-4 h-4 text-cyan-400" />
      default: return <Activity className="w-4 h-4 text-gray-400" />
    }
  }

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num?.toString() || '0'
  }

  if (isLoading && !liveMetrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading real-time dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Connection Status */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold gradient-text">Real-Time Intelligence</h2>
          <p className="text-muted-foreground">Live monitoring and system insights</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="w-5 h-5 text-green-400" />
                <span className="text-sm text-green-400">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-red-400" />
                <span className="text-sm text-red-400">Offline</span>
              </>
            )}
          </div>
          {lastUpdate && (
            <div className="text-sm text-muted-foreground">
              Last update: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <Button variant="outline" size="sm" onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Live Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="quantum-bg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
            <Target className="w-4 h-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveMetrics?.leads?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              +{liveMetrics?.leads?.recent_leads_24h || 0} in last 24h
            </p>
          </CardContent>
        </Card>

        <Card className="quantum-bg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pipeline Value</CardTitle>
            <TrendingUp className="w-4 h-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${formatNumber(liveMetrics?.leads?.pipeline_value || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {liveMetrics?.leads?.hot_leads || 0} hot leads
            </p>
          </CardContent>
        </Card>

        <Card className="quantum-bg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="w-4 h-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveMetrics?.agents?.active || 0}</div>
            <p className="text-xs text-muted-foreground">
              {liveMetrics?.agents?.utilization || 0}% utilization
            </p>
          </CardContent>
        </Card>

        <Card className="quantum-bg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Activity className="w-4 h-4 text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-green-400" />
              Excellent
            </div>
            <p className="text-xs text-muted-foreground">
              {connectionStats?.total_connections || 0} live connections
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="quantum-bg">
          <CardHeader>
            <CardTitle>Live Metrics Trend</CardTitle>
            <CardDescription>Real-time performance over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={metricsHistoryRef.current}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="leads" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="agents" stroke="#8b5cf6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="quantum-bg">
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
            <CardDescription>Sales pipeline breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {pipelineData && (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={pipelineData.pipeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="status" />
                  <YAxis />
                  <Tooltip formatter={(value) => `$${formatNumber(value)}`} />
                  <Bar dataKey="total_value" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity Stream and Agent Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="quantum-bg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Live Activity Feed
            </CardTitle>
            <CardDescription>Real-time system activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {activityStream.map((activity, index) => (
                <div key={activity.id || index} className="flex items-center gap-3 p-2 rounded-lg bg-card/50">
                  {getActivityTypeIcon(activity.activity_type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{activity.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {activity.agent_name} • {new Date(activity.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {activityStream.length === 0 && (
                <div className="text-center text-muted-foreground py-4">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No recent activities</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="quantum-bg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Agent Status Monitor
            </CardTitle>
            <CardDescription>Live agent performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {agentStatuses.slice(0, 6).map((agent, index) => (
                <div key={agent.id || index} className="flex items-center justify-between p-2 rounded-lg bg-card/50">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                    <div>
                      <p className="text-sm font-medium">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">{agent.type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{agent.readiness_score || 0}%</p>
                    <p className="text-xs text-muted-foreground">Ready</p>
                  </div>
                </div>
              ))}
              {agentStatuses.length === 0 && (
                <div className="text-center text-muted-foreground py-4">
                  <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No agent data available</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Alerts */}
      {systemAlerts.length > 0 && (
        <Card className="quantum-bg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-400" />
              System Alerts
            </CardTitle>
            <CardDescription>Current system notifications and warnings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {systemAlerts.map((alert, index) => (
                <div key={alert.id || index} className="flex items-center gap-3 p-3 rounded-lg border border-border/50">
                  <AlertCircle className={`w-4 h-4 ${
                    alert.severity === 'critical' ? 'text-red-400' :
                    alert.severity === 'high' ? 'text-orange-400' :
                    alert.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{alert.title}</p>
                    <p className="text-xs text-muted-foreground">{alert.message}</p>
                  </div>
                  <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                    {alert.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}