import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
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
  Users, 
  UserPlus, 
  Shield, 
  Crown, 
  Settings, 
  Eye,
  Edit,
  Lock,
  Trash2,
  Calendar,
  Mail,
  Phone,
  CheckCircle,
  XCircle,
  Activity
} from 'lucide-react'

export function UserManagement() {
  const [users, setUsers] = useState([])
  const [tenants, setTenants] = useState([])
  const [selectedTenant, setSelectedTenant] = useState('')
  const [loading, setLoading] = useState(false)
  const [newUser, setNewUser] = useState({
    tenant_id: '',
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    password: '',
    role: 'employee',
    phone: ''
  })
  const [selectedUser, setSelectedUser] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState('users')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const userRoles = [
    { value: 'super_admin', label: 'Super Admin', color: 'bg-red-500', icon: Crown },
    { value: 'tenant_admin', label: 'Tenant Admin', color: 'bg-purple-500', icon: Shield },
    { value: 'manager', label: 'Manager', color: 'bg-blue-500', icon: Users },
    { value: 'employee', label: 'Employee', color: 'bg-green-500', icon: Users }
  ]

  useEffect(() => {
    fetchTenants()
  }, [])

  useEffect(() => {
    if (selectedTenant) {
      fetchUsers(selectedTenant)
    }
  }, [selectedTenant])

  const fetchTenants = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/tenants/`)
      const data = await response.json()
      setTenants(data || [])
      if (data.length > 0) {
        setSelectedTenant(data[0].id)
      }
    } catch (error) {
      console.error('Error fetching tenants:', error)
    }
  }

  const fetchUsers = async (tenantId) => {
    try {
      setLoading(true)
      const response = await fetch(`${backendUrl}/api/users/tenant/${tenantId}`)
      const data = await response.json()
      setUsers(data || [])
    } catch (error) {
      console.error('Error fetching users:', error)
    } finally {
      setLoading(false)
    }
  }

  const createUser = async () => {
    try {
      setLoading(true)
      const userData = { ...newUser, tenant_id: selectedTenant }
      const response = await fetch(`${backendUrl}/api/users/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      })

      if (response.ok) {
        fetchUsers(selectedTenant)
        setShowCreateModal(false)
        setNewUser({
          tenant_id: '',
          email: '',
          username: '',
          first_name: '',
          last_name: '',
          password: '',
          role: 'employee',
          phone: ''
        })
        alert('User created successfully!')
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail || 'Failed to create user'}`)
      }
    } catch (error) {
      console.error('Error creating user:', error)
      alert('Failed to create user')
    } finally {
      setLoading(false)
    }
  }

  const updateUserStatus = async (userId, is_active) => {
    try {
      const response = await fetch(`${backendUrl}/api/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active })
      })

      if (response.ok) {
        fetchUsers(selectedTenant)
        alert(`User ${is_active ? 'activated' : 'deactivated'} successfully!`)
      }
    } catch (error) {
      console.error('Error updating user:', error)
    }
  }

  const getRoleInfo = (role) => {
    return userRoles.find(r => r.value === role) || userRoles[3]
  }

  const getStatusColor = (is_active, is_verified) => {
    if (!is_active) return 'bg-red-500'
    if (!is_verified) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getStatusText = (is_active, is_verified) => {
    if (!is_active) return 'Inactive'
    if (!is_verified) return 'Unverified'
    return 'Active'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">User Management</h2>
          <p className="text-muted-foreground">Manage users, roles, and permissions across tenants</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedTenant} onValueChange={setSelectedTenant}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select tenant" />
            </SelectTrigger>
            <SelectContent>
              {tenants.map((tenant) => (
                <SelectItem key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Badge variant="outline" className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {users.length} Users
          </Badge>
          
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button disabled={!selectedTenant}>
                <UserPlus className="w-4 h-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                  Add a new user to the selected tenant organization
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      value={newUser.first_name}
                      onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      value={newUser.last_name}
                      onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      value={newUser.username}
                      onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone (Optional)</Label>
                    <Input
                      id="phone"
                      value={newUser.phone}
                      onChange={(e) => setNewUser({...newUser, phone: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select value={newUser.role} onValueChange={(value) => setNewUser({...newUser, role: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {userRoles.map((role) => (
                          <SelectItem key={role.value} value={role.value}>
                            {role.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </Button>
                  <Button onClick={createUser} disabled={loading}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Create User
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="roles">Roles & Permissions</TabsTrigger>
          <TabsTrigger value="activity">User Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {users.map((user) => {
              const role = getRoleInfo(user.role)
              const RoleIcon = role.icon
              return (
                <Card key={user.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                          {user.first_name[0]}{user.last_name[0]}
                        </div>
                        <div>
                          <CardTitle className="text-base">
                            {user.first_name} {user.last_name}
                          </CardTitle>
                          <CardDescription className="text-sm">
                            @{user.username}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge className={`${getStatusColor(user.is_active, user.is_verified)} text-white`}>
                        {getStatusText(user.is_active, user.is_verified)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Role:</span>
                        <Badge className={`${role.color} text-white flex items-center gap-1`}>
                          <RoleIcon className="w-3 h-3" />
                          {role.label}
                        </Badge>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Mail className="w-3 h-3 text-muted-foreground" />
                          <span>{user.email}</span>
                        </div>
                        {user.phone && (
                          <div className="flex items-center gap-2">
                            <Phone className="w-3 h-3 text-muted-foreground" />
                            <span>{user.phone}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <Calendar className="w-3 h-3 text-muted-foreground" />
                          <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
                        </div>
                        {user.last_login && (
                          <div className="flex items-center gap-2">
                            <Activity className="w-3 h-3 text-muted-foreground" />
                            <span>Last login {new Date(user.last_login).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span>Login Count:</span>
                        <Badge variant="outline">{user.login_count || 0}</Badge>
                      </div>

                      <div className="flex gap-2 pt-2 border-t">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setSelectedUser(user)}
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
                        {user.is_active ? (
                          <Button 
                            variant="destructive" 
                            size="sm"
                            onClick={() => updateUserStatus(user.id, false)}
                          >
                            <XCircle className="w-3 h-3 mr-1" />
                            Deactivate
                          </Button>
                        ) : (
                          <Button 
                            variant="default" 
                            size="sm"
                            onClick={() => updateUserStatus(user.id, true)}
                          >
                            <CheckCircle className="w-3 h-3 mr-1" />
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

          {users.length === 0 && !loading && selectedTenant && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Users Found</h3>
                  <p className="text-muted-foreground mb-4">
                    Add users to this tenant organization to get started
                  </p>
                  <Button onClick={() => setShowCreateModal(true)}>
                    <UserPlus className="w-4 h-4 mr-2" />
                    Add First User
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="roles" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {userRoles.map((role) => {
              const RoleIcon = role.icon
              const roleUsers = users.filter(u => u.role === role.value)
              return (
                <Card key={role.value}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <RoleIcon className="w-5 h-5" />
                      {role.label}
                    </CardTitle>
                    <CardDescription>
                      {roleUsers.length} user{roleUsers.length !== 1 ? 's' : ''} with this role
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="text-sm">
                        <div className="font-medium mb-2">Permissions:</div>
                        <div className="space-y-1 text-muted-foreground">
                          {role.value === 'super_admin' && (
                            <>
                              <div>• Full system administration</div>
                              <div>• Manage all tenants and users</div>
                              <div>• System configuration</div>
                            </>
                          )}
                          {role.value === 'tenant_admin' && (
                            <>
                              <div>• Manage tenant users and settings</div>
                              <div>• Full access to tenant data</div>
                              <div>• Configure workflows and automation</div>
                            </>
                          )}
                          {role.value === 'manager' && (
                            <>
                              <div>• Manage team members</div>
                              <div>• Access analytics and reports</div>
                              <div>• Configure agents and workflows</div>
                            </>
                          )}
                          {role.value === 'employee' && (
                            <>
                              <div>• Use agents and workflows</div>
                              <div>• Manage leads and tasks</div>
                              <div>• View basic analytics</div>
                            </>
                          )}
                        </div>
                      </div>
                      
                      {roleUsers.length > 0 && (
                        <div className="text-sm">
                          <div className="font-medium mb-2">Users with this role:</div>
                          <div className="space-y-1">
                            {roleUsers.slice(0, 3).map(user => (
                              <div key={user.id} className="text-muted-foreground">
                                {user.first_name} {user.last_name}
                              </div>
                            ))}
                            {roleUsers.length > 3 && (
                              <div className="text-muted-foreground">
                                +{roleUsers.length - 3} more
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{users.length}</div>
                <p className="text-xs text-muted-foreground">In selected tenant</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Active Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {users.filter(u => u.is_active).length}
                </div>
                <p className="text-xs text-muted-foreground">Currently active</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Logins</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {users.filter(u => u.last_login && new Date(u.last_login) > new Date(Date.now() - 7*24*60*60*1000)).length}
                </div>
                <p className="text-xs text-muted-foreground">Last 7 days</p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Total Logins</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {users.reduce((sum, u) => sum + (u.login_count || 0), 0)}
                </div>
                <p className="text-xs text-muted-foreground">All time</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}