import { useState, useEffect, useRef } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  Phone, 
  PhoneOff, 
  Settings, 
  Bot,
  MessageSquare,
  Zap,
  Headphones,
  Radio,
  PlayCircle,
  PauseCircle,
  RotateCcw,
  Send
} from 'lucide-react'

// Realtime Audio Chat Class
class RealtimeAudioChat {
  constructor() {
    this.peerConnection = null;
    this.dataChannel = null;
    this.audioElement = null;
    this.isConnected = false;
    this.onStatusChange = null;
    this.onMessage = null;
  }

  async init(apiPrefix = '/api') {
    try {
      console.log('Initializing realtime audio chat...');
      
      // Get session from backend
      const tokenResponse = await fetch(`${apiPrefix}/advanced-voice/realtime/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        }
      });
      
      if (!tokenResponse.ok) {
        throw new Error(`Failed to get session token: ${tokenResponse.status}`);
      }
      
      const data = await tokenResponse.json();
      if (!data.client_secret?.value) {
        throw new Error("Failed to get session token");
      }

      // Create and set up WebRTC peer connection
      this.peerConnection = new RTCPeerConnection();
      this.setupAudioElement();
      await this.setupLocalAudio();
      this.setupDataChannel();

      // Create and send offer
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);

      // Send offer to backend and get answer
      const response = await fetch(`${apiPrefix}/advanced-voice/realtime/negotiate`, {
        method: "POST",
        body: offer.sdp,
        headers: {
          "Content-Type": "application/sdp"
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to negotiate connection: ${response.status}`);
      }

      const { sdp: answerSdp } = await response.json();
      const answer = {
        type: "answer",
        sdp: answerSdp
      };

      await this.peerConnection.setRemoteDescription(answer);
      this.isConnected = true;
      
      if (this.onStatusChange) {
        this.onStatusChange('connected');
      }
      
      console.log("WebRTC connection established");
      return true;
      
    } catch (error) {
      console.error("Failed to initialize audio chat:", error);
      this.isConnected = false;
      
      if (this.onStatusChange) {
        this.onStatusChange('error', error.message);
      }
      
      return false;
    }
  }

  setupAudioElement() {
    this.audioElement = document.createElement("audio");
    this.audioElement.autoplay = true;
    this.audioElement.style.display = 'none';
    document.body.appendChild(this.audioElement);

    this.peerConnection.ontrack = (event) => {
      console.log('Received audio track');
      this.audioElement.srcObject = event.streams[0];
    };
  }

  async setupLocalAudio() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, stream);
      });
      console.log('Local audio stream added');
    } catch (error) {
      console.error('Failed to get user media:', error);
      throw error;
    }
  }

  setupDataChannel() {
    this.dataChannel = this.peerConnection.createDataChannel("oai-events");
    
    this.dataChannel.onopen = () => {
      console.log('Data channel opened');
    };
    
    this.dataChannel.onmessage = (event) => {
      console.log("Received event:", event.data);
      if (this.onMessage) {
        try {
          const message = JSON.parse(event.data);
          this.onMessage(message);
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      }
    };
  }

  disconnect() {
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    
    if (this.audioElement) {
      document.body.removeChild(this.audioElement);
      this.audioElement = null;
    }
    
    this.isConnected = false;
    
    if (this.onStatusChange) {
      this.onStatusChange('disconnected');
    }
  }

  sendEvent(event) {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(event));
    }
  }
}

