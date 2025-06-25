import { 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  Button, 
  Box 
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Chat, Assessment, Search } from '@mui/icons-material'

function HomePage() {
  const navigate = useNavigate()

  return (
    <Box>
      <Typography variant="h4" gutterBottom align="center">
        Welcome to Flash AI Assistant 🐄
      </Typography>
      <Typography variant="h6" gutterBottom align="center" color="textSecondary">
        Making enterprise knowledge easier
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Chat sx={{ fontSize: 40, color: '#7ed321', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                AI Chat Assistant
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Ask questions about your enterprise knowledge base and get intelligent, 
                context-aware responses powered by our AI orchestrator.
              </Typography>
              <Button 
                variant="contained" 
                onClick={() => navigate('/chat')}
                sx={{ mt: 2 }}
              >
                Start Chatting
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Search sx={{ fontSize: 40, color: '#7ed321', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Semantic Search
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Search through your indexed documents using advanced vector similarity 
                and alias discovery technology.
              </Typography>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/chat')}
                sx={{ mt: 2 }}
              >
                Search Documents
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <Assessment sx={{ fontSize: 40, color: '#7ed321', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Monitor the health and performance of all microservices in the 
                Flash AI architecture.
              </Typography>
              <Button 
                variant="outlined" 
                onClick={() => navigate('/status')}
                sx={{ mt: 2 }}
              >
                View Status
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default HomePage 