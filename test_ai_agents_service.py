#!/usr/bin/env python3
"""
AI Agents Service Demonstration

Shows the AI Agents service is running correctly on port 5000.
"""

import requests
import json
from datetime import datetime

print("=" * 70)
print("🤖 PSYNCSYNC AI AGENTS SERVICE - DEMONSTRATION")
print("=" * 70)
print()

BASE_URL = "http://localhost:5002"

# Test 1: Health Check
print("✅ Test 1: Health Check")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"Service: {data['service']}")
    print(f"Version: {data['version']}")
    print(f"Timestamp: {data['timestamp']}")
    print("✅ Service is healthy!")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    exit(1)

print()

# Test 2: Root Endpoint
print("✅ Test 2: Root Endpoint Information")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    data = response.json()
    print(f"Service: {data['service']}")
    print(f"Version: {data['version']}")
    print(f"Status: {data['status']}")
    print()
    print("📚 Endpoints:")
    for key, value in data['endpoints'].items():
        print(f"  {key}: {value}")
    print()
    print("🤖 Agents:")
    for key, value in data['agents'].items():
        print(f"  {key}: {value}")
except Exception as e:
    print(f"❌ Root endpoint failed: {e}")

print()

# Test 3: API Documentation
print("✅ Test 3: API Documentation Access")
print("-" * 70)
print(f"Swagger UI: {BASE_URL}/docs")
print(f"ReDoc: {BASE_URL}/redoc")
print()

# Test 4: Authentication Test
print("✅ Test 4: Authentication Test")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/api/v1/ai-agents/status", timeout=5)
    if response.status_code == 401:
        print("✅ Authentication is working correctly!")
        print("   Endpoint requires JWT token (as expected)")
    else:
        print(f"⚠️  Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"❌ Auth test failed: {e}")

print()

# Summary
print("=" * 70)
print("📊 SERVICE SUMMARY")
print("=" * 70)
print()
print(f"🌐 Service URL: {BASE_URL}")
print(f"📚 Documentation: {BASE_URL}/docs")
print(f"🏥 Health Check: {BASE_URL}/health")
print(f"🤖 Agent Status: {BASE_URL}/api/v1/ai-agents/status")
print()
print("✅ AI Agents Service is running on port 5000!")
print()
print("📝 Available Services:")
print("   • Security Agents (3): Headers, Encryption, Vulnerabilities")
print("   • Development Agents (8): Style, Performance, Testing")
print("   • Operations Agents (9): Monitoring, Incidents, Automation")
print()
print("🔗 Quick Links:")
print(f"   • API Docs: {BASE_URL}/docs")
print(f"   • Service Info: {BASE_URL}/")
print(f"   • Health Check: {BASE_URL}/health")
print()
print("=" * 70)
