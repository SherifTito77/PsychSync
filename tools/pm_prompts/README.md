# 🚀 Product Management Prompts - Standalone Service

**50 Expert Product Management Prompts on Port 5001**

A beautiful, self-contained web service for browsing and executing product management prompts.

---

## 🎯 What is This?

A standalone Flask service that provides:
- **50 expert product management prompts**
- **5 categories** (Roadmap, UX, Growth, Analytics, Operations)
- **4 pre-built workflows** (Feature Launch, Retention, Enterprise, Planning)
- **Beautiful web interface** at `http://localhost:5001`
- **REST API** for programmatic access

---

## ⚡ Quick Start

### Option 1: Using the Start Script (Easiest)

```bash
cd product_management_prompts
./start.sh
```

Then open: **http://localhost:5001**

### Option 2: Manual Start

```bash
# Install dependencies
pip3 install flask flask-cors

# Start the service
cd product_management_prompts
python3 product_prompt_service.py
```

Then open: **http://localhost:5001**

---

## 🌐 Web Interface

Once started, open **http://localhost:5001** in your browser:

### Features:
- 🔍 **Search** prompts by keyword
- 📂 **Browse** by category
- 🎯 **Filter** by type and complexity
- ⚡ **Quick Workflows** for common scenarios
- 📊 **Statistics** dashboard
- 🚀 **One-click execution**

### Quick Workflows:
1. **Feature Launch** - From ideation to announcement
2. **Retention Improvement** - Reduce churn
3. **Enterprise Expansion** - B2B growth
4. **Quarterly Planning** - OKRs and roadmaps

---

## 📡 REST API

### Base URL
```
http://localhost:5001/api
```

### Endpoints

#### Get All Prompts
```bash
curl http://localhost:5001/api/prompts
```

#### Get Specific Prompt
```bash
curl http://localhost:5001/api/prompts/rs_001
```

#### Search Prompts
```bash
curl http://localhost:5001/api/prompts/search/roadmap
```

#### Get Categories
```bash
curl http://localhost:5001/api/categories
```

#### Get Workflow
```bash
curl http://localhost:5001/api/workflows/feature_launch
```

#### Execute Prompt
```bash
curl -X POST http://localhost:5001/api/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": "rs_001", "context": {}}'
```

#### Get Statistics
```bash
curl http://localhost:5001/api/stats
```

---

## 📁 File Structure

```
product_management_prompts/
├── product_prompt_service.py    # Main Flask application
├── templates/
│   └── product_prompts.html     # Web interface
├── start.sh                      # Launch script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🎨 Features

### Categories
- 🗺️ **Roadmap & Strategy** (10 prompts) - Strategic planning
- 👥 **User Experience** (10 prompts) - UX & onboarding
- 📈 **Growth & Monetization** (8 prompts) - Revenue & pricing
- 📊 **Analytics & Metrics** (10 prompts) - KPIs & dashboards
- ⚙️ **Operations** (12 prompts) - Workflows & QA

### Prompt Metadata
- **Type**: Strategic, Tactical, Analytical, Technical, Creative
- **Complexity**: Low, Medium, High
- **Estimated Time**: 1-6 hours
- **Expected Outputs**: 3-5 deliverables
- **Use Cases**: Common scenarios
- **Related Prompts**: Cross-references

---

## 🔧 Configuration

### Change Port
Edit `product_prompt_service.py` line ~287:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Enable Debug Mode
Already enabled by default. Set `debug=False` for production.

---

## 📊 Examples

### Python Client
```python
import requests

# Get all prompts
response = requests.get('http://localhost:5001/api/prompts')
prompts = response.json()

# Execute a prompt
response = requests.post('http://localhost:5001/api/execute',
    json={'prompt_id': 'rs_001', 'context': {'team_size': 10}}
)
execution = response.json()
```

### JavaScript Client
```javascript
// Get all prompts
fetch('http://localhost:5001/api/prompts')
    .then(r => r.json())
    .then(data => console.log(data.prompts));

// Execute a prompt
fetch('http://localhost:5001/api/execute', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt_id: 'rs_001', context: {}})
})
.then(r => r.json())
.then(data => console.log(data.execution));
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:5001/api/health

# Get stats
curl http://localhost:5001/api/stats

# Search prompts
curl http://localhost:5001/api/prompts/search/roadmap

# Get workflow
curl http://localhost:5001/api/workflows/feature_launch
```

---

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Find process using port 5001
lsof -i :5001

# Kill it
kill -9 <PID>
```

### Python Not Found
```bash
# Install Python 3
brew install python3  # macOS
sudo apt-get install python3  # Ubuntu
```

### Flask Not Installed
```bash
pip3 install flask flask-cors
```

### Can't Access from Other Devices
```bash
# Make sure firewall allows port 5001
# Or use localhost instead of 0.0.0.0 in product_prompt_service.py
```

---

## 🚀 Deployment

### Production

For production deployment:

1. **Use production WSGI server**:
   ```bash
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 product_prompt_service:app
   ```

2. **Disable debug mode**:
   ```python
   app.run(host='0.0.0.0', port=5001, debug=False)
   ```

3. **Use environment variables**:
   ```python
   import os
   PORT = int(os.environ.get('PORT', 5001))
   app.run(host='0.0.0.0', port=PORT, debug=False)
   ```

4. **Add reverse proxy** (nginx/Apache) for SSL

---

## 📚 Related Services

- **AI Engineering Prompts**: http://localhost:5000
- **PsychSync API**: http://localhost:8000
- **PsychSync Frontend**: http://localhost:5173

---

## 🤝 Integration

This service can be integrated with:
- **PsychSync Platform** - Full backend integration
- **Standalone Tool** - Independent use
- **API Integration** - Build custom clients
- **CLI Tool** - `python3 ../../scripts/product_prompts_cli.py`

---

## 📝 Notes

- **Data Source**: Reads from `app/db/product_management_prompts.json`
- **No Database Required**: Runs standalone without database
- **Stateless**: Each request is independent
- **In-Memory Execution Tracking**: Resets on restart

---

## 🎯 Use Cases

Perfect for:
- Product Managers
- Product Owners
- Startup Founders
- Product Teams
- Agile Coaches
- Product Strategy Sessions

---

## 📄 License

MIT License - Part of PsychSync Platform

---

## 🙏 Acknowledgments

Based on industry best practices in product management and modern product development frameworks.

---

**Made with ❤️ for Product Managers**

**Version**: 1.0.0
**Port**: 5001
**Last Updated**: 2025-01-17

For issues or questions, please contact the PsychSync team.
