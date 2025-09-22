import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
import { Input } from './ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  DollarSign, 
  Users, 
  Activity, 
  Target,
  FileText,
  Mail,
  Zap,
  Calendar,
  Download,
  RefreshCw,
  Filter,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

export function AnalyticsDashboard() {
  const [kpis, setKpis] = useState([])
  const [roiAnalysis, setRoiAnalysis] = useState(null)
  const [forecasts, setForecasts] = useState({})
  const [dashboardSummary, setDashboardSummary] = useState(null)
  const [selectedTimeRange, setSelectedTimeRange] = useState('last_30_days')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  const timeRangeOptions = [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'last_7_days', label: 'Last 7 Days' },
    { value: 'last_30_days', label: 'Last 30 Days' },
    { value: 'last_90_days', label: 'Last 90 Days' },
    { value: 'last_year', label: 'Last Year' }
  ]

  useEffect(() => {
    fetchAnalyticsData()
  }, [selectedTimeRange])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch dashboard summary (includes KPIs, ROI, and forecasts)
      const summaryResponse = await fetch(
        `${BACKEND_URL}/api/analytics/dashboard/summary?time_range=${selectedTimeRange}`
      )
      
      if (!summaryResponse.ok) {
        throw new Error('Failed to fetch analytics data')
      }

      const summaryData = await summaryResponse.json()
      
      setDashboardSummary(summaryData)
      setKpis(summaryData.kpis || [])
      setRoiAnalysis(summaryData.roi_analysis || null)
      setForecasts(summaryData.forecasts || {})

    } catch (err) {
      console.error('Error fetching analytics data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchAnalyticsData()
    setRefreshing(false)
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />
      default:
        return <Minus className="w-4 h-4 text-gray-500" />
    }
  }

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up':
        return 'text-green-500'
      case 'down':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  const formatValue = (value, formatType, unit) => {
    if (value === null || value === undefined) return 'N/A'
    
    switch (formatType) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(value)
      case 'percentage':
        return `${value}%`
      case 'number':
        return new Intl.NumberFormat('en-US').format(value)
      default:
        return `${value}${unit ? ' ' + unit : ''}`
    }
  }

  const getKpiIcon = (name) => {
    const iconMap = {
      'Total Leads': Users,
      'Conversion Rate': Target,
      'Pipeline Value': DollarSign,
      'Average Deal Size': DollarSign,
      'Agent Efficiency': Activity,
      'Document Generation Rate': FileText,
      'Sales Velocity': TrendingUp
    }
    const IconComponent = iconMap[name] || BarChart3
    return <IconComponent className="w-5 h-5 text-blue-500" />
  }

  const ForecastCard = ({ title, forecast }) => (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-500" />
          {title} Forecast
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Value</span>
            <span className="font-semibold">{forecast.current_value?.toFixed(2) || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Confidence</span>
            <div className="flex items-center gap-2">
              <Progress value={forecast.confidence_score * 100} className="w-16 h-2" />
              <span className="text-sm font-medium">
                {((forecast.confidence_score || 0) * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="text-xs text-muted-foreground line-clamp-2">
            {forecast.trend_analysis}
          </div>
          <div className="text-xs">
            <span className="text-muted-foreground">Next 14 days: </span>
            <span className="font-medium">
              {forecast.forecasted_values?.length || 0} predictions
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-lg">Loading analytics data...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-500" />
              <div>
                <h3 className="font-semibold text-red-900">Error Loading Analytics</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
            <Button onClick={handleRefresh} className="mt-4" variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold gradient-text">Advanced Analytics</h2>
          <p className="text-muted-foreground">
            Comprehensive business intelligence and performance insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRangeOptions.map(option => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button 
            onClick={handleRefresh} 
            variant="outline" 
            size="sm"
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="kpis">KPIs</TabsTrigger>
          <TabsTrigger value="roi">ROI Analysis</TabsTrigger>
          <TabsTrigger value="forecasting">Forecasting</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {dashboardSummary && (
            <>
              {/* Summary Insights */}
              <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-500" />
                    Executive Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {dashboardSummary.summary_insights?.roi_status === 'positive' ? '↗' : '↘'}
                      </div>
                      <div className="text-sm text-muted-foreground">ROI Status</div>
                      <div className="font-semibold">
                        {dashboardSummary.summary_insights?.roi_status || 'Unknown'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {dashboardSummary.summary_insights?.forecast_confidence || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Forecast Confidence</div>
                      <div className="font-semibold">Average Score</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {dashboardSummary.summary_insights?.recommendations_count || 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Recommendations</div>
                      <div className="font-semibold">Available</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {kpis.length}
                      </div>
                      <div className="text-sm text-muted-foreground">KPIs Tracked</div>
                      <div className="font-semibold">Metrics</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Top KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {kpis.slice(0, 6).map((kpi) => (
                  <Card key={kpi.name} className="hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getKpiIcon(kpi.name)}
                          {kpi.name}
                        </div>
                        {getTrendIcon(kpi.trend)}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="text-2xl font-bold">
                          {formatValue(kpi.value, kpi.format_type, kpi.unit)}
                        </div>
                        {kpi.change_percentage !== null && (
                          <div className={`text-sm flex items-center gap-1 ${getTrendColor(kpi.trend)}`}>
                            {kpi.change_percentage > 0 ? '+' : ''}{kpi.change_percentage}%
                            <span className="text-muted-foreground">vs previous period</span>
                          </div>
                        )}
                        {kpi.target && (
                          <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Target Progress</span>
                              <span>{kpi.target_percentage || 0}%</span>
                            </div>
                            <Progress value={kpi.target_percentage || 0} className="h-2" />
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* KPIs Tab */}
        <TabsContent value="kpis" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {kpis.map((kpi) => (
              <Card key={kpi.name} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg">
                    <div className="flex items-center gap-2">
                      {getKpiIcon(kpi.name)}
                      {kpi.name}
                    </div>
                    <Badge variant={kpi.trend === 'up' ? 'default' : kpi.trend === 'down' ? 'destructive' : 'secondary'}>
                      {kpi.trend}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-3xl font-bold">
                      {formatValue(kpi.value, kpi.format_type, kpi.unit)}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Previous Value</div>
                        <div className="font-semibold">
                          {formatValue(kpi.previous_value, kpi.format_type, kpi.unit)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Change</div>
                        <div className={`font-semibold ${getTrendColor(kpi.trend)}`}>
                          {kpi.change_percentage > 0 ? '+' : ''}{kpi.change_percentage}%
                        </div>
                      </div>
                    </div>

                    {kpi.target && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Target: {formatValue(kpi.target, kpi.format_type, kpi.unit)}</span>
                          <span className="font-semibold">{kpi.target_percentage || 0}%</span>
                        </div>
                        <Progress value={kpi.target_percentage || 0} className="h-2" />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ROI Analysis Tab */}
        <TabsContent value="roi" className="space-y-6">
          {roiAnalysis && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="md:col-span-2 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <DollarSign className="w-6 h-6 text-green-500" />
                    ROI Analysis Summary
                  </CardTitle>
                  <CardDescription>
                    Investment performance and return analysis for {selectedTimeRange.replace('_', ' ')}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {roiAnalysis.roi_percentage}%
                      </div>
                      <div className="text-sm text-muted-foreground">ROI Percentage</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Ratio: {roiAnalysis.roi_ratio}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {formatValue(roiAnalysis.net_profit, 'currency')}
                      </div>
                      <div className="text-sm text-muted-foreground">Net Profit</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Margin: {roiAnalysis.margin_percentage}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {roiAnalysis.payback_period_months ? `${roiAnalysis.payback_period_months}mo` : 'N/A'}
                      </div>
                      <div className="text-sm text-muted-foreground">Payback Period</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Time to break even
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Investment Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Total Investment</span>
                      <span className="font-semibold text-lg">
                        {formatValue(roiAnalysis.investment, 'currency')}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Total Revenue</span>
                      <span className="font-semibold text-lg text-green-600">
                        {formatValue(roiAnalysis.revenue, 'currency')}
                      </span>
                    </div>
                    <div className="border-t pt-4">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold">Net Profit</span>
                        <span className={`font-bold text-lg ${roiAnalysis.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatValue(roiAnalysis.net_profit, 'currency')}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>ROI Percentage</span>
                        <span>{roiAnalysis.roi_percentage}%</span>
                      </div>
                      <Progress 
                        value={Math.min(Math.max(roiAnalysis.roi_percentage, 0), 100)} 
                        className="h-2" 
                      />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Profit Margin</span>
                        <span>{roiAnalysis.margin_percentage}%</span>
                      </div>
                      <Progress 
                        value={Math.min(Math.max(roiAnalysis.margin_percentage, 0), 100)} 
                        className="h-2" 
                      />
                    </div>
                    <div className="pt-2 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        ROI calculated based on converted leads and operational costs
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Forecasting Tab */}
        <TabsContent value="forecasting" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {forecasts.conversion_rate && (
              <ForecastCard 
                title="Conversion Rate" 
                forecast={forecasts.conversion_rate}
              />
            )}
            {forecasts.lead_generation && (
              <ForecastCard 
                title="Lead Generation" 
                forecast={forecasts.lead_generation}
              />
            )}
          </div>

          {/* Recommendations */}
          {forecasts.conversion_rate?.recommendations && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-orange-500" />
                  AI Recommendations
                </CardTitle>
                <CardDescription>
                  Data-driven suggestions to improve performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {forecasts.conversion_rate.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg">
                      <div className="w-6 h-6 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-xs font-semibold text-orange-600">{index + 1}</span>
                      </div>
                      <div className="text-sm">{recommendation}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}