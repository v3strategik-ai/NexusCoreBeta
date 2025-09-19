import { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { ScrollArea } from './ui/scroll-area'
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Loader2,
  Sparkles
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

export function AgentChatModal({ agent, children }) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return

    const userMessage = currentMessage.trim()
    setCurrentMessage('')
    
    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      const response = await axios.post(`${API}/ai-chat/chat`, {
        agent_id: agent.id,
        message: userMessage,
        session_id: sessionId
      })

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        timestamp: new Date(),
        agent_name: response.data.agent_name
      }

      setMessages(prev => [...prev, aiMessage])
      
      // Set session ID for future messages
      if (!sessionId) {
        setSessionId(response.data.session_id)
      }

    } catch (error) {
      console.error('Error sending message:', error)
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getAutonomyColor = (level) => {
    switch(level) {
      case 'Quantum': return 'text-purple-400'
      case 'High': return 'text-green-400'
      case 'Medium': return 'text-yellow-400'
      default: return 'text-gray-400'
    }
  }

  const MessageBubble = ({ message }) => {
    const isUser = message.type === 'user'
    const isError = message.type === 'error'
    
    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex items-start space-x-2 max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-primary' 
              : isError 
                ? 'bg-red-500' 
                : 'bg-gradient-to-r from-blue-500 to-purple-500'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : isError ? (
              <span className="text-white text-xs">!</span>
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>
          
          <div className={`rounded-lg p-3 ${
            isUser 
              ? 'bg-primary text-primary-foreground' 
              : isError
                ? 'bg-red-100 text-red-800 border border-red-200'
                : 'bg-card border border-border quantum-bg'
          }`}>
            <div className="text-sm whitespace-pre-wrap">{message.content}</div>
            <div className="text-xs opacity-70 mt-1">
              {message.timestamp.toLocaleTimeString()}
              {message.agent_name && !isUser && (
                <span className="ml-2">• {message.agent_name}</span>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-2xl h-[600px] flex flex-col quantum-bg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className="relative">
              <Bot className="w-6 h-6 text-primary" />
              <Sparkles className="w-3 h-3 absolute -top-1 -right-1 text-yellow-400" />
            </div>
            <div>
              <span className="gradient-text">Chat with {agent.name}</span>
              <div className="text-sm text-muted-foreground font-normal mt-1">
                {agent.type} • {agent.specialization}
              </div>
            </div>
            <Badge 
              variant={agent.status === 'active' ? 'default' : 'secondary'} 
              className={`ml-auto ${getAutonomyColor(agent.autonomy_level)} quantum-pulse`}
            >
              {agent.autonomy_level} Autonomy
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Interact with your AI agent for specialized assistance in {agent.type.toLowerCase()}.
            Current efficiency: {agent.efficiency}% • Tasks completed: {agent.tasks_completed}
          </DialogDescription>
        </DialogHeader>

        {/* Chat Messages */}
        <div className="flex-1 flex flex-col min-h-0">
          <ScrollArea className="flex-1 p-4">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">Start a conversation</p>
                <p className="text-sm">
                  Ask {agent.name} about {agent.specialization.toLowerCase()} or any questions 
                  related to {agent.type.toLowerCase()}.
                </p>
              </div>
            ) : (
              <div>
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
                {isLoading && (
                  <div className="flex justify-start mb-4">
                    <div className="flex items-start space-x-2 max-w-[80%]">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="rounded-lg p-3 bg-card border border-border quantum-bg">
                        <div className="flex items-center space-x-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">
                            {agent.name} is thinking...
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </ScrollArea>

          {/* Message Input */}
          <div className="border-t border-border p-4">
            <div className="flex space-x-2">
              <Input
                placeholder={`Ask ${agent.name} anything about ${agent.type.toLowerCase()}...`}
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={sendMessage} 
                disabled={!currentMessage.trim() || isLoading}
                className="glow-effect"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Press Enter to send • {agent.autonomy_level} level AI assistant
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}