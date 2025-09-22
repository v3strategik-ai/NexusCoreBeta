import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Label } from './ui/label'
import { 
  TestTube, 
  Play, 
  Pause, 
  BarChart3, 
  Users, 
  Target,
  Plus,
  Settings,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  Mail,
  Activity,
  RefreshCw,
  Eye,
  Trash2,
  Edit
} from 'lucide-react'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

export function ABTestingManager() {
  const [activeTests, setActiveTests] = useState([])
  const [testTemplates, setTestTemplates] = useState([])
  const [selectedTest, setSelectedTest] = useState(null)
  const [testAnalysis, setTestAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  // Form state for creating new tests
  const [newTest, setNewTest] = useState({
    name: '',
    description: '',
    test_type: 'email_campaign',
    variants: [
      { name: 'Control', description: '', variant_type: 'control', traffic_percentage: 50, configuration: {} },
      { name: 'Variant A', description: '', variant_type: 'variant', traffic_percentage: 50, configuration: {} }
    ],
    metrics: [
      { metric_type: 'conversion_rate', name: 'Conversion Rate', description: 'Primary conversion metric', is_primary: true }
    ],
    min_sample_size: 100,
    confidence_level: 0.95,
    target_audience: {}
  })

  const testTypes = [
    { value: 'email_campaign', label: 'Email Campaign', icon: Mail, description: 'Test email subject lines, content, or timing' },
    { value: 'workflow', label: 'Workflow', icon: Activity, description: 'Test different workflow configurations' },
    { value: 'lead_scoring', label: 'Lead Scoring', icon: Target, description: 'Compare lead scoring algorithms' },
    { value: 'agent_configuration', label: 'Agent Configuration', icon: Settings, description: 'Test AI agent settings' },
    { value: 'ui_component', label: 'UI Component', icon: Eye, description: 'Test user interface elements' }
  ]

  const metricTypes = [
    { value: 'conversion_rate', label: 'Conversion Rate' },
    { value: 'click_rate', label: 'Click Rate' },
    { value: 'open_rate', label: 'Open Rate' },
    { value: 'completion_rate', label: 'Completion Rate' },
    { value: 'revenue', label: 'Revenue' },
    { value: 'engagement', label: 'Engagement' }
  ]

  useEffect(() => {
    fetchActiveTests()
    fetchTestTemplates()
  }, [])

  const fetchActiveTests = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${BACKEND_URL}/api/ab-testing/tests/active`)
      if (response.ok) {
        const data = await response.json()
        setActiveTests(data.active_tests || [])
      }
    } catch (err) {
      console.error('Error fetching active tests:', err)
      setError('Failed to load active tests')
    } finally {
      setLoading(false)
    }
  }

  const fetchTestTemplates = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-testing/tests/templates`)
      if (response.ok) {
        const data = await response.json()
        setTestTemplates(data.templates || [])
      }
    } catch (err) {
      console.error('Error fetching test templates:', err)
    }
  }

  const fetchTestAnalysis = async (testId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-testing/tests/${testId}/analysis`)
      if (response.ok) {
        const analysis = await response.json()
        setTestAnalysis(analysis)
      }
    } catch (err) {
      console.error('Error fetching test analysis:', err)
      setError('Failed to load test analysis')
    }
  }

  const createTest = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-testing/tests/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newTest)
      })

      if (response.ok) {
        const result = await response.json()
        setShowCreateDialog(false)
        await fetchActiveTests()
        // Reset form
        setNewTest({
          name: '',
          description: '',
          test_type: 'email_campaign',
          variants: [
            { name: 'Control', description: '', variant_type: 'control', traffic_percentage: 50, configuration: {} },
            { name: 'Variant A', description: '', variant_type: 'variant', traffic_percentage: 50, configuration: {} }
          ],
          metrics: [
            { metric_type: 'conversion_rate', name: 'Conversion Rate', description: 'Primary conversion metric', is_primary: true }
          ],
          min_sample_size: 100,
          confidence_level: 0.95,
          target_audience: {}
        })
      } else {
        throw new Error('Failed to create test')
      }
    } catch (err) {
      console.error('Error creating test:', err)
      setError('Failed to create test')
    }
  }

  const startTest = async (testId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/ab-testing/tests/${testId}/start`, {
        method: 'POST'
      })

      if (response.ok) {
        await fetchActiveTests()
      } else {
        throw new Error('Failed to start test')
      }
    } catch (err) {
      console.error('Error starting test:', err)
      setError('Failed to start test')
    }
  }

  const addVariant = () => {
    const totalPercentage = newTest.variants.reduce((sum, v) => sum + v.traffic_percentage, 0)
    const remainingPercentage = Math.max(0, 100 - totalPercentage)
    
    setNewTest({
      ...newTest,
      variants: [
        ...newTest.variants,
        {
          name: `Variant ${String.fromCharCode(65 + newTest.variants.length - 1)}`,
          description: '',
          variant_type: 'variant',
          traffic_percentage: Math.min(remainingPercentage, 25),
          configuration: {}
        }
      ]
    })
  }

  const updateVariant = (index, field, value) => {
    const newVariants = [...newTest.variants]
    newVariants[index] = { ...newVariants[index], [field]: value }
    setNewTest({ ...newTest, variants: newVariants })
  }

  const removeVariant = (index) => {
    if (newTest.variants.length > 2) {
      const newVariants = newTest.variants.filter((_, i) => i !== index)
      setNewTest({ ...newTest, variants: newVariants })
    }
  }

  const addMetric = () => {
    setNewTest({
      ...newTest,
      metrics: [
        ...newTest.metrics,
        {
          metric_type: 'click_rate',
          name: 'New Metric',
          description: '',
          is_primary: false
        }
      ]
    })
  }

  const updateMetric = (index, field, value) => {
    const newMetrics = [...newTest.metrics]
    newMetrics[index] = { ...newMetrics[index], [field]: value }
    setNewTest({ ...newTest, metrics: newMetrics })
  }

  const removeMetric = (index) => {
    if (newTest.metrics.length > 1) {
      const newMetrics = newTest.metrics.filter((_, i) => i !== index)
      setNewTest({ ...newTest, metrics: newMetrics })
    }
  }

  const getTestTypeIcon = (type) => {
    const testType = testTypes.find(t => t.value === type)
    return testType ? testType.icon : TestTube
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'bg-green-500'
      case 'paused':
        return 'bg-yellow-500'
      case 'completed':
        return 'bg-blue-500'
      case 'stopped':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusBadgeVariant = (status) => {
    switch (status) {
      case 'running':
        return 'default'
      case 'paused':
        return 'secondary'
      case 'completed':
        return 'default'
      case 'stopped':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-lg">Loading A/B testing data...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold gradient-text">A/B Testing Manager</h2>
          <p className="text-muted-foreground">
            Create, manage, and analyze A/B tests for data-driven optimization
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New A/B Test
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New A/B Test</DialogTitle>
              <DialogDescription>
                Set up a new A/B test to optimize your campaigns and workflows
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6">
              {/* Basic Configuration */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Basic Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="test-name">Test Name</Label>
                    <Input
                      id="test-name"
                      placeholder="Enter test name"
                      value={newTest.name}
                      onChange={(e) => setNewTest({ ...newTest, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Test Type</Label>
                    <Select 
                      value={newTest.test_type} 
                      onValueChange={(value) => setNewTest({ ...newTest, test_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {testTypes.map(type => {
                          const IconComponent = type.icon
                          return (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center gap-2">
                                <IconComponent className="w-4 h-4" />
                                {type.label}
                              </div>
                            </SelectItem>
                          )
                        })}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label htmlFor="test-description">Description</Label>
                  <Textarea
                    id="test-description"
                    placeholder="Describe what this test is trying to optimize"
                    value={newTest.description}
                    onChange={(e) => setNewTest({ ...newTest, description: e.target.value })}
                  />
                </div>
              </div>

              {/* Variants */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Variants</h3>
                  <Button onClick={addVariant} size="sm" variant="outline">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Variant
                  </Button>
                </div>
                <div className="space-y-3">
                  {newTest.variants.map((variant, index) => (
                    <Card key={index}>
                      <CardContent className="pt-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                          <div>
                            <Label>Variant Name</Label>
                            <Input
                              value={variant.name}
                              onChange={(e) => updateVariant(index, 'name', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label>Type</Label>
                            <Select 
                              value={variant.variant_type}
                              onValueChange={(value) => updateVariant(index, 'variant_type', value)}
                              disabled={variant.variant_type === 'control'}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="control">Control</SelectItem>
                                <SelectItem value="variant">Variant</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Traffic %</Label>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={variant.traffic_percentage}
                              onChange={(e) => updateVariant(index, 'traffic_percentage', parseInt(e.target.value) || 0)}
                            />
                          </div>
                          <div>
                            {newTest.variants.length > 2 && (
                              <Button 
                                onClick={() => removeVariant(index)} 
                                size="sm" 
                                variant="outline"
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                        <div className="mt-3">
                          <Label>Description</Label>
                          <Input
                            placeholder="Describe this variant"
                            value={variant.description}
                            onChange={(e) => updateVariant(index, 'description', e.target.value)}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <div className="text-sm text-muted-foreground">
                  Total traffic allocation: {newTest.variants.reduce((sum, v) => sum + v.traffic_percentage, 0)}%
                </div>
              </div>

              {/* Metrics */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Success Metrics</h3>
                  <Button onClick={addMetric} size="sm" variant="outline">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Metric
                  </Button>
                </div>
                <div className="space-y-3">
                  {newTest.metrics.map((metric, index) => (
                    <Card key={index}>
                      <CardContent className="pt-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                          <div>
                            <Label>Metric Type</Label>
                            <Select 
                              value={metric.metric_type}
                              onValueChange={(value) => updateMetric(index, 'metric_type', value)}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {metricTypes.map(type => (
                                  <SelectItem key={type.value} value={type.value}>
                                    {type.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Metric Name</Label>
                            <Input
                              value={metric.name}
                              onChange={(e) => updateMetric(index, 'name', e.target.value)}
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={metric.is_primary}
                                onChange={(e) => updateMetric(index, 'is_primary', e.target.checked)}
                                className="w-4 h-4"
                              />
                              <Label className="text-sm">Primary</Label>
                            </div>
                            {newTest.metrics.length > 1 && (
                              <Button 
                                onClick={() => removeMetric(index)} 
                                size="sm" 
                                variant="outline"
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Test Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Test Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Minimum Sample Size</Label>
                    <Input
                      type="number"
                      min="50"
                      value={newTest.min_sample_size}
                      onChange={(e) => setNewTest({ ...newTest, min_sample_size: parseInt(e.target.value) || 100 })}
                    />
                  </div>
                  <div>
                    <Label>Confidence Level</Label>
                    <Select 
                      value={newTest.confidence_level.toString()}
                      onValueChange={(value) => setNewTest({ ...newTest, confidence_level: parseFloat(value) })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.90">90%</SelectItem>
                        <SelectItem value="0.95">95%</SelectItem>
                        <SelectItem value="0.99">99%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => setShowCreateDialog(false)}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={createTest}
                  disabled={!newTest.name || newTest.variants.reduce((sum, v) => sum + v.traffic_percentage, 0) !== 100}
                >
                  <TestTube className="w-4 h-4 mr-2" />
                  Create Test
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-700">{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="active" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="active">Active Tests</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="analysis" disabled={!testAnalysis}>Analysis</TabsTrigger>
        </TabsList>

        {/* Active Tests Tab */}
        <TabsContent value="active" className="space-y-6">
          {activeTests.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <TestTube className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Tests</h3>
                  <p className="text-muted-foreground mb-4">
                    Start optimizing your campaigns by creating your first A/B test
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Your First Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {activeTests.map(test => {
                const IconComponent = getTestTypeIcon(test.test_type)
                return (
                  <Card key={test.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between text-lg">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-5 h-5" />
                          {test.name}
                        </div>
                        <Badge variant={getStatusBadgeVariant(test.status)}>
                          {test.status}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="text-sm text-muted-foreground">
                          {test.test_type.replace('_', ' ').toUpperCase()}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-muted-foreground">Variants</div>
                            <div className="font-semibold">{test.variants_count}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Metrics</div>
                            <div className="font-semibold">{test.metrics_count}</div>
                          </div>
                        </div>

                        {test.start_date && (
                          <div className="text-xs text-muted-foreground">
                            Started: {new Date(test.start_date).toLocaleDateString()}
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => fetchTestAnalysis(test.id)}
                          >
                            <BarChart3 className="w-4 h-4 mr-1" />
                            Analyze
                          </Button>
                          {test.status === 'draft' && (
                            <Button 
                              size="sm"
                              onClick={() => startTest(test.id)}
                            >
                              <Play className="w-4 h-4 mr-1" />
                              Start
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {testTemplates.map(template => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">{template.name}</CardTitle>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{template.test_type}</Badge>
                      <Badge variant="outline">{template.estimated_duration_days} days</Badge>
                    </div>
                    
                    <div className="text-sm space-y-2">
                      <div>
                        <span className="text-muted-foreground">Suggested Metrics: </span>
                        {template.suggested_metrics?.join(', ')}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Min Sample Size: </span>
                        {template.min_sample_size}
                      </div>
                    </div>

                    <Button 
                      className="w-full" 
                      size="sm"
                      onClick={() => {
                        // Pre-fill form with template data
                        setNewTest({
                          ...newTest,
                          name: template.name,
                          description: template.description,
                          test_type: template.test_type,
                          min_sample_size: template.min_sample_size,
                          metrics: template.suggested_metrics?.map(metric => ({
                            metric_type: metric,
                            name: metric.replace('_', ' ').toUpperCase(),
                            description: '',
                            is_primary: metric === template.suggested_metrics[0]
                          })) || newTest.metrics
                        })
                        setShowCreateDialog(true)
                      }}
                    >
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          {testAnalysis && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Test Analysis: {testAnalysis.test_name}
                  </CardTitle>
                  <CardDescription>
                    Statistical analysis and performance insights
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {testAnalysis.duration_days}
                      </div>
                      <div className="text-sm text-muted-foreground">Days Running</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {testAnalysis.total_participants}
                      </div>
                      <div className="text-sm text-muted-foreground">Participants</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {(testAnalysis.statistical_power * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Statistical Power</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {testAnalysis.winner ? '✓' : '?'}
                      </div>
                      <div className="text-sm text-muted-foreground">Winner Found</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Results by Variant */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {testAnalysis.results?.map((result, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between text-lg">
                        {result.variant_name}
                        {testAnalysis.winner === result.variant_id && (
                          <Badge className="bg-green-100 text-green-800">Winner</Badge>
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="text-center">
                          <div className="text-3xl font-bold">
                            {result.conversion_rate}%
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {result.metric_name}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Sample Size</span>
                            <span>{result.sample_size}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Conversions</span>
                            <span>{result.conversions}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Confidence Interval</span>
                            <span>{result.confidence_interval[0]}% - {result.confidence_interval[1]}%</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {result.statistical_significance ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <Clock className="w-4 h-4 text-yellow-500" />
                          )}
                          <span className="text-sm">
                            {result.statistical_significance ? 'Statistically Significant' : 'More Data Needed'}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Recommendations */}
              {testAnalysis.recommendations?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-orange-500" />
                      Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {testAnalysis.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                          <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-xs font-semibold text-blue-600">{index + 1}</span>
                          </div>
                          <div className="text-sm">{recommendation}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}