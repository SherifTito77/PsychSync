#!/usr/bin/env node

const http = require('http');
const url = require('url');

const PORT = 5174;
const TARGET_PORT = 5176;

const server = http.createServer((req, res) => {
    // Parse the request URL
    const parsedUrl = url.parse(req.url, true);
    const targetUrl = `http://localhost:${TARGET_PORT}${parsedUrl.pathname}${parsedUrl.search}`;

    console.log(`Redirecting ${req.method} ${req.url} to ${targetUrl}`);

    // Set CORS headers for development
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // Handle OPTIONS requests for CORS
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // For HEAD requests (like the ping check), respond directly
    if (req.method === 'HEAD') {
        res.writeHead(200, {
            'Content-Type': 'text/html',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        });
        res.end();
        return;
    }

    // Check if it's an API request
    if (parsedUrl.pathname.startsWith('/api/')) {
        // Redirect API calls to the backend (assuming backend is on port 8000)
        const backendUrl = `http://localhost:8000${parsedUrl.pathname}${parsedUrl.search}`;
        console.log(`Proxying API request to: ${backendUrl}`);

        const proxyReq = http.request(backendUrl, {
            method: req.method,
            headers: req.headers
        }, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res);
        });

        proxyReq.on('error', (err) => {
            console.error('Proxy error:', err);
            res.writeHead(502, { 'Content-Type': 'text/plain' });
            res.end('Bad Gateway: Backend server unavailable');
        });

        req.pipe(proxyReq);
        return;
    }

    // For all other requests, redirect to the correct frontend port
    res.writeHead(302, {
        'Location': targetUrl,
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    });
    res.end();
});

server.listen(PORT, () => {
    console.log(`🚀 Port redirect server running on http://localhost:${PORT}`);
    console.log(`📡 Redirecting all traffic to http://localhost:${TARGET_PORT}`);
    console.log(`🔧 This solves the "ERR_CONNECTION_REFUSED" on port 5174`);
    console.log(`⚡ API requests will be proxied to the backend`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down redirect server...');
    server.close(() => {
        console.log('✅ Redirect server stopped');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down redirect server...');
    server.close(() => {
        console.log('✅ Redirect server stopped');
        process.exit(0);
    });
});
