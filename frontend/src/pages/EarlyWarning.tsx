// Early Warning & Risk Dashboard - Overview page for all early warning features
import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
} from '@mui/material';
import {
  NavLink,
  useNavigate,
} from 'react-router-dom';

interface FeatureCard {
  title: string;
  description: string;
  path: string;
  icon: string;
  status: 'active' | 'beta' | 'coming-soon';
  color: string;
}

const EarlyWarning: React.FC = () => {
  const navigate = useNavigate();

  const features: FeatureCard[] = [
    {
      title: 'Burnout Prevention',
      description: '7-90 day burnout prediction & prevention with AI-powered risk assessment',
      path: '/burnout-prevention',
      icon: '🔥',
      status: 'active',
      color: '#FF6B6B'
    },
    {
      title: 'Behavioral Analytics',
      description: 'Communication patterns & sentiment analysis for early risk detection',
      path: '/behavioral-analytics',
      icon: '🧠',
      status: 'active',
      color: '#4ECDC4'
    },
    {
      title: 'Toxic Behavior Detection',
      description: 'Harassment & toxic pattern monitoring with automated alerts',
      path: '/toxic-behavior-detection',
      icon: '🛡️',
      status: 'active',
      color: '#95E1D3'
    },
    {
      title: 'Employee Safety',
      description: 'Workplace safety & incident tracking with real-time monitoring',
      path: '/employee-safety',
      icon: '⚠️',
      status: 'active',
      color: '#FFA07A'
    },
    {
      title: 'Anomaly Detection',
      description: 'ML-powered pattern detection & automated alerts',
      path: '/anomaly-detection',
      icon: '🚨',
      status: 'beta',
      color: '#DDA0DD'
    },
    {
      title: 'Team Risk Dashboard',
      description: 'Team-level risk indicators & heatmap visualization',
      path: '/team-dashboard',
      icon: '👥',
      status: 'active',
      color: '#87CEEB'
    },
    {
      title: 'Burnout Prediction',
      description: 'AI-powered risk prediction & advanced analytics',
      path: '/burnout-prediction',
      icon: '🔮',
      status: 'beta',
      color: '#F0E68C'
    }
  ];

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
        return '#4CAF50';
      case 'beta':
        return '#FF9800';
      case 'coming-soon':
        return '#9E9E9E';
      default:
        return '#9E9E9E';
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case 'active':
        return 'Active';
      case 'beta':
        return 'Beta';
      case 'coming-soon':
        return 'Coming Soon';
      default:
        return 'Unknown';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 2, fontWeight: 'bold' }}>
          ⚡ Early Warning & Risk Management
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Comprehensive tools to identify, prevent, and mitigate workplace risks before they escalate.
          Monitor burnout, behavioral patterns, and safety incidents in real-time.
        </Typography>

        {/* Quick Stats */}
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {features.filter(f => f.status === 'active').length}
                </Typography>
                <Typography variant="body2">Active Features</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  {features.filter(f => f.status === 'beta').length}
                </Typography>
                <Typography variant="body2">Beta Features</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  7
                </Typography>
                <Typography variant="body2">Risk Monitoring Tools</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
              <CardContent>
                <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                  24/7
                </Typography>
                <Typography variant="body2">Real-time Monitoring</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Features Grid */}
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
        Available Features
      </Typography>

      <Grid container spacing={3}>
        {features.map((feature) => (
          <Grid item xs={12} sm={6} md={4} key={feature.path}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
                border: feature.status === 'beta' ? '2px dashed #FF9800' : 'none',
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      fontSize: '2.5rem',
                      mr: 2,
                      bgcolor: feature.color + '20',
                      p: 1,
                      borderRadius: 2,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {feature.title}
                    </Typography>
                    <Chip
                      label={getStatusLabel(feature.status)}
                      size="small"
                      sx={{
                        bgcolor: getStatusColor(feature.status),
                        color: 'white',
                        mt: 0.5,
                      }}
                    />
                  </Box>
                </Box>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  {feature.description}
                </Typography>

                <Button
                  component={NavLink}
                  to={feature.path}
                  variant="contained"
                  fullWidth
                  disabled={feature.status === 'coming-soon'}
                  sx={{
                    mt: 'auto',
                    bgcolor: feature.color,
                    '&:hover': {
                      bgcolor: feature.color,
                      opacity: 0.8,
                    },
                  }}
                >
                  {feature.status === 'coming-soon' ? 'Coming Soon' : 'Explore'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Getting Started Section */}
      <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
          🚀 Getting Started with Early Warning
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Start with <strong>Burnout Prevention</strong> to predict employee burnout risk 7-90 days in advance,
          or use <strong>Behavioral Analytics</strong> to monitor communication patterns for early risk signs.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => navigate('/burnout-prevention')}
          >
            Start with Burnout Prevention
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            onClick={() => navigate('/behavioral-analytics')}
          >
            Explore Behavioral Analytics
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default EarlyWarning;
