#!/usr/bin/env python3
"""
Debug the MBTI frontend loading issues
"""
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_mbti_frontend_browser():
    """Test MBTI frontend using browser simulation"""
    print("🔍 Testing MBTI Frontend with Browser Simulation")
    print("=" * 60)

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        print("\n1. 🌐 Loading MBTI Assessment Page...")
        driver.get("http://localhost:5174/assessments/mbti/start")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("   ✅ Page loaded")

        # Check for loading spinner
        time.sleep(3)  # Wait for React to mount

        # Get page source
        page_source = driver.page_source

        print("\n2. 🔍 Analyzing Page Content...")

        # Look for key indicators
        checks = {
            "Loading skeleton": "Loading MBTI Assessment" in page_source,
            "React app": "React" in page_source or "root" in page_source,
            "Error message": "error" in page_source.lower() or "something went wrong" in page_source.lower(),
            "MBTI content": "MBTI" in page_source or "assessment" in page_source.lower(),
            "Questions": "question" in page_source.lower() or "At parties" in page_source,
            "Submit button": "submit" in page_source.lower() or "button" in page_source.lower()
        }

        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}: {result}")

        # Check for JavaScript errors
        print("\n3. 🐛 Checking for JavaScript Errors...")
        try:
            logs = driver.get_log('browser')
            js_errors = [log for log in logs if log['level'] == 'SEVERE']

            if js_errors:
                print(f"   ❌ Found {len(js_errors)} JavaScript errors:")
                for error in js_errors[:3]:  # Show first 3 errors
                    print(f"      • {error['message'][:100]}...")
            else:
                print("   ✅ No JavaScript errors detected")
        except Exception as e:
            print("   ⚠️  Could not access browser logs")

        # Check console
        print("\n4. 📊 Final Page State...")

        # Look for specific MBTI content
        if "At parties, do you:" in page_source:
            print("   ✅ MBTI Questions found!")
        elif "Loading MBTI Assessment" in page_source:
            print("   ⏳ Still loading (stuck in loading state)")
        elif "Something went wrong" in page_source:
            print("   ❌ Error state detected")
        else:
            print("   ⚠️  Unknown state - generic React app loaded")

        # Print a snippet of the page content
        print(f"\n5. 📄 Page Content Sample (first 500 chars):")
        content_preview = page_source[:500].replace('\n', ' ')
        print(f"   {content_preview}...")

        # Check if the MBTI component is being imported correctly
        if "MBTIAssessmentPage" in page_source:
            print("   ✅ MBTI component referenced in HTML")
        else:
            print("   ❌ MBTI component not found in HTML")

    except Exception as e:
        print(f"❌ Browser test failed: {e}")

    finally:
        try:
            driver.quit()
        except Exception as e:
            pass

def test_direct_api():
    """Test the API endpoints directly"""
    print("\n🔧 Testing API Endpoints Directly")
    print("=" * 40)

    try:
        # Test MBTI questions endpoint
        response = requests.get("http://localhost:8000/api/v1/assessment-questions/mbti")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Questions API: {data.get('success', False)}")
            print(f"📊 Question count: {len(data.get('assessment', {}).get('questions', []))}")

            # Show first question
            questions = data.get('assessment', {}).get('questions', [])
            if questions:
                print(f"❓ First question: {questions[0].get('question_text', 'N/A')}")
        else:
            print(f"❌ Questions API failed: {response.status_code}")

    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    test_direct_api()
    test_mbti_frontend_browser()
