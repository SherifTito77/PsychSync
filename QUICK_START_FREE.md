# 🚀 PsychSync Free Email Analysis - Quick Start

Get your free email analysis system running in **5 minutes** with this streamlined guide.

## ⚡ Ultra Quick Start

### 1. System Check
```bash
# Check if you have the requirements
docker --version
docker-compose --version
python3 --version
```

### 2. One-Command Setup
```bash
# Clone and setup in one command
git clone <your-repo-url> && cd psychsync && ./setup_free.sh
```

### 3. Start Everything
```bash
# Start all services
./start_free.sh
```

### 4. Access System
- **Main App**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Database**: http://localhost:5050 (admin@psychsync.local / admin123)

## 📧 Add Your First Email Account

### Gmail (Easiest)
1. **Get App Password**:
   - Go to Google Account → Security → App passwords
   - Generate password for "Mail"
   - Copy the 16-character password

2. **Connect in App**:
   - Email: `your.email@gmail.com`
   - Password: Paste the app password
   - Click "Connect"

### Alternative: Try Demo Mode
```bash
# Create sample data without connecting real email
python -c "
from app.db.session import SessionLocal
from app.services.seed_test_data import create_demo_data
db = SessionLocal()
create_demo_data(db)
print('Demo data created!')
"
```

## 🔧 Quick Configuration

### Edit .env.free
```bash
# Generate encryption key (required)
python3 -c "from cryptography.fernet import Fernet; print('EMAIL_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Update your .env.free file
nano .env.free
```

### Essential Settings Only
```bash
SECRET_KEY=change-this-to-random-string
EMAIL_ENCRYPTION_KEY=your-generated-key-here
```

## 🎯 First Analysis

### Manual Test
```bash
# Test NLP analysis
curl -X POST "http://localhost:8000/api/v1/nlp/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Great work team! I am excited about this project."}'
```

### Expected Response
```json
{
  "sentiment": {"label": "positive", "compound": 0.75},
  "emotions": {"dominant_emotion": "joy"},
  "behavioral_indicators": {"collaboration_tendency": 0.8}
}
```

## 🔍 Check Everything Works

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:5173
docker-compose -f docker-compose.free.yml ps
```

### Database Connection
```bash
# Test database
docker-compose -f docker-compose.free.yml exec db psql -U psychsync_user -d psychsync_db -c "SELECT version();"
```

## 🛠️ Common Issues

### Port Already in Use
```bash
# Kill processes using ports 5432, 6379, 8000, 5173
sudo lsof -ti:5432 | xargs kill -9
sudo lsof -ti:6379 | xargs kill -9
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:5173 | xargs kill -9
```

### Permission Denied
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Then logout and login again
```

### Docker Memory Issues
```bash
# Increase Docker memory limit
# In Docker Desktop: Settings → Resources → Memory → 4GB+
```

## 📊 What You Get

### ✅ Free Features
- **3 email accounts** per user
- **90 days** of analysis history
- **Unlimited sentiment analysis**
- **Team culture insights**
- **Personal coaching recommendations**
- **100% privacy** (data never leaves your computer)

### 🔒 Privacy Guarantee
- ❌ No email content stored
- ❌ No data sent to cloud
- ❌ No tracking or analytics
- ✅ Only metadata analyzed
- ✅ Fully open source

## 🎓 Learn More

### Next Steps
1. **Connect more emails** for better insights
2. **Explore the API** at http://localhost:8000/docs
3. **Check database** at http://localhost:5050
4. **Read full guide**: COST_FREE_GUIDE.md

### Advanced Features
- **Team analysis** with multiple users
- **Custom NLP models** (install additional)
- **Advanced queries** in database
- **API integration** with other tools

## 💡 Tips

### Performance
- **SSD storage** for faster processing
- **8GB+ RAM** for better NLP performance
- **Close other apps** during initial analysis

### Email Tips
- **Start with 1 email account** to test
- **Use work email** for professional insights
- **Connect personal email** for communication patterns

### Analysis Tips
- **Wait 24 hours** after connecting emails
- **Check trends** over weeks, not days
- **Focus on patterns**, not individual emails

---

## 🎉 You're All Set!

Your **free PsychSync Email Analysis** system is running!

**Total cost**: $0 forever
**Privacy**: 100% local
**Features**: Professional-grade insights

**Ready to transform your communication insights?**

🚀 **Start analyzing**: http://localhost:5173
📚 **Learn more**: COST_FREE_GUIDE.md
🐛 **Get help**: GitHub issues

**Welcome to the future of workplace communication insights - completely free!** 🎊