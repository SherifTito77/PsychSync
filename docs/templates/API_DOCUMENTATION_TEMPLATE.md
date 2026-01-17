# API Documentation Template

> **Purpose:** Prevent documentation quality issues before they happen
> **Version:** 1.0
> **Created:** January 17, 2026
> **Usage:** Copy this template for all new API documentation

---

## 📋 Template Checklist

Use this checklist before publishing ANY API documentation:

### ✅ Section 1: Security (CRITICAL)
- [ ] No hardcoded credentials in examples (use `$VARIABLE` placeholders)
- [ ] All authentication examples use environment variables
- [ ] Security warnings included where applicable
- [ ] No production secrets in any code example
- [ ] API tokens/keys shown as `YOUR_API_TOKEN` or `$TOKEN`

### ✅ Section 2: Code Examples (CRITICAL)
- [ ] All code examples are syntactically valid
- [ ] Python examples have all functions defined or imported
- [ ] Bash scripts are complete and executable
- [ ] JSON examples validate against JSON schema
- [ ] cURL commands are tested and working
- [ ] No `TODO` or placeholder code in examples

### ✅ Section 3: Parameter Documentation
- [ ] All parameters documented with:
  - Type (string, integer, boolean, object, array)
  - Required/Optional status
  - Valid range or allowed values
  - Default value (if applicable)
  - Description of purpose
- [ ] Request body schemas provided
- [ ] Query parameters documented
- [ ] Path parameters documented

### ✅ Section 4: Error Responses
- [ ] 400 Bad Request example
- [ ] 401 Unauthorized example
- [ ] 404 Not Found example
- [ ] 500 Internal Server Error example
- [ ] Domain-specific errors (if applicable)
- [ ] Error response structure documented

### ✅ Section 5: Performance & Limits
- [ ] Rate limits documented (requests per minute/hour)
- [ ] Response time expectations (p50, p95, p99)
- [ ] Maximum request size
- [ ] Pagination parameters (if listing endpoints)
- [ ] Timeout values

### ✅ Section 6: Versioning & Compatibility
- [ ] API version specified
- [ ] Backward compatibility notes
- [ ] Deprecation warnings (if applicable)
- [ ] Breaking changes highlighted
- [ ] Migration guide for version changes

---

## 📝 Template Structure

Below is the complete template structure. Copy/paste and fill in the blanks.

---

# [Feature Name] API Documentation

## Overview
[Brief description of what this API does and when to use it]

## Base URL
```
[PROTOCOL]://[HOST]:[PORT]/api/v[VERSION]/[RESOURCE]
```

## Authentication
All endpoints require authentication. Include your JWT token:

```bash
export API_TOKEN="your_jwt_token_here"
curl -H "Authorization: Bearer $API_TOKEN" [URL]
```

### Getting Your Token
```bash
# NEVER hardcode credentials - use environment variables
curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}"
```

---

## Endpoints

### 1. [Endpoint Name]

**Description:** [What this endpoint does]

**Method:** `GET` | `POST` | `PUT` | `PATCH` | `DELETE`

**Endpoint:** `[PATH]`

**Authentication:** Required | Optional

---

#### Request Parameters

##### Query Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `param_name` | string | Yes | [Description] | `value` |
| `param_name2` | integer | No | [Description with valid range: 1-100] | `42` |

**Default Values:**
- `param_name2`: `10` (if not provided)

---

##### Request Body (for POST/PUT/PATCH)

```json
{
  "field1": "string value",
  "field2": 123,
  "field3": {
    "nested_field": "value"
  }
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field1` | string | Yes | [Description] |
| `field2` | integer | Yes | [Description with valid range: 1-1000] |
| `field3` | object | No | [Description] |

---

#### Example Request

```bash
curl -X POST $API_URL/[PATH] \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "value1",
    "field2": 123
  }'
```

---

#### Response

**Success Response:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "created_at": "2024-01-17T12:00:00Z"
  }
}
```

---

#### Error Responses

**400 Bad Request**
```json
{
  "error_code": "VAL_3001",
  "message": "Invalid request parameter",
  "details": {
    "field": "param_name",
    "issue": "Must be between 1 and 100"
  }
}
```

**401 Unauthorized**
```json
{
  "error_code": "AUTH_2001",
  "message": "Invalid or expired token",
  "details": {
    "action": "Refresh your token"
  }
}
```

**404 Not Found**
```json
{
  "error_code": "BIZ_4100",
  "message": "Resource not found",
  "details": {
    "resource_id": "123"
  }
}
```

**500 Internal Server Error**
```json
{
  "error_code": "SYS_5001",
  "message": "Internal server error",
  "details": {
    "request_id": "req_abc123",
    "action": "Contact support if persists"
  }
}
```

---

#### Rate Limiting

- **Limit:** 100 requests per minute
- **Headers Returned:**
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: 95
  - `X-RateLimit-Reset`: 1705480800

**When Rate Limited:**
```json
{
  "error_code": "AUTH_4001",
  "message": "Rate limit exceeded",
  "details": {
    "retry_after": 60,
    "limit": 100
  }
}
```

---

#### Performance Expectations

- **Average Response Time:** 150ms (p50)
- **95th Percentile:** 300ms (p95)
- **99th Percentile:** 500ms (p99)

---

#### Pagination (for List Endpoints)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (starts at 1) |
| `per_page` | integer | 20 | Items per page (1-100) |

**Response Headers:**
- `X-Total-Count`: 1234
- `X-Total-Pages`: 62
- `X-Current-Page`: 1

---

## Python Client Example

```python
import requests
import os
from typing import Dict, Any

