import { useState, useEffect } from 'react'
import { 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  Chip,
  Box,
  CircularProgress
} from '@mui/material'
import axios from 'axios'

interface ServiceStatus {
  status: string
  url?: string
  response_time?: number
  error?: string
}

interface HealthResponse {
  gateway: string
  timestamp: string
  services: {
    [key: string]: ServiceStatus
  }
}

function SystemStatus() {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await axios.get('/api/health')
        setHealthData(response.data)
      } catch (error) {
        console.error('Failed to fetch health status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
    const interval = setInterval(fetchHealth, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success'
      case 'unhealthy': return 'error'
      case 'unavailable': return 'error'
      default: return 'default'
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Status 📊
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Real-time monitoring of Flash AI microservices
      </Typography>
      
      {healthData && (
        <>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Gateway Status
              </Typography>
              <Chip 
                label={healthData.gateway}
                color={getStatusColor(healthData.gateway) as any}
                sx={{ mr: 2 }}
              />
              <Typography variant="body2" color="textSecondary">
                Last updated: {new Date(healthData.timestamp).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
          
          <Grid container spacing={3}>
            {Object.entries(healthData.services).map(([serviceName, serviceData]) => (
              <Grid item xs={12} md={6} key={serviceName}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {serviceName.charAt(0).toUpperCase() + serviceName.slice(1)}
                    </Typography>
                    <Chip 
                      label={serviceData.status}
                      color={getStatusColor(serviceData.status) as any}
                      sx={{ mb: 2 }}
                    />
                    {serviceData.url && (
                      <Typography variant="body2" color="textSecondary">
                        URL: {serviceData.url}
                      </Typography>
                    )}
                    {serviceData.response_time && (
                      <Typography variant="body2" color="textSecondary">
                        Response time: {serviceData.response_time.toFixed(3)}s
                      </Typography>
                    )}
                    {serviceData.error && (
                      <Typography variant="body2" color="error">
                        Error: {serviceData.error}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </Box>
  )
}

export default SystemStatus 