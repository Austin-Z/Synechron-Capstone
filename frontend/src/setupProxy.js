const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/dashboard',
    createProxyMiddleware({
      target: 'http://localhost:8501',
      changeOrigin: true,
      pathRewrite: {
        '^/dashboard': '/' // Remove /dashboard prefix when forwarding to Streamlit
      },
    })
  );
};