# ALWAYS use environment variables
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN")

def call_endpoint(param1: str, param2: int) -> Dict[str, Any]:
    """
    Call the endpoint with proper error handling

    Args:
        param1: Description of param1
        param2: Description of param2 (valid range: 1-100)

    Returns:
        Dict containing the response data

    Raises:
        ValueError: If parameters are invalid
        requests.HTTPError: If API call fails
    """
    if not 1 <= param2 <= 100:
        raise ValueError(f"param2 must be between 1 and 100, got {param2}")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "field1": param1,
        "field2": param2
    }

    response = requests.post(
        f"{API_URL}/[PATH]",
        headers=headers,
        json=payload,
        timeout=10  # Always set timeout
    )

    response.raise_for_status()
    return response.json()

# Example usage
if __name__ == "__main__":
    try:
        result = call_endpoint("value", 42)
        print(f"Success: {result}")
    except requests.HTTPError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
    except ValueError as e:
        print(f"Validation Error: {e}")
```

---

## JavaScript/TypeScript Client Example

```typescript
interface ApiResponse {
  success: boolean;
  data: {
    id: string;
    name: string;
    createdAt: string;
  };
}

interface ApiError {
  errorCode: string;
  message: string;
  details: Record<string, unknown>;
}

// ALWAYS use environment variables
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_TOKEN = process.env.REACT_APP_API_TOKEN;

async function callEndpoint(param1: string, param2: number): Promise<ApiResponse> {
  if (param2 < 1 || param2 > 100) {
    throw new Error(`param2 must be between 1 and 100, got ${param2}`);
  }

  const response = await fetch(`${API_URL}/[PATH]`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      field1: param1,
      field2: param2,
    }),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(`API Error: ${error.errorCode} - ${error.message}`);
  }

  return response.json();
}

// Example usage
try {
  const result = await callEndpoint('value', 42);
  console.log('Success:', result);
} catch (error) {
  console.error('Error:', error);
}
```

---

## Shell Script Example

```bash
#!/bin/bash
# example-script.sh

# NEVER hardcode credentials
set -euo pipefail

# Load environment variables
source .env 2>/dev/null || true

API_URL="${API_URL:-http://localhost:8000}"
API_TOKEN="${API_TOKEN:?Error: API_TOKEN environment variable not set}"

PARAM1="${1:?Error: param1 not provided}"
PARAM2="${2:?Error: param2 not provided}"

# Validate parameter
if ! [[ "$PARAM2" =~ ^[0-9]+$ ]] || [ "$PARAM2" -lt 1 ] || [ "$PARAM2" -gt 100 ]; then
  echo "Error: param2 must be between 1 and 100"
  exit 1
fi

# Make API call
response=$(curl -s -X POST "${API_URL}/[PATH]" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"field1\": \"${PARAM1}\", \"field2\": ${PARAM2}}")

# Check for errors
if echo "$response" | jq -e '.error' > /dev/null; then
  echo "API Error:"
  echo "$response" | jq '.'
  exit 1
fi

echo "Success:"
echo "$response" | jq '.'
```

---

## Testing Checklist

Before marking documentation as complete, test ALL examples:

- [ ] Copy/paste cURL examples and verify they work
- [ ] Run Python example and verify no errors
- [ ] Run TypeScript example and verify compilation
- [ ] Execute shell script with valid/invalid inputs
- [ ] Test error scenarios with invalid data
- [ ] Verify all error response examples match actual API behavior

---

## Additional Considerations

### Idempotency
- [ ] Document if endpoint is idempotent
- [ ] If POST/PATCH, provide idempotency key usage

### Webhooks
- [ ] If endpoint triggers webhooks, document event format
- [ ] Provide webhook signature verification

### Caching
- [ ] Document caching behavior
- [ ] List cache-control headers

### Monitoring
- [ ] Reference monitoring dashboards
- [ ] List relevant metrics/alarms

### Compliance
- [ ] GDPR considerations (if applicable)
- [ ] HIPAA considerations (if applicable)
- [ ] Data retention policies

---

## Changelog

### Version 1.0 (YYYY-MM-DD)
- Initial release
- [Description of features]

---

## Related Documentation

- [API Quick Start](../../QUICK_START.md)
- [Authentication Guide](../AUTHENTICATION.md)
- [Error Codes Reference](../developer/ERROR_CODE_QUICK_REFERENCE.md)
- [Rate Limiting Policy](../RATE_LIMITING.md)

---

## Support

**Questions?**
- API Documentation: `$API_URL/docs`
- Slack Channel: `#api-development`
- Email: `api-support@psychsync.com`

**Issues?**
- Bug Reports: [GitHub Issues](link to issues)
- Feature Requests: [GitHub Discussions](link to discussions)
- Emergency Contacts: [Runbook](link to runbook)
