let express;
try {
  express = require('express');
} catch (error) {
  console.error('[EXPRESS] Error loading express module:', error.message);
  console.log('[EXPRESS] Trying to load express from global installation...');
  process.exit(1); // Exit with error so Railway can retry
}

const path = require('path');
const fs = require('fs');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();
const PORT = process.env.EXPRESS_PORT || 8080;
const STREAMLIT_PORT = process.env.STREAMLIT_PORT || 3001;

console.log(`[EXPRESS] Starting server on port ${PORT}`);

// Middleware to log all requests
app.use((req, res, next) => {
  console.log(`[EXPRESS] ${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Setup proxy for dashboard requests to Streamlit
const streamlitProxy = createProxyMiddleware({
  target: `http://127.0.0.1:${STREAMLIT_PORT}`,
  changeOrigin: true,
  pathRewrite: { '^/dashboard': '/' },
  ws: true,
  logLevel: 'debug'
});

// Apply proxy middleware to dashboard routes
app.use('/dashboard', streamlitProxy);
app.use('/_stcore', streamlitProxy); // For Streamlit static files

// Check if the build directory exists
const buildPath = path.join(__dirname, 'frontend', 'build');
if (fs.existsSync(buildPath)) {
  console.log(`[EXPRESS] Build directory exists at ${buildPath}`);
  
  // List files in the build directory
  const files = fs.readdirSync(buildPath);
  console.log(`[EXPRESS] Files in build directory: ${files.join(', ')}`);
  
  // Serve static files from the React build
  app.use(express.static(buildPath));
  
  // Always return the index.html for any request that isn't a static file
  app.get('*', (req, res) => {
    res.sendFile(path.join(buildPath, 'index.html'));
  });
} else {
  console.log(`[EXPRESS] Build directory does not exist at ${buildPath}`);
  
  // Serve a simple HTML page if the build directory doesn't exist
  app.get('*', (req, res) => {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>FOFs Dashboard - Express Fallback</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .container { max-width: 800px; margin: 0 auto; }
          .button { display: inline-block; background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>FOFs Dashboard - Express Fallback</h1>
          <p>The React frontend build files could not be found. This is a fallback page served by Express.</p>
          
          <h2>Diagnostic Information</h2>
          <p>Build directory: ${buildPath}</p>
          <p>Current directory: ${__dirname}</p>
          <p>Request URL: ${req.url}</p>
          
          <h2>Quick Access</h2>
          <p>
            <a href="/dashboard" class="button">Go to Dashboard</a>
          </p>
        </div>
      </body>
      </html>
    `);
  });
}

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[EXPRESS] Server is running on port ${PORT}`);
});
