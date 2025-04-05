import { useNavigate } from 'react-router-dom';
import { Container, Typography, Box, Button, Paper } from '@mui/material';
import { SentimentDissatisfied, Home } from '@mui/icons-material';

const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 8, textAlign: 'center' }}>
        <Paper elevation={3} sx={{ p: 5, borderRadius: 2 }}>
          <SentimentDissatisfied sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          
          <Typography variant="h3" component="h1" gutterBottom>
            404 - Page Not Found
          </Typography>
          
          <Typography variant="h6" color="text.secondary" paragraph>
            Oops! The page you are looking for doesn't exist.
          </Typography>
          
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<Home />}
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
          >
            Back to Home
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default NotFoundPage;