export function AdvancedVoiceInterface() {
  const [isListening, setIsListening] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [audioLevel, setAudioLevel] = useState(0)
  const [conversation, setConversation] = useState([])
  const [availableCommands, setAvailableCommands] = useState({})
  const [voiceStats, setVoiceStats] = useState(null)
  const [activeSession, setActiveSession] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const audioChat = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const animationRef = useRef(null)

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  useEffect(() => {
    fetchAvailableCommands()
    fetchVoiceStats()
    
    return () => {
      if (audioChat.current) {
        audioChat.current.disconnect()
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

  const fetchAvailableCommands = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/advanced-voice/commands/available`)
      const data = await response.json()
      setAvailableCommands(data.enhanced_commands || {})
    } catch (error) {
      console.error('Error fetching voice commands:', error)
    }
  }

  const fetchVoiceStats = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/advanced-voice/analytics/usage`)
      const data = await response.json()
      setVoiceStats(data)
    } catch (error) {
      console.error('Error fetching voice stats:', error)
    }
  }

  const startRealtimeVoiceChat = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Initialize audio chat if not already done
      if (!audioChat.current) {
        audioChat.current = new RealtimeAudioChat()
        
        audioChat.current.onStatusChange = (status, errorMsg) => {
          setConnectionStatus(status)
          setIsConnected(status === 'connected')
          
          if (status === 'error') {
            setError(errorMsg || 'Connection failed')
          }
        }
        
        audioChat.current.onMessage = (message) => {
          console.log('Received voice message:', message)
          
          setConversation(prev => [...prev, {
            id: Date.now(),
            type: 'ai',
            content: message.text || message.content || 'AI response',
            timestamp: new Date()
          }])
        }
      }
      
      // Create voice session
      const sessionResponse = await fetch(`${backendUrl}/api/advanced-voice/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current-user',
          tenant_id: 'default-tenant',
          session_type: 'realtime_voice',
          context: { interface_type: 'advanced' }
        })
      })
      
      if (sessionResponse.ok) {
        const session = await sessionResponse.json()
        setActiveSession(session)
      }
      
      // Initialize realtime connection
      const success = await audioChat.current.init(backendUrl + '/api')
      
      if (success) {
        setIsListening(true)
        startAudioVisualization()
        
        // Add system message
        setConversation(prev => [...prev, {
          id: Date.now(),
          type: 'system',
          content: 'Voice chat connected. You can now speak naturally!',
          timestamp: new Date()
        }])
      }
      
    } catch (error) {
      console.error('Error starting voice chat:', error)
      setError('Failed to start voice chat: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const stopRealtimeVoiceChat = () => {
    if (audioChat.current) {
      audioChat.current.disconnect()
    }
    
    setIsListening(false)
    setIsConnected(false)
    setConnectionStatus('disconnected')
    stopAudioVisualization()
    
    if (activeSession) {
      // End session
      fetch(`${backendUrl}/api/advanced-voice/sessions/${activeSession.session_id}`, {
        method: 'DELETE'
      }).catch(console.error)
      
      setActiveSession(null)
    }
    
    setConversation(prev => [...prev, {
      id: Date.now(),
      type: 'system',
      content: 'Voice chat disconnected.',
      timestamp: new Date()
    }])
  }

  const startAudioVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      analyserRef.current = audioContextRef.current.createAnalyser()
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      
      analyserRef.current.fftSize = 256
      const bufferLength = analyserRef.current.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      
      const updateAudioLevel = () => {
        analyserRef.current.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((a, b) => a + b) / bufferLength
        setAudioLevel(Math.round((average / 255) * 100))
        
        animationRef.current = requestAnimationFrame(updateAudioLevel)
      }
      
      updateAudioLevel()
      
    } catch (error) {
      console.error('Error setting up audio visualization:', error)
    }
  }

  const stopAudioVisualization = () => {
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    
    if (analyserRef.current) {
      analyserRef.current = null
    }
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
    
    setAudioLevel(0)
  }

  const executeVoiceCommand = async (command) => {
    try {
      const response = await fetch(`${backendUrl}/api/advanced-voice/commands/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: command,
          user_id: 'current-user',
          tenant_id: 'default-tenant'
        })
      })

      const result = await response.json()
      
      setConversation(prev => [...prev, {
        id: Date.now(),
        type: 'user',
        content: command,
        timestamp: new Date()
      }, {
        id: Date.now() + 1,
        type: 'ai',
        content: result.response_text,
        timestamp: new Date(),
        action: result.action_taken
      }])
      
    } catch (error) {
      console.error('Error executing voice command:', error)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'disconnected': return 'bg-gray-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Advanced Voice Interface</h2>
          <p className="text-muted-foreground">Full audio interface with AI conversation and voice responses</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={`${getStatusColor(connectionStatus)} text-white flex items-center gap-1`}>
            <Radio className="w-3 h-3" />
            {connectionStatus}
          </Badge>
          {voiceStats && (
            <Badge variant="outline" className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {voiceStats.total_sessions} Sessions
            </Badge>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      <Tabs defaultValue="voice-chat" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="voice-chat">Voice Chat</TabsTrigger>
          <TabsTrigger value="commands">Voice Commands</TabsTrigger>
          <TabsTrigger value="conversation">Conversation</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="voice-chat" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Headphones className="w-5 h-5" />
                Realtime Voice Interface
              </CardTitle>
              <CardDescription>
                Natural voice conversation with AI using advanced speech recognition and synthesis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Voice Control Interface */}
              <div className="flex items-center justify-center">
                <div className="relative">
                  <Button
                    size="lg"
                    className={`h-24 w-24 rounded-full ${isListening ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'}`}
                    onClick={isListening ? stopRealtimeVoiceChat : startRealtimeVoiceChat}
                    disabled={loading}
                  >
                    {loading ? (
                      <RotateCcw className="w-8 h-8 animate-spin" />
                    ) : isListening ? (
                      <PhoneOff className="w-8 h-8" />
                    ) : (
                      <Phone className="w-8 h-8" />
                    )}
                  </Button>
                  
                  {/* Audio Level Visualization */}
                  {isListening && (
                    <div className="absolute -inset-2 rounded-full border-4 border-blue-300 animate-pulse">
                      <div className="absolute inset-0 rounded-full border-4 border-blue-200 animate-ping" style={{
                        transform: `scale(${1 + (audioLevel / 100) * 0.3})`
                      }} />
                    </div>
                  )}
                </div>
              </div>

              <div className="text-center">
                <p className="text-lg font-medium">
                  {isListening ? 'Listening...' : 'Click to start voice chat'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {isListening ? 'Speak naturally - AI will respond with voice' : 'Start a realtime voice conversation'}
                </p>
              </div>

              {/* Audio Level Meter */}
              {isListening && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Mic className="w-4 h-4" />
                    <Progress value={audioLevel} className="flex-1" />
                    <span className="text-sm font-mono w-12">{audioLevel}%</span>
                  </div>
                </div>
              )}

              {/* Connection Status */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="space-y-1">
                  <div className="text-sm font-medium">Status</div>
                  <Badge className={`${getStatusColor(connectionStatus)} text-white`}>
                    {connectionStatus}
                  </Badge>
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-medium">Audio Level</div>
                  <div className="text-lg font-mono">{audioLevel}%</div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm font-medium">Session</div>
                  <div className="text-sm">
                    {activeSession ? 'Active' : 'None'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="commands" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(availableCommands).map(([category, commands]) => (
              <Card key={category}>
                <CardHeader>
                  <CardTitle className="text-base capitalize">
                    {category.replace('_', ' ')}
                  </CardTitle>
                  <CardDescription>
                    {commands.length} available commands
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {commands.slice(0, 5).map((command, index) => (
                      <Button
                        key={index}
                        variant="ghost"
                        className="w-full justify-start h-auto p-2 text-left"
                        onClick={() => executeVoiceCommand(command)}
                      >
                        <div className="flex items-center gap-2">
                          <Mic className="w-3 h-3" />
                          <span className="text-sm">"{command}"</span>
                        </div>
                      </Button>
                    ))}
                    {commands.length > 5 && (
                      <div className="text-xs text-muted-foreground text-center">
                        +{commands.length - 5} more commands
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="conversation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Conversation History
              </CardTitle>
              <CardDescription>
                {conversation.length} messages in current session
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {conversation.map((message) => (
                  <div key={message.id} className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                      message.type === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : message.type === 'system'
                        ? 'bg-gray-100 text-gray-800'
                        : 'bg-gray-200 text-gray-800'
                    }`}>
                      <div className="text-sm">{message.content}</div>
                      <div className="text-xs opacity-70 mt-1">
                        {formatTime(message.timestamp)}
                      </div>
                      {message.action && (
                        <div className="text-xs opacity-70 mt-1">
                          Action: {message.action}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {conversation.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No conversation yet</p>
                    <p className="text-sm">Start voice chat to see messages here</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          {voiceStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Total Sessions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{voiceStats.total_sessions}</div>
                  <p className="text-xs text-muted-foreground">Voice conversations</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Active Now</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{voiceStats.active_sessions}</div>
                  <p className="text-xs text-muted-foreground">Current sessions</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Messages</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{voiceStats.total_messages}</div>
                  <p className="text-xs text-muted-foreground">Voice interactions</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Engagement</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{voiceStats.user_engagement_score}%</div>
                  <p className="text-xs text-muted-foreground">User satisfaction</p>
                </CardContent>
              </Card>
            </div>
          )}

          {voiceStats?.voice_feature_adoption && (
            <Card>
              <CardHeader>
                <CardTitle>Voice Features Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(voiceStats.voice_feature_adoption).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center gap-2">
                      {enabled ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                      <span className="text-sm capitalize">
                        {feature.replace('_', ' ')}
                      </span>
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