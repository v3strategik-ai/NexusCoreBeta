import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Checkbox } from './ui/checkbox'
import { Label } from './ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { 
  FileText, 
  Plus, 
  Trash2, 
  Play, 
  Download, 
  Filter,
  BarChart3,
  Users,
  Activity,
  Database,
  Calendar,
  Eye,
  Settings,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

export function ReportBuilder({ onReportGenerated = () => {} }) {
  const [reportConfig, setReportConfig] = useState({
    name: '',
    description: '',
    report_type: 'performance',
    data_sources: [],
    metrics: [],
    filters: [],
    time_range: 'last_30_days',
    grouping: '',
    sorting: {}
  })
  
  const [templates, setTemplates] = useState([])
  const [dataSources, setDataSources] = useState([])
  const [availableFields, setAvailableFields] = useState({})
  const [previewData, setPreviewData] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPreviewing, setIsPreviewing] = useState(false)
  const [error, setError] = useState(null)
  const [showPreview, setShowPreview] = useState(false)

  const reportTypes = [
    { value: 'performance', label: 'Performance Report', icon: BarChart3 },
    { value: 'revenue', label: 'Revenue Report', icon: '💰' },
    { value: 'conversion', label: 'Conversion Report', icon: '🎯' },
    { value: 'pipeline', label: 'Pipeline Report', icon: '🔄' },
    { value: 'agent_activity', label: 'Agent Activity Report', icon: Activity },
    { value: 'custom', label: 'Custom Report', icon: Settings }
  ]

  const timeRangeOptions = [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'last_7_days', label: 'Last 7 Days' },
    { value: 'last_30_days', label: 'Last 30 Days' },
    { value: 'last_90_days', label: 'Last 90 Days' },
    { value: 'last_year', label: 'Last Year' }
  ]

  const operators = [
    { value: 'eq', label: 'Equals' },
    { value: 'ne', label: 'Not Equals' },
    { value: 'gt', label: 'Greater Than' },
    { value: 'lt', label: 'Less Than' },
    { value: 'gte', label: 'Greater Than or Equal' },
    { value: 'lte', label: 'Less Than or Equal' },
    { value: 'in', label: 'In List' },
    { value: 'nin', label: 'Not In List' }
  ]

  useEffect(() => {
    fetchTemplatesAndDataSources()
  }, [])

  const fetchTemplatesAndDataSources = async () => {
    try {
      // Fetch report templates
      const templatesResponse = await fetch(`${BACKEND_URL}/api/analytics/reports/templates`)
      if (templatesResponse.ok) {
        const templatesData = await templatesResponse.json()
        setTemplates(templatesData.templates || [])
      }

      // Fetch available data sources
      const dataSourcesResponse = await fetch(`${BACKEND_URL}/api/analytics/reports/data-sources`)
      if (dataSourcesResponse.ok) {
        const dataSourcesData = await dataSourcesResponse.json()
        setDataSources(dataSourcesData.data_sources || [])
        
        // Build available fields mapping
        const fieldsMap = {}
        dataSourcesData.data_sources?.forEach(source => {
          fieldsMap[source.name] = source.available_fields || []
        })
        setAvailableFields(fieldsMap)
      }
    } catch (err) {
      console.error('Error fetching templates and data sources:', err)
      setError('Failed to load report builder data')
    }
  }

  const handleTemplateSelect = (template) => {
    setReportConfig({
      ...reportConfig,
      name: template.name,
      description: template.description,
      report_type: template.report_type,
      data_sources: template.data_sources || [],
      metrics: template.metrics || [],
      time_range: template.default_time_range || 'last_30_days'
    })
  }

  const handleDataSourceToggle = (sourceName) => {
    const newDataSources = reportConfig.data_sources.includes(sourceName)
      ? reportConfig.data_sources.filter(s => s !== sourceName)
      : [...reportConfig.data_sources, sourceName]
    
    setReportConfig({
      ...reportConfig,
      data_sources: newDataSources
    })
  }

  const handleMetricToggle = (metric) => {
    const newMetrics = reportConfig.metrics.includes(metric)
      ? reportConfig.metrics.filter(m => m !== metric)
      : [...reportConfig.metrics, metric]
    
    setReportConfig({
      ...reportConfig,
      metrics: newMetrics
    })
  }

  const addFilter = () => {
    setReportConfig({
      ...reportConfig,
      filters: [
        ...reportConfig.filters,
        { field: '', operator: 'eq', value: '' }
      ]
    })
  }

  const updateFilter = (index, field, value) => {
    const newFilters = [...reportConfig.filters]
    newFilters[index] = { ...newFilters[index], [field]: value }
    setReportConfig({
      ...reportConfig,
      filters: newFilters
    })
  }

  const removeFilter = (index) => {
    const newFilters = reportConfig.filters.filter((_, i) => i !== index)
    setReportConfig({
      ...reportConfig,
      filters: newFilters
    })
  }

  const handlePreview = async () => {
    if (!reportConfig.name || reportConfig.data_sources.length === 0) {
      setError('Please provide a report name and select at least one data source')
      return
    }

    try {
      setIsPreviewing(true)
      setError(null)

      const response = await fetch(`${BACKEND_URL}/api/analytics/reports/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reportConfig)
      })

      if (!response.ok) {
        throw new Error('Failed to generate report preview')
      }

      const previewResult = await response.json()
      setPreviewData(previewResult)
      setShowPreview(true)

    } catch (err) {
      console.error('Error generating preview:', err)
      setError(err.message)
    } finally {
      setIsPreviewing(false)
    }
  }

  const handleGenerate = async () => {
    if (!reportConfig.name || reportConfig.data_sources.length === 0) {
      setError('Please provide a report name and select at least one data source')
      return
    }

    try {
      setIsGenerating(true)
      setError(null)

      const response = await fetch(`${BACKEND_URL}/api/analytics/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reportConfig)
      })

      if (!response.ok) {
        throw new Error('Failed to generate report')
      }

      const reportResult = await response.json()
      onReportGenerated(reportResult)

    } catch (err) {
      console.error('Error generating report:', err)
      setError(err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  const getAvailableMetrics = () => {
    const allMetrics = new Set()
    reportConfig.data_sources.forEach(sourceName => {
      const fields = availableFields[sourceName] || []
      fields.forEach(field => {
        if (['value', 'score', 'revenue', 'cost', 'count'].some(metric => 
          field.toLowerCase().includes(metric)
        )) {
          allMetrics.add(field)
        }
      })
    })
    return Array.from(allMetrics)
  }

  const getAvailableFields = () => {
    const allFields = new Set()
    reportConfig.data_sources.forEach(sourceName => {
      const fields = availableFields[sourceName] || []
      fields.forEach(field => allFields.add(field))
    })
    return Array.from(allFields)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold gradient-text">Custom Report Builder</h2>
          <p className="text-muted-foreground">
            Create custom reports with advanced filtering and analytics
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handlePreview} 
            variant="outline"
            disabled={isPreviewing || !reportConfig.name || reportConfig.data_sources.length === 0}
          >
            {isPreviewing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Eye className="w-4 h-4 mr-2" />
            )}
            Preview
          </Button>
          <Button 
            onClick={handleGenerate}
            disabled={isGenerating || !reportConfig.name || reportConfig.data_sources.length === 0}
          >
            {isGenerating ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Play className="w-4 h-4 mr-2" />
            )}
            Generate Report
          </Button>
        </div>
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

      <Tabs defaultValue="config" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="preview" disabled={!previewData}>Preview</TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Basic Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Basic Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="report-name">Report Name</Label>
                  <Input
                    id="report-name"
                    placeholder="Enter report name"
                    value={reportConfig.name}
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      name: e.target.value
                    })}
                  />
                </div>
                
                <div>
                  <Label htmlFor="report-description">Description</Label>
                  <Textarea
                    id="report-description"
                    placeholder="Describe what this report analyzes"
                    value={reportConfig.description}
                    onChange={(e) => setReportConfig({
                      ...reportConfig,
                      description: e.target.value
                    })}
                  />
                </div>

                <div>
                  <Label>Report Type</Label>
                  <Select 
                    value={reportConfig.report_type} 
                    onValueChange={(value) => setReportConfig({
                      ...reportConfig,
                      report_type: value
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {reportTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Time Range</Label>
                  <Select 
                    value={reportConfig.time_range} 
                    onValueChange={(value) => setReportConfig({
                      ...reportConfig,
                      time_range: value
                    })}
                  >
                    <SelectTrigger>
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
                </div>
              </CardContent>
            </Card>

            {/* Data Sources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Data Sources
                </CardTitle>
                <CardDescription>
                  Select which data sources to include in your report
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dataSources.map(source => (
                    <div key={source.name} className="flex items-center space-x-2">
                      <Checkbox
                        id={source.name}
                        checked={reportConfig.data_sources.includes(source.name)}
                        onCheckedChange={() => handleDataSourceToggle(source.name)}
                      />
                      <Label htmlFor={source.name} className="flex-1 cursor-pointer">
                        <div className="font-medium">{source.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {source.description}
                        </div>
                      </Label>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Metrics Selection */}
          {reportConfig.data_sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Metrics & Fields
                </CardTitle>
                <CardDescription>
                  Choose which metrics and fields to include
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {getAvailableMetrics().map(metric => (
                    <div key={metric} className="flex items-center space-x-2">
                      <Checkbox
                        id={metric}
                        checked={reportConfig.metrics.includes(metric)}
                        onCheckedChange={() => handleMetricToggle(metric)}
                      />
                      <Label htmlFor={metric} className="text-sm cursor-pointer">
                        {metric}
                      </Label>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Filters
                </div>
                <Button onClick={addFilter} size="sm" variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Filter
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {reportConfig.filters.map((filter, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                    <Select 
                      value={filter.field} 
                      onValueChange={(value) => updateFilter(index, 'field', value)}
                    >
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Field" />
                      </SelectTrigger>
                      <SelectContent>
                        {getAvailableFields().map(field => (
                          <SelectItem key={field} value={field}>{field}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Select 
                      value={filter.operator} 
                      onValueChange={(value) => updateFilter(index, 'operator', value)}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {operators.map(op => (
                          <SelectItem key={op.value} value={op.value}>
                            {op.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Input
                      placeholder="Value"
                      value={filter.value}
                      onChange={(e) => updateFilter(index, 'value', e.target.value)}
                      className="flex-1"
                    />

                    <Button 
                      onClick={() => removeFilter(index)} 
                      size="sm" 
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
                {reportConfig.filters.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No filters added. Click "Add Filter" to include data filtering.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map(template => (
              <Card key={template.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">{template.name}</CardTitle>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{template.report_type}</Badge>
                      <Badge variant="outline">{template.default_time_range}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <div>Data Sources: {template.data_sources?.join(', ')}</div>
                      <div>Metrics: {template.metrics?.join(', ')}</div>
                    </div>
                    <Button 
                      onClick={() => handleTemplateSelect(template)}
                      className="w-full"
                      size="sm"
                    >
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-6">
          {previewData && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Report Preview
                  </CardTitle>
                  <CardDescription>
                    Showing {previewData.showing_records} of {previewData.total_records} records
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Summary */}
                    {previewData.summary && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-blue-50 rounded-lg">
                        <div className="text-center">
                          <div className="text-lg font-semibold">
                            {previewData.total_records}
                          </div>
                          <div className="text-sm text-muted-foreground">Total Records</div>
                        </div>
                        {Object.entries(previewData.summary.metrics || {}).map(([key, value]) => (
                          <div key={key} className="text-center">
                            <div className="text-lg font-semibold">
                              {typeof value === 'object' ? value.total || 0 : value}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {(key || '').replace('_', ' ').toUpperCase()}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Data Table */}
                    <div className="border rounded-lg overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              {previewData.preview_data[0] && Object.keys(previewData.preview_data[0]).map(key => (
                                <th key={key} className="px-4 py-2 text-left font-medium">
                                  {key.replace('_', ' ').toUpperCase()}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {previewData.preview_data.slice(0, 10).map((row, index) => (
                              <tr key={index} className="border-t">
                                {Object.values(row).map((value, cellIndex) => (
                                  <td key={cellIndex} className="px-4 py-2">
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {previewData.total_records > 10 && (
                      <div className="text-center text-sm text-muted-foreground">
                        ... and {previewData.total_records - 10} more records
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}