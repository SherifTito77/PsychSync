# 🧠 PsychSync AI - Psychological Assessment & Email Analysis Platform

Professional psychological insights powered by AI - **with FREE localhost option!**

## 🎯 Two Ways to Use PsychSync

### 💼 **Cloud Version** (Paid)
- OAuth email integration (Gmail, Outlook)
- Advanced OpenAI/Anthropic NLP analysis
- Cloud hosting & maintenance
- Professional support
- **$100-500/month**

### 🆓 **Free Version** (localhost)
- IMAP email connectors
- Open-source NLP (VADER, spaCy)
- Self-hosted on your computer
- 100% privacy (data never leaves your machine)
- **$0 forever**

## 🚀 Quick Start

### Option 1: Free Localhost Setup (Recommended)
```bash
# Clone and setup free version
git clone <your-repo-url>
cd psychsync
./setup_free.sh
./start_free.sh

# Access at http://localhost:5173
```

### Option 2: Cloud Setup
```bash
# Traditional cloud setup
docker-compose up --build
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
- **FastAPI** (Python 3.11+)
- **PostgreSQL** with SQLAlchemy 2.0
- **Redis** for caching & sessions
- **Celery** for background tasks
- **Alembic** for database migrations

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Query** for data fetching
- **Context API** for state management

### AI/NLP
- **OpenAI/Anthropic** (Cloud version)
- **VADER + spaCy + NLTK** (Free version)
- **Custom assessment processors**
- **Sentiment & emotion analysis**

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