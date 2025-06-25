import { useState } from 'react'
import { 
  Typography, 
  Card, 
  CardContent, 
  TextField,
  Button,
  Box,
  Paper
} from '@mui/material'

function ChatPage() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{ text: string, sender: 'user' | 'ai' }>>([])

  const handleSend = async () => {
    if (!message.trim()) return

    // Add user message
    const userMessage = { text: message, sender: 'user' as const }
    setMessages(prev => [...prev, userMessage])
    setMessage('')

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const aiMessage = { 
        text: `I received your message: "${userMessage.text}". The AI orchestrator and embedding services are ready to help you!`, 
        sender: 'ai' as const 
      }
      setMessages(prev => [...prev, aiMessage])
    }, 1000)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Flash AI Chat 💬
      </Typography>
      
      <Card sx={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
          {messages.length === 0 ? (
            <Typography color="textSecondary" align="center" sx={{ mt: 4 }}>
              Start a conversation with Flash AI Assistant!
            </Typography>
          ) : (
            <Box>
              {messages.map((msg, index) => (
                <Paper
                  key={index}
                  sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: msg.sender === 'user' ? '#e3f2fd' : '#f5f5f5',
                    ml: msg.sender === 'user' ? 4 : 0,
                    mr: msg.sender === 'ai' ? 4 : 0,
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    {msg.sender === 'user' ? 'You' : '🐄 Flash AI'}
                  </Typography>
                  <Typography variant="body1">{msg.text}</Typography>
                </Paper>
              ))}
            </Box>
          )}
        </CardContent>
        
        <Box sx={{ p: 2, display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask Flash AI anything..."
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            variant="outlined"
            size="small"
          />
          <Button 
            variant="contained" 
            onClick={handleSend}
            disabled={!message.trim()}
          >
            Send
          </Button>
        </Box>
      </Card>
    </Box>
  )
}

export default ChatPage 