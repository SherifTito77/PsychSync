
# Save this as test_endpoints.sh
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "Testing endpoints..."
echo ""

echo "1. Root:"
curl -s $BASE_URL/ | jq

echo ""
echo "2. Health:"
curl -s $BASE_URL/health | jq

echo ""
echo "3. Docs (should return HTML):"
curl -s -I $BASE_URL/api/docs | grep -i "content-type"

echo ""
echo "4. ReDoc (should return HTML):"
curl -s -I $BASE_URL/api/redoc | grep -i "content-type"

echo ""
echo "5. OpenAPI:"
curl -s $BASE_URL/api/openapi.json | jq '.info'