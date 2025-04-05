import { Box, Container, Typography, Link as MuiLink } from '@mui/material';

const Footer = () => {
  return (
    <Box 
      component="footer" 
      sx={{ 
        py: 3, 
        mt: 'auto',
        backgroundColor: theme => theme.palette.mode === 'light' 
          ? theme.palette.grey[200] 
          : theme.palette.grey[900]
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          {'© '}
          <MuiLink color="inherit" href="https://github.com">
            Collaborative Coding Agents
          </MuiLink>{' '}
          {new Date().getFullYear()}
          {'. Built with ❤️ for better code generation.'}
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;