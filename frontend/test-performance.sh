#!/bin/bash
# Quick performance test for the frontend

echo "🧪 Testing Frontend Performance..."
echo ""

# Test 1: Server is running
echo "1️⃣ Checking if server is running..."
if curl -s http://localhost:5005/ > /dev/null; then
    echo "   ✅ Server is running on port 5005"
else
    echo "   ❌ Server is not responding"
    exit 1
fi

# Test 2: Page loads without errors
echo ""
echo "2️⃣ Checking page load..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5005/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Page loads successfully (HTTP 200)"
else
    echo "   ❌ Page load failed (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 3: Check response time
echo ""
echo "3️⃣ Measuring response time..."
TTFB=$(curl -s -o /dev/null -w "%{time_starttransfer}" http://localhost:5005/)
if (( $(echo "$TTFB < 3.0" | bc -l) )); then
    echo "   ✅ Time to First Byte: ${TTFB}s (good)"
else
    echo "   ⚠️  Time to First Byte: ${TTFB}s (slow, but might be dev mode)"
fi

# Test 4: Check JavaScript bundle
echo ""
echo "4️⃣ Checking JavaScript bundle..."
if curl -s http://localhost:5005/ | grep -q "script"; then
    echo "   ✅ JavaScript bundle is present"
else
    echo "   ❌ JavaScript bundle not found"
fi

# Test 5: Verify main app files
echo ""
echo "5️⃣ Verifying key components..."
if [ -f "src/App.tsx" ]; then
    echo "   ✅ App.tsx exists"
else
    echo "   ❌ App.tsx missing"
fi

if [ -f "src/components/layout/DashboardLayout.tsx" ]; then
    echo "   ✅ DashboardLayout.tsx exists"
else
    echo "   ❌ DashboardLayout.tsx missing"
fi

if [ -f "src/components/layout/Sidebar.tsx" ]; then
    echo "   ✅ Sidebar.tsx exists"
else
    echo "   ❌ Sidebar.tsx missing"
fi

echo ""
echo "✅ Basic performance tests complete!"
echo ""
echo "📊 For detailed performance metrics, open browser console and run:"
echo "   perfDiagnostics.generateReport()"
