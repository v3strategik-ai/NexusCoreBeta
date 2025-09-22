import { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Settings,
  MessageSquare,
  Users,
  BarChart3,
  FileText,
  Workflow,
  Mail
} from 'lucide-react'

export function VoiceCommands({ onCommand = () => {} }) {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [confidence, setConfidence] = useState(0)
  const [lastCommand, setLastCommand] = useState(null)
  const [error, setError] = useState(null)
  
  const recognitionRef = useRef(null)
  const synthRef = useRef(null)
  
  // Voice command patterns
  const commandPatterns = [
    { pattern: /show (me )?leads?/i, action: 'navigate', target: 'leads', description: 'Show leads page' },
    { pattern: /show (me )?agents?/i, action: 'navigate', target: 'agents', description: 'Show digital employees' },
    { pattern: /show (me )?analytics?/i, action: 'navigate', target: 'analytics', description: 'Show analytics dashboard' },
    { pattern: /show (me )?documents?/i, action: 'navigate', target: 'documents', description: 'Show documents' },
    { pattern: /show (me )?workflows?/i, action: 'navigate', target: 'workflows', description: 'Show workflows' },
    { pattern: /show (me )?integrations?/i, action: 'navigate', target: 'integrations', description: 'Show integrations' },
    
    { pattern: /create (a )?new lead/i, action: 'create', target: 'lead', description: 'Open new lead form' },
    { pattern: /create (a )?new agent/i, action: 'create', target: 'agent', description: 'Open new agent form' },
    { pattern: /create (a )?new document/i, action: 'create', target: 'document', description: 'Open document generator' },
    
    { pattern: /search (for )?(.+)/i, action: 'search', target: 'general', description: 'Search across platform' },
    { pattern: /find lead (.+)/i, action: 'search', target: 'leads', description: 'Search for specific lead' },
    { pattern: /find agent (.+)/i, action: 'search', target: 'agents', description: 'Search for specific agent' },
    
    { pattern: /(hi|hello|hey)/i, action: 'greeting', target: 'none', description: 'Voice assistant greeting' },
    { pattern: /(help|what can you do)/i, action: 'help', target: 'none', description: 'Show available commands' },
    { pattern: /(thank you|thanks)/i, action: 'thanks', target: 'none', description: 'Acknowledgment' },
    { pattern: /(stop|cancel|nevermind)/i, action: 'cancel', target: 'none', description: 'Cancel current action' }
  ]

  useEffect(() => {
    // Check if speech recognition is supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsSupported(true)
      
      // Initialize speech recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'
      
      recognitionRef.current.onstart = () => {
        setIsListening(true)
        setError(null)
        setTranscript('')
      }
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          const confidence = event.results[i][0].confidence
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript
            setConfidence(confidence || 1)
          } else {
            interimTranscript += transcript
          }
        }
        
        setTranscript(finalTranscript || interimTranscript)
        
        if (finalTranscript) {
          processCommand(finalTranscript.trim())
        }
      }
      
      recognitionRef.current.onerror = (event) => {
        setError(`Speech recognition error: ${event.error}`)
        setIsListening(false)
      }
      
      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
    
    // Initialize speech synthesis
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [])
  
  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start()
      } catch (err) {
        setError('Failed to start voice recognition')
      }
    }
  }
  
  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
    }
  }
  
  const speak = (text) => {
    if (synthRef.current && text) {
      // Cancel any ongoing speech
      synthRef.current.cancel()
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.9
      utterance.pitch = 1
      utterance.volume = 0.8
      
      synthRef.current.speak(utterance)
    }
  }
  
  const processCommand = (transcript) => {
    const lowerTranscript = transcript.toLowerCase()
    
    // Find matching command pattern
    for (const command of commandPatterns) {
      const match = lowerTranscript.match(command.pattern)
      if (match) {
        const commandData = {
          transcript,
          action: command.action,
          target: command.target,
          match: match,
          timestamp: new Date()
        }
        
        setLastCommand(commandData)
        executeCommand(commandData)
        return
      }
    }
    
    // No matching pattern found
    setLastCommand({
      transcript,
      action: 'unknown',
      target: 'none',
      timestamp: new Date()
    })
    
    speak("I didn't understand that command. Try saying 'help' to see what I can do.")
  }
  
  const executeCommand = (command) => {
    switch (command.action) {
      case 'navigate':
        handleNavigation(command.target)
        speak(`Showing ${command.target} page`)
        break
        
      case 'create':
        handleCreate(command.target)
        speak(`Opening ${command.target} creation form`)
        break
        
      case 'search':
        handleSearch(command.target, command.match)
        speak(`Searching for ${command.target}`)
        break
        
      case 'greeting':
        speak("Hello! I'm your voice assistant. I can help you navigate the platform, create new items, and search for information. What would you like to do?")
        break
        
      case 'help':
        speak("I can help you navigate to different pages, create new leads or agents, search for information, and more. Try saying 'show leads', 'create new agent', or 'search for John'.")
        break
        
      case 'thanks':
        speak("You're welcome! Let me know if you need anything else.")
        break
        
      case 'cancel':
        speak("Okay, canceled.")
        break
        
      default:
        speak("I'm not sure how to handle that command yet.")
    }
    
    // Notify parent component
    onCommand(command)
  }
  
  const handleNavigation = (target) => {
    // This would integrate with your app's navigation system
    const targetMap = {
      'leads': 'crm',
      'agents': 'agents',
      'analytics': 'analytics',
      'documents': 'documents',
      'workflows': 'workflows',
      'integrations': 'integrations'
    }
    
    const tabValue = targetMap[target]
    if (tabValue) {
      // Trigger tab change - this would need to be connected to your app's tab system
      const event = new CustomEvent('voiceNavigate', { detail: { tab: tabValue } })
      window.dispatchEvent(event)
    }
  }
  
  const handleCreate = (target) => {
    // Trigger creation modals
    const event = new CustomEvent('voiceCreate', { detail: { type: target } })
    window.dispatchEvent(event)
  }
  
  const handleSearch = (target, match) => {
    const searchTerm = match[2] || match[1] || ''
    const event = new CustomEvent('voiceSearch', { 
      detail: { target, query: searchTerm.trim() } 
    })
    window.dispatchEvent(event)
  }
  
  if (!isSupported) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center">
            <MicOff className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Voice commands not supported in this browser
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <div className="space-y-4">
      {/* Voice Control Button */}
      <div className="flex items-center gap-3">
        <Button
          onClick={isListening ? stopListening : startListening}
          variant={isListening ? "default" : "outline"}
          size="sm"
          className={`transition-all ${isListening ? 'bg-red-500 hover:bg-red-600 animate-pulse' : ''}`}
        >
          {isListening ? (
            <>
              <MicOff className="w-4 h-4 mr-2" />
              Stop
            </>
          ) : (
            <>
              <Mic className="w-4 h-4 mr-2" />
              Voice
            </>
          )}
        </Button>
        
        {isListening && (
          <Badge variant="secondary" className="animate-pulse">
            Listening...
          </Badge>
        )}
        
        {transcript && (
          <div className="flex-1 text-sm text-muted-foreground">
            "{transcript}"
          </div>
        )}
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}
      
      {/* Last Command */}
      {lastCommand && (
        <Card className="max-w-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Last Command
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Said:</span> "{lastCommand.transcript}"
              </div>
              <div>
                <span className="font-medium">Action:</span> {lastCommand.action}
              </div>
              {lastCommand.target !== 'none' && (
                <div>
                  <span className="font-medium">Target:</span> {lastCommand.target}
                </div>
              )}
              {confidence > 0 && (
                <div>
                  <span className="font-medium">Confidence:</span> {(confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export function VoiceCommandsHelp() {
  const [showHelp, setShowHelp] = useState(false)
  
  const exampleCommands = [
    { command: "Show leads", description: "Navigate to CRM leads page", icon: Users },
    { command: "Show agents", description: "View digital employees", icon: Users },
    { command: "Show analytics", description: "Open analytics dashboard", icon: BarChart3 },
    { command: "Create new lead", description: "Open lead creation form", icon: Users },
    { command: "Create new agent", description: "Start agent setup", icon: Users },
    { command: "Search for John", description: "Search across platform", icon: MessageSquare },
    { command: "Help", description: "Show available commands", icon: MessageSquare }
  ]
  
  return (
    <div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowHelp(!showHelp)}
        className="text-muted-foreground"
      >
        <Volume2 className="w-4 h-4 mr-2" />
        Voice Help
      </Button>
      
      {showHelp && (
        <Card className="mt-2 w-80">
          <CardHeader>
            <CardTitle className="text-base">Voice Commands</CardTitle>
            <CardDescription>
              Click the voice button and try these commands
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {exampleCommands.map((cmd, index) => {
                const IconComponent = cmd.icon
                return (
                  <div key={index} className="flex items-start gap-3">
                    <IconComponent className="w-4 h-4 mt-0.5 text-muted-foreground" />
                    <div className="flex-1">
                      <div className="font-medium text-sm">"{cmd.command}"</div>
                      <div className="text-xs text-muted-foreground">{cmd.description}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}