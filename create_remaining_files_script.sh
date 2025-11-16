#!/bin/bash

# ============================================================================
# PsychSync AI - Complete HTML Template Creation Script
# Creates all missing HTML files while avoiding duplicates
# ============================================================================

set -e  # Exit on error

echo "🚀 Creating PsychSync AI HTML Templates..."
echo "================================================"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Create directory structure
# ============================================================================
echo -e "${BLUE}📁 Creating directory structure...${NC}"

mkdir -p app/templates/{email,docs,errors,admin}
mkdir -p frontend/public/{marketing,legal,help,assets}
mkdir -p static

echo -e "${GREEN}✓ Directories created${NC}"

# ============================================================================
# Backend Email Templates (NEW - not duplicates)
# ============================================================================
echo -e "${BLUE}📧 Creating email templates...${NC}"

# subscription_confirmation.html (NEW)
cat > app/templates/email/subscription_confirmation.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Subscription Confirmed - PsychSync</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: white; padding: 40px; border-radius: 8px;">
        <div style="text-align: center; border-bottom: 2px solid #6366f1; padding-bottom: 20px;">
            <div style="font-size: 28px; font-weight: bold; color: #6366f1;">PsychSync AI</div>
        </div>
        
        <h1>🎉 Subscription Confirmed!</h1>
        <p>Hi {{ user_name }},</p>
        <p>Welcome to PsychSync! Your subscription has been successfully activated.</p>
        
        <div style="background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin: 20px 0;">
            {{ plan_name }} Plan
        </div>
        
        <div style="background: #eff6ff; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6;">
            <h3>Billing Details</h3>
            <p><strong>Plan:</strong> {{ plan_name }}</p>
            <p><strong>Amount:</strong> ${{ amount }}/{{ billing_cycle }}</p>
            <p><strong>Next Billing Date:</strong> {{ next_billing_date }}</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ dashboard_link }}" style="display: inline-block; padding: 12px 30px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">
                Access Your Dashboard
            </a>
        </div>
        
        <p style="text-align: center; color: #6b7280; font-size: 14px; margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
            © 2025 PsychSync AI. All rights reserved.
        </p>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✓ subscription_confirmation.html created${NC}"

# ============================================================================
# Legal/Docs Pages (NEW - not duplicates)
# ============================================================================
echo -e "${BLUE}⚖️ Creating legal documentation...${NC}"

# gdpr_compliance.html (NEW)
cat > app/templates/docs/gdpr_compliance.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GDPR Compliance - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px;">
    <h1>🇪🇺 GDPR Compliance Documentation</h1>
    <p><strong>Last Updated:</strong> January 2025</p>
    
    <h2>Your Rights Under GDPR</h2>
    <ul>
        <li>Right to Access</li>
        <li>Right to Rectification</li>
        <li>Right to Erasure</li>
        <li>Right to Data Portability</li>
        <li>Right to Object</li>
    </ul>
    
    <p>Contact our DPO: <a href="mailto:dpo@psychsync.ai">dpo@psychsync.ai</a></p>
</body>
</html>
EOF

# cookies.html (NEW)
cat > frontend/public/legal/cookies.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cookie Policy - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px;">
    <h1>🍪 Cookie Policy</h1>
    <p><strong>Effective Date:</strong> January 1, 2025</p>
    
    <h2>What Are Cookies?</h2>
    <p>Cookies are small text files stored on your device when you visit a website.</p>
    
    <h2>Types of Cookies We Use</h2>
    <ul>
        <li><strong>Essential Cookies:</strong> Required for site functionality</li>
        <li><strong>Analytics Cookies:</strong> Help us improve our service</li>
        <li><strong>Marketing Cookies:</strong> Only with your consent</li>
    </ul>
    
    <div style="text-align: center; margin: 30px 0;">
        <button style="padding: 10px 20px; background: #6366f1; color: white; border: none; border-radius: 6px;">
            Manage Cookie Preferences
        </button>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✓ gdpr_compliance.html created${NC}"
echo -e "${GREEN}✓ cookies.html created${NC}"

# ============================================================================
# Marketing Pages (NEW - not duplicates with React app)
# ============================================================================
echo -e "${BLUE}🎯 Creating marketing pages...${NC}"

