import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'
import { 
  Clock, 
  Calendar, 
  Play, 
  Pause, 
  Settings, 
  Repeat, 
  Zap,
  Plus,
  Trash2,
  CheckCircle,
  XCircle,
  Timer,
  CalendarDays
} from 'lucide-react'

export function TimeBasedTriggers() {
  const [triggers, setTriggers] = useState([])
  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [supportedSchedules, setSupportedSchedules] = useState([])
  const [loading, setLoading] = useState(false)
  const [newTrigger, setNewTrigger] = useState({
    name: '',
    description: '',
    schedule: '',
    timezone: 'UTC',
    enabled: true,
    workflow_template: 'notification'
  })
  const [activeTab, setActiveTab] = useState('triggers')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  // Predefined schedule templates
  const scheduleTemplates = [
    { label: 'Every Minute', value: '* * * * *', description: 'Runs every minute' },
    { label: 'Every Hour', value: '0 * * * *', description: 'Runs at the start of every hour' },
    { label: 'Daily at 9 AM', value: '0 9 * * *', description: 'Runs daily at 9:00 AM' },
    { label: 'Weekly on Monday', value: '0 9 * * 1', description: 'Runs Monday at 9:00 AM' },
    { label: 'Monthly (1st)', value: '0 9 1 * *', description: 'Runs on 1st of every month' },
    { label: 'Business Hours', value: '0 9-17 * * 1-5', description: 'Runs hourly during business hours' }
  ]

  const workflowTemplates = [
    { value: 'notification', label: 'Send Notification', description: 'Send a scheduled notification' },
    { value: 'lead_follow_up', label: 'Lead Follow-up', description: 'Automated lead follow-up process' },
    { value: 'agent_report', label: 'Agent Report', description: 'Generate performance reports' },
    { value: 'data_sync', label: 'Data Sync', description: 'Synchronize data with external systems' },
    { value: 'maintenance', label: 'System Maintenance', description: 'Scheduled system maintenance tasks' }
  ]

  useEffect(() => {
    fetchSchedulerStatus()
    fetchTriggers()
  }, [])

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/triggers/scheduler/status`)
      const data = await response.json()
      setSchedulerStatus(data)
      setSupportedSchedules(data.supported_schedules || [])
    } catch (error) {
      console.error('Error fetching scheduler status:', error)
    }
  }

  const fetchTriggers = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/triggers`)
      const data = await response.json()
      setTriggers(data.triggers || [])
    } catch (error) {
      console.error('Error fetching triggers:', error)
    }
  }

  const createTimeTrigger = async () => {
    if (!newTrigger.name || !newTrigger.schedule) return

    setLoading(true)
    try {
      const workflowData = {
        name: newTrigger.name,
        description: newTrigger.description || `Time-based workflow: ${newTrigger.name}`,
        status: "active",
        trigger: {
          type: "time_based",
          name: newTrigger.name,
          schedule: newTrigger.schedule,
          parameters: {
            timezone: newTrigger.timezone,
            enabled: newTrigger.enabled
          }
        },
        actions: [
          {
            type: newTrigger.workflow_template === 'notification' ? 'notification' : 'create_task',
            name: `${newTrigger.workflow_template} Action`,
            parameters: {
              message: `Scheduled ${newTrigger.workflow_template}: ${newTrigger.name}`,
              type: "scheduled",
              template: newTrigger.workflow_template
            }
          }
        ],
        created_by: "time_trigger_builder",
        category: "scheduled_automation"
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowData)
      })

      if (response.ok) {
        fetchTriggers()
        setNewTrigger({
          name: '',
          description: '',
          schedule: '',
          timezone: 'UTC',
          enabled: true,
          workflow_template: 'notification'
        })
        alert('Time-based trigger created successfully!')
      }
    } catch (error) {
      console.error('Error creating time trigger:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleScheduler = async () => {
    try {
      const endpoint = schedulerStatus?.running ? 'stop' : 'start'
      const response = await fetch(`${backendUrl}/api/workflow-engine/triggers/scheduler/${endpoint}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        fetchSchedulerStatus()
      }
    } catch (error) {
      console.error('Error toggling scheduler:', error)
    }
  }

  const validateCronExpression = (cron) => {
    const parts = cron.split(' ')
    return parts.length === 5 // Basic validation
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Time-Based Triggers</h2>
          <p className="text-muted-foreground">Schedule workflows with precise timing and recurring automation</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge 
            variant={schedulerStatus?.running ? 'default' : 'secondary'}
            className="flex items-center gap-1"
          >
            {schedulerStatus?.running ? (
              <Play className="w-3 h-3" />
            ) : (
              <Pause className="w-3 h-3" />
            )}
            Scheduler {schedulerStatus?.running ? 'Running' : 'Stopped'}
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Timer className="w-3 h-3" />
            {triggers.length} Active Triggers
          </Badge>
          <Button variant="outline" size="sm" onClick={toggleScheduler}>
            {schedulerStatus?.running ? 'Stop Scheduler' : 'Start Scheduler'}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="triggers">Active Triggers</TabsTrigger>
          <TabsTrigger value="create">Create Trigger</TabsTrigger>
          <TabsTrigger value="templates">Schedule Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="space-y-6">
          {/* Create New Time Trigger */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Create Time-Based Trigger
              </CardTitle>
              <CardDescription>
                Set up automated workflows that run on a schedule using cron expressions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="triggerName">Trigger Name</Label>
                  <Input
                    id="triggerName"
                    placeholder="Daily Lead Report"
                    value={newTrigger.name}
                    onChange={(e) => setNewTrigger({...newTrigger, name: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Workflow Template</Label>
                  <Select value={newTrigger.workflow_template} onValueChange={(value) => setNewTrigger({...newTrigger, workflow_template: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {workflowTemplates.map((template) => (
                        <SelectItem key={template.value} value={template.value}>
                          {template.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what this trigger will do..."
                  value={newTrigger.description}
                  onChange={(e) => setNewTrigger({...newTrigger, description: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="schedule">Cron Schedule</Label>
                  <Input
                    id="schedule"
                    placeholder="0 9 * * *"
                    value={newTrigger.schedule}
                    onChange={(e) => setNewTrigger({...newTrigger, schedule: e.target.value})}
                  />
                  <p className="text-xs text-muted-foreground">
                    Format: minute hour day month dayOfWeek
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Select value={newTrigger.timezone} onValueChange={(value) => setNewTrigger({...newTrigger, timezone: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Chicago">Central Time</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 className="font-medium">Schedule Validation</h4>
                  <p className="text-sm text-muted-foreground">
                    {newTrigger.schedule ? (
                      validateCronExpression(newTrigger.schedule) ? (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle className="w-4 h-4" />
                          Valid cron expression
                        </span>
                      ) : (
                        <span className="text-red-600 flex items-center gap-1">
                          <XCircle className="w-4 h-4" />
                          Invalid cron expression
                        </span>
                      )
                    ) : (
                      'Enter a cron expression to validate'
                    )}
                  </p>
                </div>
              </div>

              <Button 
                onClick={createTimeTrigger} 
                disabled={loading || !newTrigger.name || !newTrigger.schedule}
                className="w-full"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Time Trigger
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="triggers" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {triggers.map((trigger) => (
              <Card key={trigger.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{trigger.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant={trigger.enabled ? 'default' : 'secondary'}>
                        {trigger.enabled ? 'Active' : 'Paused'}
                      </Badge>
                      <Clock className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                  <CardDescription>{trigger.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Schedule:</span>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {trigger.trigger?.schedule || 'N/A'}
                      </code>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Type:</span>
                      <Badge variant="outline">{trigger.trigger?.type}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Executions:</span>
                      <Badge variant="outline">{trigger.execution_count || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Last Run:</span>
                      <span className="text-xs text-muted-foreground">
                        {trigger.last_executed ? new Date(trigger.last_executed).toLocaleDateString() : 'Never'}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {triggers.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Triggers</h3>
                  <p className="text-muted-foreground">
                    Create your first time-based trigger to automate workflows
                  </p>
                  <Button className="mt-4" onClick={() => setActiveTab('create')}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Trigger
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {scheduleTemplates.map((template, index) => (
              <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{template.label}</CardTitle>
                    <Repeat className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <code className="text-sm bg-muted px-2 py-1 rounded block">
                      {template.value}
                    </code>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => {
                        setNewTrigger({...newTrigger, schedule: template.value})
                        setActiveTab('create')
                      }}
                    >
                      Use This Schedule
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Cron Expression Guide</CardTitle>
              <CardDescription>Understanding the schedule format</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="grid grid-cols-5 gap-2 text-center text-sm">
                  <div className="font-medium">Minute</div>
                  <div className="font-medium">Hour</div>
                  <div className="font-medium">Day</div>
                  <div className="font-medium">Month</div>
                  <div className="font-medium">Day of Week</div>
                  <div>0-59</div>
                  <div>0-23</div>
                  <div>1-31</div>
                  <div>1-12</div>
                  <div>0-7 (0=Sun)</div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Use * for "any value", / for intervals, - for ranges, and , for lists
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}