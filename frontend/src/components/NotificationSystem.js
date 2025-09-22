import { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { 
  Bell, 
  BellRing, 
  X, 
  Check, 
  Info, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Mail,
  Users,
  FileText,
  Zap,
  Settings
} from 'lucide-react'
import { toast, ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

export function NotificationSystem({ 
  notifications = [], 
  onNotificationRead, 
  onNotificationDismiss,
  maxVisible = 5 
}) {
  const [visibleNotifications, setVisibleNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showPanel, setShowPanel] = useState(false)
  
  const audioRef = useRef(null)

  useEffect(() => {
    // Update visible notifications (most recent first)
    const sortedNotifications = [...notifications]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, maxVisible)
    
    setVisibleNotifications(sortedNotifications)
    
    // Count unread notifications
    const unread = notifications.filter(n => !n.read).length
    setUnreadCount(unread)
    
    // Play sound for new notifications (if enabled)
    if (unread > 0 && audioRef.current) {
      audioRef.current.play().catch(() => {
        // Audio play failed - user hasn't interacted with page yet
      })
    }
  }, [notifications, maxVisible])

  const getNotificationIcon = (type, category) => {
    if (category === 'email') return <Mail className="w-5 h-5" />
    if (category === 'lead') return <Users className="w-5 h-5" />
    if (category === 'document') return <FileText className="w-5 h-5" />
    if (category === 'workflow') return <Zap className="w-5 h-5" />
    if (category === 'agent') return <Settings className="w-5 h-5" />
    
    switch (type) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case 'error': return <XCircle className="w-5 h-5 text-red-400" />
      default: return <Info className="w-5 h-5 text-blue-400" />
    }
  }

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success': return 'border-green-400/50 bg-green-400/10'
      case 'warning': return 'border-yellow-400/50 bg-yellow-400/10'
      case 'error': return 'border-red-400/50 bg-red-400/10'
      default: return 'border-blue-400/50 bg-blue-400/10'
    }
  }

  const handleNotificationClick = (notification) => {
    if (!notification.read && onNotificationRead) {
      onNotificationRead(notification.id)
    }
  }

  const handleDismissNotification = (e, notificationId) => {
    e.stopPropagation()
    if (onNotificationDismiss) {
      onNotificationDismiss(notificationId)
    }
  }

  const markAllAsRead = () => {
    notifications
      .filter(n => !n.read)
      .forEach(n => {
        if (onNotificationRead) {
          onNotificationRead(n.id)
        }
      })
  }

  const dismissAll = () => {
    notifications.forEach(n => {
      if (onNotificationDismiss) {
        onNotificationDismiss(n.id)
      }
    })
    setShowPanel(false)
  }

  return (
    <>
      {/* Notification Bell Button */}
      <div className="relative">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setShowPanel(!showPanel)}
          className={`relative ${unreadCount > 0 ? 'text-primary border-primary/50' : ''}`}
        >
          {unreadCount > 0 ? (
            <BellRing className="w-5 h-5" />
          ) : (
            <Bell className="w-5 h-5" />
          )}
          {unreadCount > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-2 -right-2 px-1 min-w-[20px] h-5 text-xs"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>

        {/* Notification Panel */}
        {showPanel && (
          <Card className="absolute right-0 top-full mt-2 w-96 max-h-96 z-50 quantum-bg border-primary/20 shadow-2xl">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Notifications</CardTitle>
                <div className="flex gap-2">
                  {unreadCount > 0 && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={markAllAsRead}
                      className="text-xs h-7"
                    >
                      <Check className="w-3 h-3 mr-1" />
                      Mark all read
                    </Button>
                  )}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={dismissAll}
                    className="text-xs h-7"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Clear all
                  </Button>
                </div>
              </div>
              {unreadCount > 0 && (
                <CardDescription>
                  {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent className="p-0">
              <div className="max-h-64 overflow-y-auto">
                {visibleNotifications.length > 0 ? (
                  <div className="space-y-1">
                    {visibleNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-3 cursor-pointer hover:bg-accent/50 transition-colors border-l-4 ${getNotificationColor(notification.type)} ${
                          !notification.read ? 'bg-accent/20' : ''
                        }`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 mt-0.5">
                            {getNotificationIcon(notification.type, notification.category)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1">
                                <h4 className={`text-sm font-medium ${!notification.read ? 'font-semibold' : ''}`}>
                                  {notification.title}
                                </h4>
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {notification.message}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="text-xs text-muted-foreground">
                                    {new Date(notification.timestamp).toLocaleTimeString()}
                                  </span>
                                  {notification.category && (
                                    <Badge variant="outline" className="text-xs px-1 py-0">
                                      {notification.category}
                                    </Badge>
                                  )}
                                  {!notification.read && (
                                    <div className="w-2 h-2 bg-primary rounded-full" />
                                  )}
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="p-1 h-6 w-6 opacity-60 hover:opacity-100"
                                onClick={(e) => handleDismissNotification(e, notification.id)}
                              >
                                <X className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>No notifications</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Toast Container for real-time notifications */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
        toastClassName="quantum-bg border border-primary/20"
        className="toast-container"
      />

      {/* Audio element for notification sounds */}
      <audio
        ref={audioRef}
        preload="auto"
        style={{ display: 'none' }}
      >
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwfCTGH0fPTgjMGHm7A7+OZURE=" type="audio/wav" />
      </audio>

      {/* Click outside to close panel */}
      {showPanel && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowPanel(false)}
          style={{ backgroundColor: 'transparent' }}
        />
      )}
    </>
  )
}

// Custom toast notification functions
export const showNotification = {
  success: (title, message, options = {}) => {
    toast.success(
      <div>
        <div className="font-semibold">{title}</div>
        <div className="text-sm opacity-90">{message}</div>
      </div>,
      {
        icon: <CheckCircle className="w-5 h-5" />,
        ...options
      }
    )
  },
  
  error: (title, message, options = {}) => {
    toast.error(
      <div>
        <div className="font-semibold">{title}</div>
        <div className="text-sm opacity-90">{message}</div>
      </div>,
      {
        icon: <XCircle className="w-5 h-5" />,
        ...options
      }
    )
  },
  
  warning: (title, message, options = {}) => {
    toast.warning(
      <div>
        <div className="font-semibold">{title}</div>
        <div className="text-sm opacity-90">{message}</div>
      </div>,
      {
        icon: <AlertTriangle className="w-5 h-5" />,
        ...options
      }
    )
  },
  
  info: (title, message, options = {}) => {
    toast.info(
      <div>
        <div className="font-semibold">{title}</div>
        <div className="text-sm opacity-90">{message}</div>
      </div>,
      {
        icon: <Info className="w-5 h-5" />,
        ...options
      }
    )
  }
}

// Hook for managing notifications state
export function useNotifications() {
  const [notifications, setNotifications] = useState([])

  const addNotification = (notification) => {
    const newNotification = {
      id: `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      read: false,
      ...notification
    }
    
    setNotifications(prev => [newNotification, ...prev])
    
    // Auto-show toast for important notifications
    if (notification.showToast !== false) {
      const toastFunc = showNotification[notification.type] || showNotification.info
      toastFunc(notification.title, notification.message)
    }
    
    return newNotification.id
  }

  const markAsRead = (notificationId) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    )
  }

  const dismissNotification = (notificationId) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId))
  }

  const clearAll = () => {
    setNotifications([])
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  return {
    notifications,
    addNotification,
    markAsRead,
    dismissNotification,
    clearAll,
    markAllAsRead,
    unreadCount: notifications.filter(n => !n.read).length
  }
}