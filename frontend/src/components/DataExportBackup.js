import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
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
  Download, 
  Upload, 
  Archive, 
  FileText, 
  Database, 
  Shield, 
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  Trash2,
  FileDown,
  HardDrive,
  Zap,
  Settings,
  RefreshCw
} from 'lucide-react'

export function DataExportBackup() {
  const [exportJobs, setExportJobs] = useState([])
  const [backupJobs, setBackupJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [newExport, setNewExport] = useState({
    tenant_id: 'default-tenant',
    export_type: 'full',
    format: 'json',
    include_metadata: true,
    compress: true,
    date_range: null
  })
  const [newBackup, setNewBackup] = useState({
    tenant_id: 'default-tenant',
    backup_type: 'full',
    include_audit_logs: true,
    retention_days: 90
  })
  const [showExportModal, setShowExportModal] = useState(false)
  const [showBackupModal, setShowBackupModal] = useState(false)
  const [activeTab, setActiveTab] = useState('exports')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const exportTypes = [
    { value: 'full', label: 'Full Export', description: 'All data types' },
    { value: 'agents', label: 'Agents Only', description: 'AI agents and configurations' },
    { value: 'leads', label: 'Leads Only', description: 'CRM lead data' },
    { value: 'workflows', label: 'Workflows Only', description: 'Automation workflows' },
    { value: 'audit', label: 'Audit Logs', description: 'Security and compliance logs' }
  ]

  const formatTypes = [
    { value: 'json', label: 'JSON', description: 'Machine-readable format' },
    { value: 'csv', label: 'CSV', description: 'Spreadsheet compatible' },
    { value: 'excel', label: 'Excel', description: 'Microsoft Excel format' }
  ]

  const backupTypes = [
    { value: 'full', label: 'Full Backup', description: 'Complete data backup' },
    { value: 'incremental', label: 'Incremental', description: 'Recent changes only' }
  ]

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/data-export/jobs`)
      const data = await response.json()
      setExportJobs(data.export_jobs || [])
      setBackupJobs(data.backup_jobs || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
    }
  }

  const createExportJob = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/data-export/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newExport)
      })

      if (response.ok) {
        fetchJobs()
        setShowExportModal(false)
        setNewExport({
          tenant_id: 'default-tenant',
          export_type: 'full',
          format: 'json',
          include_metadata: true,
          compress: true,
          date_range: null
        })
        alert('Export job created successfully!')
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail || 'Failed to create export'}`)
      }
    } catch (error) {
      console.error('Error creating export:', error)
      alert('Failed to create export')
    } finally {
      setLoading(false)
    }
  }

  const createBackupJob = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/data-export/backup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBackup)
      })

      if (response.ok) {
        fetchJobs()
        setShowBackupModal(false)
        setNewBackup({
          tenant_id: 'default-tenant',
          backup_type: 'full',
          include_audit_logs: true,
          retention_days: 90
        })
        alert('Backup job created successfully!')
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail || 'Failed to create backup'}`)
      }
    } catch (error) {
      console.error('Error creating backup:', error)
      alert('Failed to create backup')
    } finally {
      setLoading(false)
    }
  }

  const downloadFile = async (jobId, type) => {
    try {
      const endpoint = type === 'export' 
        ? `/api/data-export/export/${jobId}/download`
        : `/api/data-export/backup/${jobId}/download`
      
      const response = await fetch(`${backendUrl}${endpoint}`)
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_${jobId}.${type === 'export' ? 'zip' : 'zip'}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Failed to download file')
      }
    } catch (error) {
      console.error('Error downloading file:', error)
      alert('Failed to download file')
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'processing':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      case 'processing': return 'bg-blue-500'
      default: return 'bg-yellow-500'
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Data Export & Backup</h2>
          <p className="text-muted-foreground">Enterprise-grade data export and automated backup systems</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Archive className="w-3 h-3" />
            {exportJobs.length} Exports
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <HardDrive className="w-3 h-3" />
            {backupJobs.length} Backups
          </Badge>
          
          <Dialog open={showExportModal} onOpenChange={setShowExportModal}>
            <DialogTrigger asChild>
              <Button>
                <Download className="w-4 h-4 mr-2" />
                New Export
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Data Export</DialogTitle>
                <DialogDescription>
                  Export your data for analysis, backup, or compliance purposes
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Export Type</Label>
                    <Select value={newExport.export_type} onValueChange={(value) => setNewExport({...newExport, export_type: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {exportTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Format</Label>
                    <Select value={newExport.format} onValueChange={(value) => setNewExport({...newExport, format: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {formatTypes.map((format) => (
                          <SelectItem key={format.value} value={format.value}>
                            {format.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="include-metadata"
                      checked={newExport.include_metadata}
                      onChange={(e) => setNewExport({...newExport, include_metadata: e.target.checked})}
                    />
                    <Label htmlFor="include-metadata">Include metadata and timestamps</Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="compress"
                      checked={newExport.compress}
                      onChange={(e) => setNewExport({...newExport, compress: e.target.checked})}
                    />
                    <Label htmlFor="compress">Compress export file</Label>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" onClick={() => setShowExportModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={createExportJob} disabled={loading}>
                    <Download className="w-4 h-4 mr-2" />
                    Create Export
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showBackupModal} onOpenChange={setShowBackupModal}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Archive className="w-4 h-4 mr-2" />
                New Backup
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Backup</DialogTitle>
                <DialogDescription>
                  Create secure backups for disaster recovery and compliance
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Backup Type</Label>
                    <Select value={newBackup.backup_type} onValueChange={(value) => setNewBackup({...newBackup, backup_type: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {backupTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Retention (days)</Label>
                    <Input
                      type="number"
                      value={newBackup.retention_days}
                      onChange={(e) => setNewBackup({...newBackup, retention_days: parseInt(e.target.value)})}
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="include-audit"
                    checked={newBackup.include_audit_logs}
                    onChange={(e) => setNewBackup({...newBackup, include_audit_logs: e.target.checked})}
                  />
                  <Label htmlFor="include-audit">Include audit logs for compliance</Label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" onClick={() => setShowBackupModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={createBackupJob} disabled={loading}>
                    <Archive className="w-4 h-4 mr-2" />
                    Create Backup
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="exports">Data Exports</TabsTrigger>
          <TabsTrigger value="backups">Backups</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        <TabsContent value="exports" className="space-y-4">
          <div className="space-y-4">
            {exportJobs.map((job) => (
              <Card key={job.export_id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <div className="font-medium">
                          Export #{job.export_id.slice(-8)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Created {formatDateTime(job.created_at)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <Badge className={`${getStatusColor(job.status)} text-white`}>
                          {job.status}
                        </Badge>
                        <div className="text-sm text-muted-foreground mt-1">
                          {job.file_size ? formatFileSize(job.file_size) : 'Calculating...'}
                        </div>
                      </div>
                      
                      {job.status === 'processing' && (
                        <div className="w-24">
                          <Progress value={job.progress} className="h-2" />
                          <div className="text-xs text-center mt-1">{job.progress}%</div>
                        </div>
                      )}
                      
                      {job.status === 'completed' && (
                        <Button 
                          size="sm"
                          onClick={() => downloadFile(job.export_id, 'export')}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      )}
                      
                      {job.status === 'failed' && (
                        <div className="text-sm text-red-600">
                          {job.error_message || 'Export failed'}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {exportJobs.length === 0 && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8">
                    <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Export Jobs</h3>
                    <p className="text-muted-foreground mb-4">
                      Create your first data export for analysis or backup
                    </p>
                    <Button onClick={() => setShowExportModal(true)}>
                      <Download className="w-4 h-4 mr-2" />
                      Create Export
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="backups" className="space-y-4">
          <div className="space-y-4">
            {backupJobs.map((job) => (
              <Card key={job.backup_id}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <div className="font-medium">
                          Backup #{job.backup_id.slice(-8)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Created {formatDateTime(job.created_at)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <Badge className={`${getStatusColor(job.status)} text-white`}>
                          {job.status}
                        </Badge>
                        <div className="text-sm text-muted-foreground mt-1">
                          {job.backup_size ? formatFileSize(job.backup_size) : 'Calculating...'}
                        </div>
                      </div>
                      
                      {job.status === 'processing' && (
                        <div className="w-24">
                          <Progress value={job.progress} className="h-2" />
                          <div className="text-xs text-center mt-1">{job.progress}%</div>
                        </div>
                      )}
                      
                      {job.status === 'completed' && (
                        <Button 
                          size="sm"
                          onClick={() => downloadFile(job.backup_id, 'backup')}
                        >
                          <FileDown className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      )}
                      
                      {job.status === 'failed' && (
                        <div className="text-sm text-red-600">
                          {job.error_message || 'Backup failed'}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {backupJobs.length === 0 && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8">
                    <HardDrive className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Backup Jobs</h3>
                    <p className="text-muted-foreground mb-4">
                      Create automated backups for disaster recovery
                    </p>
                    <Button onClick={() => setShowBackupModal(true)}>
                      <Archive className="w-4 h-4 mr-2" />
                      Create Backup
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Data Exports</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{exportJobs.length}</div>
                <p className="text-xs text-muted-foreground">Total exports created</p>
                <div className="mt-2">
                  <div className="text-sm">
                    Completed: {exportJobs.filter(j => j.status === 'completed').length}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Backup Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{backupJobs.length}</div>
                <p className="text-xs text-muted-foreground">Backup jobs created</p>
                <div className="mt-2">
                  <div className="text-sm">
                    Successful: {backupJobs.filter(j => j.status === 'completed').length}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Data Size</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatFileSize(
                    [...exportJobs, ...backupJobs]
                      .filter(j => j.status === 'completed')
                      .reduce((total, j) => total + (j.file_size || j.backup_size || 0), 0)
                  )}
                </div>
                <p className="text-xs text-muted-foreground">Total exported data</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Compliance Features
              </CardTitle>
              <CardDescription>
                Enterprise-grade data management and compliance tools
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-medium">Export Features</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Multiple format support (JSON, CSV, Excel)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Compressed archives for efficiency</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Metadata and audit trail inclusion</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Date range filtering</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <h4 className="font-medium">Backup & Recovery</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Automated backup scheduling</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Full and incremental backups</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Configurable retention policies</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Audit log preservation</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}