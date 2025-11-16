# Frontend Deployment Guide - PsychSync Compliance System

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Build Process](#build-process)
4. [Deployment Options](#deployment-options)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring](#monitoring)

---

## Prerequisites

### Required Software
- Node.js 18+
- npm or yarn package manager
- Git
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)

### Required Services
- Backend API server running (see backend deployment guide)
- PostgreSQL database
- Redis server (for real-time features)
- WebSocket enabled server

### Environment Variables
Create `.env.production` file in frontend root:

```bash
# API Configuration
REACT_APP_API_BASE_URL=https://api.psychsync.ai
REACT_APP_WS_URL=ws://api.psychsync.ai:8000

# Application Settings
REACT_APP_NAME=PsychSync Compliance Platform
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production

# Analytics (Optional)
REACT_APP_GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID

# Sentry (Optional)
REACT_APP_SENTRY_DSN=your-sentry-dsn

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_AI_ASSISTANT=true
REACT_APP_ENABLE_WEBHOOKS=true
REACT_APP_ENABLE_MULTI_LANGUAGE=true
```

---

## Environment Setup

### 1. Install Dependencies

```bash
cd frontend

# Install production dependencies
npm install

# Install additional required packages
npm install socket.io-client clsx tailwind-merge lucide-react

# Install development dependencies
npm install --save-dev @types/node typescript
```

### 2. Update package.json Scripts

```json
{
  "scripts": {
    "start": "vite",
    "build": "tsc && vite build",
    "build:production": "npm run type-check && vite build --mode production",
    "build:analyze": "vite build --mode production && npx vite-bundle-analyzer dist",
    "preview": "vite preview",
    "type-check": "tsc --noEmit",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

---

## Build Process

### Development Build
```bash
npm run build
```

### Production Build
```bash
npm run build:production
```

### Build Analysis
```bash
npm run build:analyze
```

### Build Output
The build process creates optimized files in `frontend/dist/`:
- HTML files with hashed filenames
- CSS bundles with minification
- JavaScript chunks with code splitting
- Static assets (images, icons)
- Service worker for PWA functionality

---

## Deployment Options

### Option 1: Static Hosting (Recommended for Production)

#### Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Or use Vercel web interface
# 1. Push to GitHub
# 2. Connect Vercel to your repository
# 3. Deploy
```

#### Deploy to Netlify
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Build and deploy
npm run build
netlify deploy --prod --dir=dist
```

#### Deploy to AWS S3 + CloudFront
```bash
# 1. Create S3 bucket
aws s3 mb s3://psychsync-frontend --region us-east-1

# 2. Configure bucket for website hosting
aws s3 website s3://psychsync-frontend/ --index-file index.html --error-document index.html

# 3. Upload build files
aws s3 sync dist/ s3://psychsync-frontend/ --delete

# 4. Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name psychsync-frontend.s3.amazonaws.com \
  --default-root-object index.html \
  --enabled
```

### Option 2: Docker Deployment

#### Dockerfile.production
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build:production

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose
```yaml
# docker-compose.frontend.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.production
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    restart: always
    environment:
      - NODE_ENV=production
```

#### Build and Deploy
```bash
# Build and start with Docker Compose
docker-compose -f docker-compose.frontend.yml up -d --build

# Scale if needed
docker-compose -f docker-compose.frontend.yml up -d --scale frontend=3
```

### Option 3: Kubernetes Deployment

#### kubernetes/frontend-deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: psychsync-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: psychsync-frontend
  template:
    metadata:
      labels:
        app: psychsync-frontend
    spec:
      containers:
      - name: frontend
        image: psychsync/frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        env:
        - name: NODE_ENV
          value: "production"
---
apiVersion: v1
kind: Service
metadata:
  name: psychsync-frontend-service
spec:
  selector:
    app: psychsync-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

#### Deploy to Kubernetes
```bash
# Apply configuration
kubectl apply -f kubernetes/

# Check deployment
kubectl get pods -l app=psychsync-frontend
kubectl get services
```

---

## Configuration

### Environment Variables
Configure your production environment variables:

```bash
# Production
export REACT_APP_API_BASE_URL=https://api.psychsync.ai
export REACT_APP_WS_URL=wss://api.psychsync.ai:8000

# Staging
export REACT_APP_API_BASE_URL=https://api-staging.psychsync.ai
export REACT_APP_WS_URL=wss://api-staging.psychsync.ai:8000

# Development
export REACT_APP_API_BASE_URL=http://localhost:8000
export REACT_APP_WS_URL=ws://localhost:8000
```

### API Endpoints Configuration
Update `src/services/api.ts` with your production URLs:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
```

### Service Worker Configuration
```typescript
// src/service-worker.ts
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then((registration) => {
      console.log('SW registered: ', registration);
    })
    .catch((registrationError) => {
      console.log('SW registration failed: ', registrationError);
    });
}
```

---

## Testing

### Unit Testing
```bash
# Run all tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Integration Testing
```bash
# Test build output
npm run preview

# Test with different browsers
npx playwright test
```

### End-to-End Testing
```bash
# Install Playwright
npm install @playwright/test

# Run E2E tests
npx playwright test

# Run tests with headed mode
npx playwright test --headed
```

### Lighthouse Testing
```bash
# Install Lighthouse CLI
npm install -g @lhci/cli@0.12.x

# Run Lighthouse audit
lhci autorun
```

### Accessibility Testing
```bash
# Install axe-core for automated testing
npm install --save-dev axe-core

# Test accessibility
npx axe http://localhost:5173
```

---

## Performance Optimization

### Bundle Analysis
```bash
# Analyze bundle size
npm run build:analyze

# Check for unused dependencies
npx depcheck

# Optimize images
npx imagemin src/assets/*
```

### Lazy Loading Implementation
```typescript
// Code splitting example
const LazyAnalyticsDashboard = React.lazy(() => import('./AnalyticsDashboard'));

// Route-level code splitting
<Suspense fallback={<LoadingSpinner />}>
  <Route path="/analytics" element={<LazyAnalyticsDashboard />} />
</Suspense>
```

### Image Optimization
```typescript
// src/components/OptimizedImage.tsx
const OptimizedImage: React.FC<{ src: string; alt: string }> = ({ src, alt }) => {
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      className="object-cover"
    />
  );
};
```

### Service Worker for Caching
```javascript
// public/sw.js
const CACHE_NAME = 'psychsync-v1';
const urlsToCache = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

---

## Monitoring

### Application Monitoring

#### Sentry Integration
```typescript
// src/monitoring/sentry.ts
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay()
  ]
});
```

#### Google Analytics
```typescript
// src/monitoring/analytics.ts
import ReactGA from 'react-ga4';

const MEASUREMENT_ID = process.env.REACT_APP_GOOGLE_ANALYTICS_ID;

if (MEASUREMENT_ID) {
  ReactGA.initialize(MEASUREMENT_ID);
}

export const trackEvent = (action: string, category: string) => {
  ReactGA.event({
    category,
    action,
    label: 'User Interaction'
  });
};
```

### Performance Monitoring

#### Core Web Vitals
```typescript
// src/monitoring/web-vitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

const sendToAnalytics = (metric: any) => {
  // Send to your analytics service
  gtag('event', metric.name, {
    value: Math.round(metric.value),
    event_category: 'Web Vitals'
  });
};

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

#### Error Boundaries
```typescript
// src/components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);

    // Send to Sentry
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack
        }
      }
    });
  }
}
```

### Health Check Endpoints

#### Liveness Probe
```typescript
// src/api/health.ts
export const healthCheck = async () => {
  try {
    const response = await fetch('/api/v1/health');
    if (!response.ok) throw new Error('Health check failed');
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};
```

---

## Security Considerations

### HTTPS and SSL/TLS
```nginx
# nginx.conf for production
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    ssl_certificate /etc/nginx/certs/psychsync.crt;
    ssl_certificate_key /etc/nginx/certs/psychsync.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
}
```

### Content Security Policy
```typescript
// Content-Security-Policy header
const CSP_HEADER = "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' https://api.psychsync.ai wss://api.psychsync.ai:8000";
```

### Environment Variable Security
```bash
# Use secure environment variable storage
# Never commit sensitive data to repository
echo "REACT_APP_API_KEY=your-secret-key" >> .env.production

# Use encrypted secrets in production
kubectl create secret generic psychsync-secrets --from-literal=api-key=your-secret-key
```

---

## Troubleshooting

### Common Issues

#### Build Fails
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear build cache
rm -rf dist
npm run build
```

#### WebSocket Connection Issues
```typescript
// Check WebSocket connectivity
const checkWebSocketConnection = () => {
  if (!navigator.onLine) {
    console.log('Browser is offline');
    return false;
  }
  return true;
};
```

#### API Connection Issues
```typescript
// Add connection retry logic
const apiCallWithRetry = async (url: string, options: RequestInit, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  throw new Error('Max retries exceeded');
};
```

### Performance Issues

#### Bundle Size Too Large
```bash
# Analyze bundle
npm run build:analyze

# Identify large dependencies
npx webpack-bundle-analyzer dist/static/js/*.js

# Remove unused dependencies
npx depcheck

# Tree-shake configuration
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['lucide-react']
        }
      }
    }
  }
});
```

---

## Rollback Procedure

### Quick Rollback
```bash
# Deploy previous version
git checkout previous-stable-tag
npm run build

# Update hosting service with previous build
netlify deploy --prod --dir=dist
```

### Blue-Green Deployment
```bash
# Deploy to staging environment
npm run build:staging
vercel --staging

# Run smoke tests
npm run test:smoke

# Promote to production
vercel --prod
```

### Database Rollback
```bash
# Database rollback
alembic downgrade -1

# Application rollback
heroku rollback
```

---

## Maintenance

### Regular Updates
- Weekly security updates for dependencies
- Monthly bundle analysis and optimization
- Quarterly performance audits
- Annual architecture review

### Monitoring Checklist
- [ ] Application performance metrics
- [ ] Error rates and types
- [ ] User engagement analytics
- [ ] Security scanning results
- [ ] Accessibility compliance
- [ ] Core Web Vitals scores

This guide provides comprehensive instructions for deploying the PsychSync compliance frontend in production environments with proper security, monitoring, and performance optimizations.