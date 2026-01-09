const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();

// 静态文件
app.use('/', express.static('.'));

// 代理 /api 到 Flask
app.use('/api', createProxyMiddleware({
  target: 'http://127.0.0.1:5001',
  changeOrigin: true
}));

app.listen(5000, () => console.log('Front dev-server http://localhost:5000'));