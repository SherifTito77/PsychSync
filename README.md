# 🧠 **PsychSync AI - Advanced Psychological Assessment Platform**

<div align="center">

![PsychSync Logo](https://img.shields.io/badge/PsychSync-AI%20Platform-blue?style=for-the-badge&logo=brain)
![Version](https://img.shields.io/badge/version-2.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen?style=for-the-badge)

**Enterprise-grade psychological assessment platform with AI-powered insights and 1000% performance optimization**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue?style=flat-square)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square)](https://postgresql.org)

[⭐ Star](https://github.com/psychsync/psychsync) | [🐛 Report Bug](https://github.com/psychsync/psychsync/issues) | [📖 Documentation](https://docs.psychsync.ai)

</div>

---

## **🎯 Overview**

PsychSync AI is a **revolutionary psychological assessment SaaS platform** that combines cutting-edge AI technology with evidence-based psychological frameworks to deliver comprehensive personality, team, and organizational insights.

### **🌟 Key Features**

- **🔬 Multi-Framework Assessments**: Big Five, MBTI, Enneagram, Predictive Index, and more
- **🤖 AI-Powered Insights**: Advanced NLP and machine learning for deep analysis
- **⚡ Lightning Performance**: 1000% optimized with advanced caching and request processing
- **🏢 Enterprise Teams**: Team optimization, succession planning, and organizational analytics
- **📊 Rich Dashboards**: Real-time analytics and comprehensive reporting
- **🔒 Military-Grade Security**: Advanced security with rate limiting and threat detection
- **🌐 Multi-Client Support**: Web, mobile, API, and IoT device optimization

## **💼 Two Deployment Options**

### 🆓 **Self-Hosted Version** (FREE)
- Complete privacy and data ownership
- Advanced open-source AI capabilities
- Local hosting with zero vendor lock-in
- **$0 forever** with enterprise features
- Full API access and customization

### ☁️ **Cloud Version** (Premium)
- Managed hosting and maintenance
- Advanced AI model integrations
- Professional support and SLA
- **Enterprise pricing** available
- Automatic updates and scaling

## **🚀 Quick Start**

### **Prerequisites**

- **Python 3.9+**
- **Node.js 16+**
- **PostgreSQL 15+**
- **Redis 6+**
- **Docker & Docker Compose** (optional but recommended)

### **🛠️ Installation**

#### **Option 1: Docker (Recommended)**

```bash
# Clone the repository
git clone https://github.com/psychsync/psychsync.git
cd psychsync

# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

#### **Option 2: Manual Installation**

```bash
# Clone the repository
git clone https://github.com/psychsync/psychsync.git
cd psychsync

# Backend Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database Setup
createdb psychsync
alembic upgrade head

# Frontend Setup
cd frontend
npm install
npm run build

# Start Services
# Backend (Terminal 1)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Terminal 2)
cd frontend && npm run dev
```

### **🔧 Environment Configuration**

Create `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/psychsync
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Performance
RATE_LIMIT_PER_MINUTE=1000
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=100

# External Services
SENTRY_DSN=your-sentry-dsn
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🌟 Key Features

### 📧 **Email Analysis** (Free & Paid)
- **Sentiment analysis** - Track emotional patterns
- **Behavioral insights** - Communication style analysis
- **Culture health** - Team psychological safety
- **AI coaching** - Personalized recommendations
- **Privacy-first** - Only metadata analysis, no content storage

### 🧠 **Psychological Assessments**
- **Big Five** (OCEAN) personality traits
- **MBTI** compatibility analysis
- **Enneagram** personality types
- **Clifton Strengths** assessment
- **Predictive Index** behavioral analysis

### 👥 **Team & Organization**
- Multi-team management
- Role-based permissions
- Assessment analytics
- Culture metrics dashboard
- Performance insights

## 📊 Email Analysis Capabilities

### 🔍 **Communication Patterns**
- Response time analysis
- Collaboration network mapping
- Leadership identification
- Conflict detection
- Work-life balance insights

### 💭 **Emotional Intelligence**
- Sentiment trend tracking
- Emotion detection patterns
- Stress level monitoring
- Engagement measurement
- Team morale assessment

### 🎯 **Coaching Insights**
- Personal development recommendations
- Team building suggestions
- Leadership coaching tips
- Communication improvement plans
- Culture enhancement strategies

## 🔧 Technical Stack

### Backend
- **FastAPI** (Python 3.12+) - Modern async web framework with automatic documentation
- **PostgreSQL 15+** with connection pooling (40 connections, 60 overflow)
- **Redis 7+** for caching, sessions, and rate limiting
- **SQLAlchemy 2.0** - Modern async ORM with type safety
- **Alembic** for database migrations with validation
- **Pydantic Settings** - Comprehensive configuration management

### Frontend
- **React 18** with TypeScript 5.0+ - Modern React with type safety
- **Vite** for lightning-fast build tooling and HMR
- **Tailwind CSS** for responsive utility-first styling
- **React Query** for server state management with caching
- **Context API** for global state management

### Enterprise Security
- **JWT Authentication** with refresh tokens and device fingerprinting
- **Rate Limiting** - Token bucket algorithm with DDoS protection
- **Input Validation** - Comprehensive SQL injection and XSS prevention
- **CSRF Protection** with token-based validation
- **Session Security** with timeout controls and audit logging
- **Password Security** with bcrypt and complexity requirements

### AI/NLP & Assessment Frameworks
- **Custom Assessment Processors** - Big Five, MBTI, Enneagram, Predictive Index
- **VADER + spaCy + NLTK** for sentiment and emotion analysis
- **Advanced Analytics** for team optimization and insights
- **Machine Learning** for behavioral pattern recognition
- **Multi-framework Support** for psychological assessments

### DevOps & Infrastructure
- **GitHub Actions CI/CD** with comprehensive automated pipeline:
  - Security scanning (Bandit, Safety, Semgrep)
  - Multi-environment testing (dev, staging, production)
  - Database migration validation
  - Performance regression testing
  - Security compliance checks
- **Docker** for containerized deployment
- **Performance Monitoring** with structured logging and metrics
- **Health Checks** for comprehensive system monitoring

### Infrastructure
- **Docker** & Docker Compose
- **Nginx** reverse proxy
- **SSL/TLS** encryption
- **Health checks** & monitoring

## 📚 Documentation

### 🆓 **Free Version Guides**
- [📖 Cost-Free Implementation Guide](./COST_FREE_GUIDE.md)
- [⚡ Quick Start Free](./QUICK_START_FREE.md)
- [📧 Free Email Setup](./FREE_EMAIL_SETUP.md)

### 💼 **General Documentation**
- [🏗️ Architecture Overview](./docs/ARCHITECTURE.md)
- [📡 API Documentation](./docs/API.md)
- [🔧 Development Setup](./docs/DEVELOPMENT.md)
- [🚀 Deployment Guide](./docs/DEPLOYMENT.md)

## 🛠️ Development

### Setup Development Environment
```bash
# Clone repository
git clone <your-repo-url>
cd psychsync

# Setup backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install
cd ..

# Database setup
alembic upgrade head

# Start services
uvicorn app.main:app --reload  # Backend
cd frontend && npm run dev     # Frontend
```

### Running Tests
```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Integration tests
pytest tests/integration/ -v
```

## 🚀 Deployment

### Free Localhost Deployment
```bash
# One-command setup
./setup_free.sh

# Start all services
./start_free.sh
```

### Production Deployment
```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Manual deployment
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔐 Security & Privacy

### Privacy-First Design
- ✅ **Email content never stored**
- ✅ **Only metadata analysis**
- ✅ **Encrypted credentials**
- ✅ **GDPR compliant**
- ✅ **User data control**

### Security Features
- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Encrypted sensitive data at rest
- API rate limiting
- SQL injection protection
- XSS and CSRF protection

### Free Version Benefits
- 🏠 **100% local hosting** - Your data never leaves your computer
- 🔒 **No tracking or analytics**
- 📖 **Open source and auditable**
- 💾 **Full data ownership and control**

## 🎯 Use Cases

### For Individuals
- **Personal Development** - Track communication patterns and emotional intelligence
- **Career Growth** - Improve professional relationships and leadership skills
- **Self-Awareness** - Understand your behavioral tendencies and strengths

### For Teams
- **Team Building** - Identify communication patterns and improve collaboration
- **Culture Health** - Monitor psychological safety and team morale
- **Conflict Prevention** - Early detection of communication issues
- **Performance Optimization** - Data-driven team development

### For Organizations
- **Culture Assessment** - Comprehensive organization-wide insights
- **Leadership Development** - Identify and develop emerging leaders
- **Employee Engagement** - Monitor and improve satisfaction levels
- **Risk Management** - Early warning system for organizational issues

## 🌟 Why Choose PsychSync?

### 🆓 **Unbeatable Value**
- **Free version** with powerful features
- **No subscription required** for basic use
- **Professional-grade insights** at zero cost
- **Scalable** to paid plans when needed

### 🔒 **Privacy Guaranteed**
- **Your data stays yours** in free version
- **No cloud dependencies** for sensitive analysis
- **Open source transparency**
- **GDPR and privacy compliant**

### 🧠 **Psychology-Backed**
- **Research-based assessments** (Big Five, MBTI, etc.)
- **Professional psychological frameworks**
- **Validated measurement tools**
- **Evidence-based insights**

### ⚡ **Easy to Use**
- **5-minute setup** for free version
- **Intuitive dashboard** and reports
- **Actionable recommendations**
- **No technical expertise required**

## 📈 Pricing

### 🆓 **Free Version** ($0/month)
- Up to 10 users per organization
- 3 email connections per user
- 90 days of analysis history
- All core assessment types
- Basic team analytics
- 100% privacy (localhost)

### 💼 **Professional** ($99/month)
- Unlimited users
- Unlimited email connections
- 1 year analysis history
- Advanced analytics
- Priority support
- Cloud hosting

### 🏢 **Enterprise** (Custom)
- Custom deployments
- Advanced security features
- Dedicated support
- Custom integrations
- SLA guarantees

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- 🐛 Report bugs and issues
- 💡 Suggest features and improvements
- 📖 Improve documentation
- 🔧 Submit pull requests
- 🧪 Add tests and coverage

## 📞 Support

### Free Version Support
- 📚 [Documentation](./docs/)
- 🐛 [GitHub Issues](https://github.com/your-repo/psychsync/issues)
- 💬 [Community Forums](https://github.com/your-repo/psychsync/discussions)

### Professional Support
- 📧 Email: support@psychsync.ai
- 💬 Live chat: Available on website
- 📅 Scheduled calls: Enterprise customers

## 🎉 Start Your Journey

### Ready to transform your team communication?

**For Free Localhost Setup:**
```bash
git clone <your-repo-url>
cd psychsync
./setup_free.sh
./start_free.sh
# Open http://localhost:5173
```

**For Cloud Setup:**
- Visit [psychsync.ai](https://psychsync.ai)
- Start free trial
- Connect your email accounts
- Get instant insights

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🧠 Transform your workplace communication with AI-powered insights - starting completely free!**

*Built with ❤️ for better teams and healthier organizations*
