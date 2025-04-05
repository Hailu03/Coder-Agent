import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Box, 
  Button, 
  Paper, 
  Card, 
  CardContent, 
  CardHeader,
  Avatar,
  useTheme
} from '@mui/material';
import { 
  Psychology, 
  Search, 
  Code, 
  Speed,
  Architecture,
  AutoAwesome
} from '@mui/icons-material';

const HomePage = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  // Features list for the homepage
  const features = [
    {
      title: 'Smart Planning',
      description: 'AI agents analyze your requirements and create an optimal solution plan',
      icon: <Psychology fontSize="large" color="primary" />
    },
    {
      title: 'Deep Research',
      description: 'Automatically researches libraries, algorithms, and best practices',
      icon: <Search fontSize="large" color="primary" />
    },
    {
      title: 'Clean Code Generation',
      description: 'Produces readable, optimized code that follows best practices',
      icon: <Code fontSize="large" color="primary" />
    },
    {
      title: 'Performance Optimization',
      description: 'Identifies and implements efficient algorithms and data structures',
      icon: <Speed fontSize="large" color="primary" />
    },
    {
      title: 'Architecture Design',
      description: 'Creates well-structured code organization with proper design patterns',
      icon: <Architecture fontSize="large" color="primary" />
    },
    {
      title: 'Multi-Agent Collaboration',
      description: 'Agents work together, sharing insights to create better solutions',
      icon: <AutoAwesome fontSize="large" color="primary" />
    }
  ];

  return (
    <Container maxWidth="lg">
      {/* Hero Section */}
      <Box 
        sx={{ 
          my: 4, 
          p: 4, 
          borderRadius: 2,
          background: theme => `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
          color: 'white',
          textAlign: 'center'
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom>
          Collaborative Coding Agents
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Multi-agent AI system that transforms requirements into clean, optimized code
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Button 
            variant="contained" 
            size="large" 
            color="secondary"
            onClick={() => navigate('/solve')}
            sx={{ 
              fontWeight: 'bold', 
              px: 4, 
              py: 1.5,
              backgroundColor: 'white',
              color: theme.palette.primary.main,
              '&:hover': {
                backgroundColor: theme.palette.grey[200]
              }
            }}
          >
            Start Coding
          </Button>
        </Box>
      </Box>

      {/* Features Section */}
      <Typography variant="h4" component="h2" gutterBottom align="center" sx={{ my: 4 }}>
        How It Works
      </Typography>
      <Box 
        sx={{ 
          mb: 6,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: 3
        }}
      >
        {features.map((feature, index) => (
          <Box 
            key={index}
            sx={{ 
              width: { xs: '100%', sm: 'calc(50% - 24px)', md: 'calc(33.333% - 24px)' },
              display: 'flex',
              justifyContent: 'center'
            }}
          >
            <Card 
              sx={{ 
                height: '100%', 
                width: '100%',
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-10px)',
                  boxShadow: 6
                }
              }}
              elevation={3}
            >
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                    {feature.icon}
                  </Avatar>
                }
                title={<Typography variant="h6">{feature.title}</Typography>}
                sx={{ textAlign: 'center' }}
              />
              <CardContent sx={{ textAlign: 'center', flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="body1">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      {/* How to Use Section */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          mb: 6, 
          borderRadius: 2
        }}
      >
        <Typography variant="h4" component="h2" gutterBottom align="center">
          Getting Started
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main }}>1</Avatar>
            <Typography variant="body1">
              <strong>Enter your requirements</strong> - Describe the programming problem or paste the task from sources like LeetCode
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main }}>2</Avatar>
            <Typography variant="body1">
              <strong>Choose a programming language</strong> - Select your preferred language for the solution
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main }}>3</Avatar>
            <Typography variant="body1">
              <strong>Let the agents collaborate</strong> - Our AI agents will plan, research, and generate code
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main }}>4</Avatar>
            <Typography variant="body1">
              <strong>Get your solution</strong> - Receive clean, well-structured code with explanations
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button 
            variant="contained" 
            size="large" 
            color="primary"
            onClick={() => navigate('/solve')}
          >
            Try It Now
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default HomePage;