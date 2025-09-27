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
  Building2, 
  Users, 
  Bot, 
  Crown, 
  Shield, 
  Plus,
  Edit,
  Trash2,
  Eye,
  Settings,
  HardDrive,
  Calendar,
  Globe
} from 'lucide-react'

export function TenantManagement() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(false)
  const [newTenant, setNewTenant] = useState({
    name: '',
    subdomain: '',
    admin_email: '',
    admin_first_name: '',
    admin_last_name: '',
    plan_type: 'standard',
    max_users: 50,
    max_agents: 20
  })
  const [selectedTenant, setSelectedTenant] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const planTypes = [
    { value: 'trial', label: 'Trial', max_users: 5, max_agents: 3, color: 'bg-yellow-500' },
    { value: 'standard', label: 'Standard', max_users: 50, max_agents: 20, color: 'bg-blue-500' },
    { value: 'professional', label: 'Professional', max_users: 200, max_agents: 100, color: 'bg-purple-500' },
    { value: 'enterprise', label: 'Enterprise', max_users: 1000, max_agents: 500, color: 'bg-green-500' }
  ]

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/tenants/`)
      const data = await response.json()
      setTenants(data || [])
    } catch (error) {
      console.error('Error fetching tenants:', error)
    } finally {
      setLoading(false)
    }
  }

  const createTenant = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/tenants/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTenant)
      })

      if (response.ok) {
        fetchTenants()
        setShowCreateModal(false)
        setNewTenant({
          name: '',
          subdomain: '',
          admin_email: '',
          admin_first_name: '',
          admin_last_name: '',
          plan_type: 'standard',
          max_users: 50,
          max_agents: 20
        })
        alert('Tenant created successfully!')
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail || 'Failed to create tenant'}`)
      }
    } catch (error) {
      console.error('Error creating tenant:', error)
      alert('Failed to create tenant')
    } finally {
      setLoading(false)
    }
  }

  const updateTenantStatus = async (tenantId, status) => {
    try {
      const response = await fetch(`${backendUrl}/api/tenants/${tenantId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })

      if (response.ok) {
        fetchTenants()
        alert(`Tenant ${status} successfully!`)
      }
    } catch (error) {
      console.error('Error updating tenant:', error)
    }
  }

  const getPlanInfo = (planType) => {
    return planTypes.find(p => p.value === planType) || planTypes[1]
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'trial': return 'bg-yellow-500'
      case 'suspended': return 'bg-red-500'
      case 'expired': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Enterprise Tenant Management</h2>
          <p className="text-muted-foreground">Manage organizations, users, and subscriptions</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Building2 className="w-3 h-3" />
            {tenants.length} Tenants
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Crown className="w-3 h-3" />
            Super Admin
          </Badge>
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Tenant
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Tenant</DialogTitle>
                <DialogDescription>
                  Set up a new organization with admin user and subscription plan
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="tenantName">Organization Name</Label>
                    <Input
                      id="tenantName"
                      placeholder="Acme Corporation"
                      value={newTenant.name}
                      onChange={(e) => setNewTenant({...newTenant, name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subdomain">Subdomain</Label>
                    <Input
                      id="subdomain"
                      placeholder="acme"
                      value={newTenant.subdomain}
                      onChange={(e) => setNewTenant({...newTenant, subdomain: e.target.value})}
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="adminEmail">Admin Email</Label>
                  <Input
                    id="adminEmail"
                    type="email"
                    placeholder="admin@acme.com"
                    value={newTenant.admin_email}
                    onChange={(e) => setNewTenant({...newTenant, admin_email: e.target.value})}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">Admin First Name</Label>
                    <Input
                      id="firstName"
                      placeholder="John"
                      value={newTenant.admin_first_name}
                      onChange={(e) => setNewTenant({...newTenant, admin_first_name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Admin Last Name</Label>
                    <Input
                      id="lastName"
                      placeholder="Doe"
                      value={newTenant.admin_last_name}
                      onChange={(e) => setNewTenant({...newTenant, admin_last_name: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Subscription Plan</Label>
                    <Select value={newTenant.plan_type} onValueChange={(value) => {
                      const plan = getPlanInfo(value)
                      setNewTenant({
                        ...newTenant, 
                        plan_type: value,
                        max_users: plan.max_users,
                        max_agents: plan.max_agents
                      })
                    }}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {planTypes.map((plan) => (
                          <SelectItem key={plan.value} value={plan.value}>
                            {plan.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxUsers">Max Users</Label>
                    <Input
                      id="maxUsers"
                      type="number"
                      value={newTenant.max_users}
                      onChange={(e) => setNewTenant({...newTenant, max_users: parseInt(e.target.value)})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxAgents">Max Agents</Label>
                    <Input
                      id="maxAgents"
                      type="number"
                      value={newTenant.max_agents}
                      onChange={(e) => setNewTenant({...newTenant, max_agents: parseInt(e.target.value)})}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={createTenant} disabled={loading}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Tenant
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Tenant Details</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tenants.map((tenant) => {
              const plan = getPlanInfo(tenant.plan_type)
              return (
                <Card key={tenant.id} className="relative">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-5 h-5" />
                        <CardTitle className="text-lg">{tenant.name}</CardTitle>
                      </div>
                      <div className="flex items-center gap-1">
                        <Badge className={`${getStatusColor(tenant.status)} text-white`}>
                          {tenant.status}
                        </Badge>
                      </div>
                    </div>
                    <CardDescription>
                      {tenant.subdomain}.nexus-core.com
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Plan:</span>
                        <Badge className={`${plan.color} text-white`}>
                          {plan.label}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            <span>Users</span>
                          </div>
                          <div className="font-medium">
                            {tenant.current_users}/{tenant.max_users}
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <Bot className="w-3 h-3" />
                            <span>Agents</span>
                          </div>
                          <div className="font-medium">
                            {tenant.current_agents}/{tenant.max_agents}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span>Storage:</span>
                        <span>{Math.round(tenant.storage_used_mb || 0)} MB</span>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span>Created:</span>
                        <span>{new Date(tenant.created_at).toLocaleDateString()}</span>
                      </div>

                      <div className="flex gap-2 pt-2 border-t">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedTenant(tenant)}
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          View
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                        >
                          <Edit className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                        {tenant.status === 'active' ? (
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={() => updateTenantStatus(tenant.id, 'suspended')}
                          >
                            <Shield className="w-3 h-3 mr-1" />
                            Suspend
                          </Button>
                        ) : (
                          <Button 
                            variant="default" 
                            size="sm"
                            onClick={() => updateTenantStatus(tenant.id, 'active')}
                          >
                            <Shield className="w-3 h-3 mr-1" />
                            Activate
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {tenants.length === 0 && !loading && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Building2 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Tenants Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first tenant organization to get started
                  </p>
                  <Button onClick={() => setShowCreateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Tenant
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          {selectedTenant ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="w-5 h-5" />
                  {selectedTenant.name}
                </CardTitle>
                <CardDescription>Detailed tenant information and settings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Organization Details</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Name:</span>
                        <span>{selectedTenant.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Subdomain:</span>
                        <span>{selectedTenant.subdomain}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Admin Email:</span>
                        <span>{selectedTenant.admin_email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Status:</span>
                        <Badge className={`${getStatusColor(selectedTenant.status)} text-white`}>
                          {selectedTenant.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h4 className="font-medium">Subscription & Limits</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Plan:</span>
                        <Badge className={`${getPlanInfo(selectedTenant.plan_type).color} text-white`}>
                          {getPlanInfo(selectedTenant.plan_type).label}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Max Users:</span>
                        <span>{selectedTenant.max_users}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Max Agents:</span>
                        <span>{selectedTenant.max_agents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Created:</span>
                        <span>{new Date(selectedTenant.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Eye className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Select a Tenant</h3>
                  <p className="text-muted-foreground">
                    Choose a tenant from the overview to view detailed information
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Organizations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{tenants.length}</div>
                <p className="text-xs text-muted-foreground">Active tenants</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {tenants.reduce((sum, t) => sum + (t.current_users || 0), 0)}
                </div>
                <p className="text-xs text-muted-foreground">Across all tenants</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Agents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {tenants.reduce((sum, t) => sum + (t.current_agents || 0), 0)}
                </div>
                <p className="text-xs text-muted-foreground">AI agents deployed</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}