# features.html (NEW - static for SEO)
cat > frontend/public/marketing/features.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Features - PsychSync AI</title>
    <meta name="description" content="Discover powerful features for team optimization">
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; text-align: center;">
        <h1 style="font-size: 48px; margin: 0;">Powerful Features</h1>
        <p style="font-size: 20px;">Everything you need for high-performance teams</p>
    </div>
    
    <div style="max-width: 1200px; margin: 60px auto; padding: 0 20px;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px;">
            <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 48px; margin-bottom: 15px;">🧠</div>
                <h3>Multi-Framework Assessments</h3>
                <p>MBTI, Big Five, Enneagram, DISC, and more</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 48px; margin-bottom: 15px;">🤖</div>
                <h3>AI-Powered Optimization</h3>
                <p>Machine learning for team composition</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 48px; margin-bottom: 15px;">📊</div>
                <h3>Real-Time Analytics</h3>
                <p>Beautiful, interactive dashboards</p>
            </div>
        </div>
    </div>
    
    <div style="background: #f9fafb; padding: 60px 20px; text-align: center;">
        <h2>Ready to Get Started?</h2>
        <a href="/register" style="display: inline-block; padding: 15px 40px; background: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px;">
            Start Free Trial
        </a>
    </div>
</body>
</html>
EOF

# case-studies.html (NEW)
cat > frontend/public/marketing/case-studies.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Case Studies - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f9fafb;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; text-align: center;">
        <h1>Customer Success Stories</h1>
    </div>
    
    <div style="max-width: 1100px; margin: 40px auto; padding: 0 20px;">
        <div style="background: white; padding: 40px; margin-bottom: 30px; border-radius: 12px;">
            <h2>TechCorp: 67% Reduction in Team Conflicts</h2>
            <p>Learn how TechCorp transformed their engineering team...</p>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: bold; color: #6366f1;">67%</div>
                    <div style="color: #6b7280;">Less Conflicts</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: bold; color: #6366f1;">89%</div>
                    <div style="color: #6b7280;">Satisfaction</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: bold; color: #6366f1;">34%</div>
                    <div style="color: #6b7280;">Faster Velocity</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: bold; color: #6366f1;">$450K</div>
                    <div style="color: #6b7280;">Annual Savings</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF

# demo-request.html (NEW)
cat > frontend/public/marketing/demo-request.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Request a Demo - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px;">
        <h1>Request a Demo</h1>
        <p>See PsychSync AI in action</p>
        
        <form action="/api/v1/demo-request" method="POST">
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px;">Full Name *</label>
                <input type="text" name="fullName" required style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px;">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px;">Work Email *</label>
                <input type="email" name="email" required style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px;">
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px;">Company *</label>
                <input type="text" name="company" required style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px;">
            </div>
            
            <button type="submit" style="width: 100%; padding: 15px; background: #6366f1; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                Request Demo
            </button>
        </form>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✓ features.html created${NC}"
echo -e "${GREEN}✓ case-studies.html created${NC}"
echo -e "${GREEN}✓ demo-request.html created${NC}"

# ============================================================================
# Help/Support Pages (NEW)
# ============================================================================
echo -e "${BLUE}📚 Creating help pages...${NC}"

# getting-started.html (NEW)
cat > frontend/public/help/getting-started.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Getting Started - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
    <div style="background: #6366f1; color: white; padding: 40px 20px; text-align: center;">
        <h1>Getting Started with PsychSync AI</h1>
    </div>
    
    <div style="max-width: 900px; margin: 40px auto; padding: 0 20px;">
        <h2>Quick Start Guide</h2>
        
        <div style="background: #f9fafb; padding: 20px; margin: 20px 0; border-left: 4px solid #6366f1; border-radius: 4px;">
            <h3>Step 1: Create Your Account</h3>
            <p>Sign up at psychsync.ai/register</p>
        </div>
        
        <div style="background: #f9fafb; padding: 20px; margin: 20px 0; border-left: 4px solid #6366f1; border-radius: 4px;">
            <h3>Step 2: Complete Your First Assessment</h3>
            <p>Take a personality assessment (10 minutes)</p>
        </div>
        
        <div style="background: #f9fafb; padding: 20px; margin: 20px 0; border-left: 4px solid #6366f1; border-radius: 4px;">
            <h3>Step 3: Create Your Team</h3>
            <p>Set up your team and invite members</p>
        </div>
    </div>
</body>
</html>
EOF

# contact.html (NEW)
cat > frontend/public/help/contact.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact Support - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f9fafb;">
    <div style="background: #6366f1; color: white; padding: 40px 20px; text-align: center;">
        <h1>Contact Support</h1>
        <p>We're here to help!</p>
    </div>
    
    <div style="max-width: 900px; margin: 40px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div style="background: white; padding: 30px; border-radius: 8px; text-align: center;">
            <div style="font-size: 48px;">💬</div>
            <h3>Live Chat</h3>
            <p>9am-5pm PT</p>
            <a href="#" style="display: inline-block; padding: 10px 20px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">
                Start Chat
            </a>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 8px; text-align: center;">
            <div style="font-size: 48px;">📧</div>
            <h3>Email</h3>
            <p>Response within 4 hours</p>
            <a href="mailto:support@psychsync.ai" style="display: inline-block; padding: 10px 20px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">
                Email Us
            </a>
        </div>
        
        <div style="background: white; padding: 30px; border-radius: 8px; text-align: center;">
            <div style="font-size: 48px;">📞</div>
            <h3>Phone</h3>
            <p>+1 (555) 123-4567</p>
            <a href="tel:+15551234567" style="display: inline-block; padding: 10px 20px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">
                Call Now
            </a>
        </div>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✓ getting-started.html created${NC}"
echo -e "${GREEN}✓ contact.html created${NC}"

# ============================================================================
# System Pages (NEW)
# ============================================================================
echo -e "${BLUE}⚙️ Creating system pages...${NC}"

# 503.html (NEW)
cat > static/503.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>503 Service Unavailable - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; padding: 20px;">
    <div style="text-align: center; background: white; padding: 60px 40px; border-radius: 12px; max-width: 600px;">
        <div style="font-size: 120px; font-weight: bold; color: #6366f1;">503</div>
        <h1>Service Temporarily Unavailable</h1>
        <p>We're experiencing technical difficulties. Service will be restored shortly.</p>
        <a href="https://status.psychsync.ai" style="display: inline-block; padding: 12px 30px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px;">
            Check System Status
        </a>
    </div>
</body>
</html>
EOF

# status.html (NEW)
cat > static/status.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>System Status - PsychSync AI</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f9fafb;">
    <div style="background: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="max-width: 1100px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 24px; font-weight: bold; color: #6366f1;">PsychSync AI</div>
            <div>System Status</div>
        </div>
    </div>
    
    <div style="max-width: 1100px; margin: 40px auto; padding: 0 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 40px;">
            <div style="font-size: 48px;">✅</div>
            <h1>All Systems Operational</h1>
            <p>Last updated: <span id="lastUpdate"></span></p>
        </div>
        
        <h2>Services</h2>
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; display: flex; justify-content: space-between;">
            <span>Web Application</span>
            <span style="color: #10b981; font-weight: bold;">● Operational</span>
        </div>
        
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; display: flex; justify-content: space-between;">
            <span>API Services</span>
            <span style="color: #10b981; font-weight: bold;">● Operational</span>
        </div>
        
        <div style="background: white; padding: 20px; margin: 10px 0; border-radius: 8px; display: flex; justify-content: space-between;">
            <span>AI Processing Engine</span>
            <span style="color: #10b981; font-weight: bold;">● Operational</span>
        </div>
    </div>
    
    <script>
        document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
EOF

echo -e "${GREEN}✓ 503.html created${NC}"
echo -e "${GREEN}✓ status.html created${NC}"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================================"
echo -e "${GREEN}✅ All HTML templates created successfully!${NC}"
echo "================================================"
echo ""
echo "Summary:"
echo "  📧 Email Templates: 1 (subscription_confirmation)"
echo "  ⚖️  Legal/Docs: 2 (gdpr_compliance, cookies)"
echo "  🎯 Marketing: 3 (features, case-studies, demo-request)"
echo "  📚 Help: 2 (getting-started, contact)"
echo "  ⚙️  System: 2 (503, status)"
echo ""
echo "Total: 10 new files created (no duplicates)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review and customize content for your needs"
echo "  2. Update placeholders ({{ variable }}) with your data"
echo "  3. Test all forms and links"
echo "  4. Deploy to production"
echo ""
echo "Done! 🎉"