# Bare Exception Handler Analysis Report

**Total findings:** 217


## By Severity

- **CRITICAL**: 4 occurrences
- **HIGH**: 55 occurrences
- **MEDIUM**: 130 occurrences
- **LOW**: 28 occurrences

## By Category

- **api**: 52 occurrences
- **database**: 3 occurrences
- **file_ops**: 14 occurrences
- **other**: 116 occurrences
- **security**: 4 occurrences
- **test**: 28 occurrences

## Top Files With Most Issues

- /Users/sheriftito/Downloads/psychsync/execute_comprehensive_uat.py: 8 issues
- /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py: 8 issues
- /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py: 7 issues
- /Users/sheriftito/Downloads/psychsync/simple_cve_scanner.py: 6 issues
- /Users/sheriftito/Downloads/psychsync/mobile_viewport_testing.py: 5 issues
- /Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/health.py: 5 issues
- /Users/sheriftito/Downloads/psychsync/comprehensive_devops_security_scanner.py: 4 issues
- /Users/sheriftito/Downloads/psychsync/security_enhancement_suite.py: 4 issues
- /Users/sheriftito/Downloads/psychsync/scripts/session_security_tester.py: 4 issues
- /Users/sheriftito/Downloads/psychsync/ai_agents/specialized_agents.py: 4 issues

## Critical & High Priority Details


### /Users/sheriftito/Downloads/psychsync/comprehensive_database_security_tests.py:369
**Severity:** critical | **Category:** security
**Suggested fix:** `except Exception as e:`
```
                            if b'CREATE TABLE' in decoded or b'INSERT INTO' in decoded:
                                is_encrypted = False
                                backup_info["issues"].append("Base64 encoded backup - not true encryption")
                        except:
                            pass

                    backup_info["encrypted"] = is_encrypted
```

### /Users/sheriftito/Downloads/psychsync/backup_encryption_tester.py:116
**Severity:** critical | **Category:** security
**Suggested fix:** `except Exception as e:`
```
                    if any(keyword in text_content.lower() for keyword in ["password", "secret", "key", "token"]):
                        result["security_issues"].append("Unencrypted backup contains sensitive keywords")
                        result["risk_level"] = "HIGH"
                except:
                    pass

            # Check file permissions
```

### /Users/sheriftito/Downloads/psychsync/tests/security/test_security_suite.py:163
**Severity:** critical | **Category:** security
**Suggested fix:** `except Exception as e:`
```
                            print(f"  ⚠ WARN: Token expiry too long ({exp_minutes:.0f} minutes)")
                        else:
                            print(f"  ✓ PASS: Token expiry appropriate ({exp_minutes:.0f} minutes)")
                except:
                    print("  ⊘ SKIP: Could not verify token expiry")
        else:
            print("  ⊘ SKIP: Could not test JWT security")
```

### /Users/sheriftito/Downloads/psychsync/app/core/security_fixes.py:362
**Severity:** critical | **Category:** security
**Suggested fix:** `except Exception as e:`
```
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except:
        return False
```

### /Users/sheriftito/Downloads/psychsync/security_enhancement_suite.py:188
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        if 'stack' in str(error_data).lower() or 'traceback' in str(error_data).lower():
                            vulnerabilities.append("API may disclose sensitive error information")
                            security_score -= 15
                    except:
                        pass

            # Check CORS configuration
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:119
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        try:
                            error = response.json()
                            print(f"   Error: {error.get('detail', 'Unknown')}")
                        except:
                            pass
            else:  # expected_validation == "fail"
                if response.status_code == 422:
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:128
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        error = response.json()
                        error_msg = error.get('detail', 'Unknown validation error')
                        print(f"   Status: Correctly rejected - {error_msg}")
                    except:
                        print(f"   Status: Correctly rejected")
                else:
                    print(f"❌ {test['name']}")
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:137
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        try:
                            error = response.json()
                            print(f"   Unexpected: {error.get('detail', 'Unknown')}")
                        except:
                            pass

        except requests.exceptions.RequestException as e:
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:184
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        print("   ✅ Fixed error message format detected!")
                        print("   ✅ Multiple validation errors aggregated correctly!")

            except:
                print(f"   Raw error response: {response.text}")

    except requests.exceptions.RequestException as e:
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:202
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            print("✅ Swagger UI documentation accessible")
        else:
            print(f"⚠️  Docs returned status: {docs_response.status_code}")
    except:
        print("❌ Could not access documentation")

    try:
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:217
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                pass
        else:
            print(f"⚠️  OpenAPI returned status: {openapi_response.status_code}")
    except:
        print("❌ Could not access OpenAPI specification")

    print()
```

### /Users/sheriftito/Downloads/psychsync/test_end_to_end_validation.py:213
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                openapi_data = openapi_response.json()
                schema_count = len(openapi_data.get('components', {}).get('schemas', {}))
                print(f"   Schemas defined: {schema_count}")
            except:
                pass
        else:
            print(f"⚠️  OpenAPI returned status: {openapi_response.status_code}")
```

### /Users/sheriftito/Downloads/psychsync/psychsync_platform_regression_suite.py:179
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    health_data = response.json() if response.content else {}
                    dependencies = health_data.get("dependencies", {})
                except:
                    pass

                health_check = PlatformHealthCheck(
```

### /Users/sheriftito/Downloads/psychsync/psychsync_platform_regression_suite.py:700
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                            try:
                                data = response.json()
                                print(f"✅ {endpoint}: Valid JSON response")
                            except:
                                print(f"⚠️  {endpoint}: Invalid JSON response")
                        else:
                            print(f"⚠️  {endpoint}: Non-JSON response type: {content_type}")
```

### /Users/sheriftito/Downloads/psychsync/psychsync_platform_regression_suite.py:767
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    data = response.json() if response.content else {}
                    data_validated = True
                except:
                    data_validated = True  # Some endpoints may return empty responses

                self.test_results.append(RegressionTestResult(
```

### /Users/sheriftito/Downloads/psychsync/comprehensive_rate_limiting_tests.py:52
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    health_json = response.json()
                    health_data["server_info"] = health_json
                except:
                    pass

            print(f"✅ Health check passed - {response.status_code} ({health_data['response_time']:.0f}ms)")
```

### /Users/sheriftito/Downloads/psychsync/jwt_token_test_suite.py:152
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```

                try:
                    response_data = await response.json()
                except:
                    response_data = {"raw_response": await response.text()}

                return TokenTestResult(
```

### /Users/sheriftito/Downloads/psychsync/comprehensive_jwt_tests.py:145
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```

                try:
                    response_data = await response.json()
                except:
                    response_data = {"raw_response": await response.text()}

                return response.status, response_time, response_data
```

### /Users/sheriftito/Downloads/psychsync/available_endpoints_test.py:97
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        print(f"   📄 Response keys: {list(data.keys())}")
                        if 'access_token' in data:
                            print(f"   🔑 Token found: {data['access_token'][:20]}...")
                    except:
                        print(f"   📄 Response: {response.text[:100]}...")
                elif response.status_code != 404:
                    print(f"   📄 Response: {response.text[:100]}...")
```

### /Users/sheriftito/Downloads/psychsync/postman_test_runner.py:128
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            # Parse response
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {'raw_response': response.text}

            return TestResult(
```

### /Users/sheriftito/Downloads/psychsync/test_dashboard_widgets.py:49
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    result["json_data"] = response.json()
                except:
                    result["json_data"] = None

            return result
```

### /Users/sheriftito/Downloads/psychsync/simple_gdpr_test.py:53
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            if response.status_code == 200:
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = "Invalid JSON"
            else:
                result["error"] = response.text[:200]
```

### /Users/sheriftito/Downloads/psychsync/simple_gdpr_test.py:83
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print("   Response: Invalid JSON format")
        else:
            print(f"❌ Public data summary endpoint: HTTP {response.status_code}")
```

### /Users/sheriftito/Downloads/psychsync/simple_gdpr_test.py:115
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                data = response.json()
                print(f"   Consent ID: {data.get('consent_id', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
            except:
                print("   Response: Invalid JSON format")
        else:
            print(f"❌ Cookie consent endpoint: HTTP {response.status_code}")
```

### /Users/sheriftito/Downloads/psychsync/quick_api_test.py:90
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                    response_json = response.json()
                    if "error" in response_json or "message" in response_json:
                        has_error_structure = True
                except:
                    pass

                status = "✅" if graceful and has_error_structure else "⚠️" if graceful else "❌"
```

### /Users/sheriftito/Downloads/psychsync/quick_api_test.py:105
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                            error_data = response.json()
                            if "message" in error_data:
                                print(f"    Message: {error_data['message'][:80]}...")
                        except:
                            pass
                else:
                    print(f"    ⚠️  Server error - needs investigation")
```

### /Users/sheriftito/Downloads/psychsync/api_security_test_suite.py:408
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                            is_vulnerable = True
                            print(f"  🚨 MASS ASSIGNMENT VULNERABILITY: Field '{field}' was accepted!")
                            break
                except:
                    pass  # JSON parse errors are not mass assignment vulnerabilities

            # Check if the request was rejected (good protection)
```

### /Users/sheriftito/Downloads/psychsync/api_security_test_suite.py:585
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                async with self.session.post(url, json={"test": "data"}) as post_response:
                    post_status = post_response.status
                    post_response_text = await post_response.text()
            except:
                post_status = None
                post_response_text = ""

```

### /Users/sheriftito/Downloads/psychsync/nosql_injection_tester.py:490
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
        """Analyze HTTP response for injection indicators"""
        try:
            data = await response.json()
        except:
            data = await response.text()

        # Check for injection success indicators
```

### /Users/sheriftito/Downloads/psychsync/update_all_remaining_assessments.py:271
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                print(f"   DISC API: {q_count} questions ✅")
            else:
                print(f"   DISC API: Error {response.status_code} ❌")
        except:
            print("   DISC API: Connection error ❌")

    # Update Social Styles
```

### /Users/sheriftito/Downloads/psychsync/update_all_remaining_assessments.py:288
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                print(f"   Social Styles API: {q_count} questions ✅")
            else:
                print(f"   Social Styles API: Error {response.status_code} ❌")
        except:
            print("   Social Styles API: Connection error ❌")

    print(f"\n🎉 COMPLETED UPDATING {success_count} ASSESSMENTS!")
```

### /Users/sheriftito/Downloads/psychsync/advanced_business_logic_attacks.py:387
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        try:
                            response_data = response.json()
                            current_resource_id = response_data.get('id')
                        except:
                            pass

                    workflow_results.append({
```

### /Users/sheriftito/Downloads/psychsync/clear_mbti_cache.py:53
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}")

    except Exception as e:
```

### /Users/sheriftito/Downloads/psychsync/test_live_validation.py:88
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    error_detail = response.json()
                    print(f"   Validation Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Raw Response: {response.text[:200]}...")
            elif response.status_code == 201:
                print(f"   ✅ Registration successful")
```

### /Users/sheriftito/Downloads/psychsync/live_permission_demo.py:121
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            # Parse response
            try:
                response_data = response.json() if response.content else None
            except:
                response_data = response.text[:200] if response.text else None

            # Determine if result matches expectations
```

### /Users/sheriftito/Downloads/psychsync/internal_api_security_test.py:182
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    response_data = response.json()
                    endpoint_result["response_data"] = json.dumps(response_data)[:200]  # Truncate
                except:
                    endpoint_result["response_data"] = response.text[:200]

            except requests.exceptions.RequestException as e:
```

### /Users/sheriftito/Downloads/psychsync/internal_api_security_test.py:295
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                try:
                    response_data = response.json()
                    exposure_result["response_data"] = json.dumps(response_data)[:200]
                except:
                    exposure_result["response_data"] = response.text[:200]

            except requests.exceptions.RequestException:
```

### /Users/sheriftito/Downloads/psychsync/tests/pwa_comprehensive_test_suite.py:375
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                response = requests.get(manifest_url, timeout=5)
                manifest_accessible = response.status_code == 200
                manifest_valid = response.headers.get('Content-Type', '').startswith('application/json')
            except:
                manifest_accessible = False
                manifest_valid = False

```

### /Users/sheriftito/Downloads/psychsync/tests/integration_test_runner.py:120
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                    if response.status == 200:
                        working_endpoints.append(endpoint)
            except:
                pass  # Skip failed endpoints

        duration = time.time() - start_time
```

### /Users/sheriftito/Downloads/psychsync/scripts/api_excellence_optimizer.py:504
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        rapid_requests.append((response.status, response_time))
                except:
                    rapid_requests.append((500, 5000))

            # If no 429 or 503 responses, rate limiting might be missing
```

### /Users/sheriftito/Downloads/psychsync/scripts/warm_cache.py:34
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=2)
        print(f"✅ Server is running (HTTP {response.status_code})")
    except:
        print("❌ Server not running! Start it first:")
        print("   uvicorn app.main:app --reload")
        return
```

### /Users/sheriftito/Downloads/psychsync/scripts/session_security_tester.py:380
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        if response.status_code != 200:
                            sessions_invalidated += 1
                            session_statuses[f"session_{i+1}"]["invalidated_by_logout"] = True
                    except:
                        pass

            # Step 4: Test session limit enforcement
```

### /Users/sheriftito/Downloads/psychsync/scripts/session_security_tester.py:572
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```

                    expired_response = expired_session.get(f"{self.base_url}/api/v1/me", timeout=10)
                    token_properly_expired = expired_response.status_code != 200
                except:
                    token_properly_expired = False
                    expired_token = None
            else:
```

### /Users/sheriftito/Downloads/psychsync/scripts/session_security_tester.py:706
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        "contains_stack_trace": "traceback" in error_response.text.lower(),
                        "contains_session_info": any(p in error_response.text.lower() for p in sensitive_patterns)
                    }
                except:
                    error_responses[endpoint] = {"error": "Request failed"}

            # Step 4: Test session ID predictability
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:414
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                elif response.status_code == 200:
                    # Possibly unprotected
                    unprotected_count += 1
            except:
                pass

        return {
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:449
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                if response.status_code in [400, 422]:
                    sanitized_count += 1

            except:
                pass

        return {
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:484
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                'content_length': len(content)
            }

        except:
            return {
                'sensitive_data_exposed': False,
                'error': 'Could not fetch content'
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:551
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                if response.status_code in [400, 422, 401] or 'error' in response.text.lower():
                    protected_count += 1

            except:
                protected_count += 1  # Connection error is better than vulnerability

        return {
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:586
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                if response.status_code in [400, 422] or payload not in response.text:
                    protected_count += 1

            except:
                protected_count += 1

        return {
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:618
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        rate_limited = True
                        break

            except:
                pass

            results['endpoint_tests'][endpoint] = {
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:645
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
            response = requests.get(f"{self.base_url}/privacy", timeout=5)
            results['has_privacy_policy'] = response.status_code == 200
            results['details']['privacy_policy_status'] = response.status_code
        except:
            results['details']['privacy_policy_status'] = 'error'

        # Check for GDPR compliance pages
```

### /Users/sheriftito/Downloads/psychsync/scripts/security_release_tests.py:658
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                if response.status_code == 200:
                    gdpr_found = True
                    break
            except:
                pass

        results['has_gdpr_compliance'] = gdpr_found
```

### /Users/sheriftito/Downloads/psychsync/scripts/monitoring_observability_system.py:907
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        for check_name, check_result in response_data['checks'].items():
                            if not check_result.get('passed', True):
                                issues.append(f"{check_name}: {check_result.get('message', 'Failed')}")
            except:
                pass

            if status == 'UNHEALTHY' and not issues:
```

### /Users/sheriftito/Downloads/psychsync/scripts/test_cache_auth.py:161
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=2)
        print(f"✅ Server is running (HTTP {response.status_code})")
    except:
        print("❌ Server not running! Start it first:")
        print("   uvicorn app.main:app --reload")
        return
```

### /Users/sheriftito/Downloads/psychsync/scripts/validate_pwa_staging.py:148
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                            endpoints_found += 1
                    except:
                        pass
        except:
            pass

        backend_results["pwa_endpoints"] = endpoints_found > 0
```

### /Users/sheriftito/Downloads/psychsync/scripts/validate_pwa_staging.py:146
**Severity:** high | **Category:** api
**Suggested fix:** `except Exception as e:`
```
                        response = await client.get(f"http://localhost:8000{endpoint}", timeout=5)
                        if response.status_code == 200:
                            endpoints_found += 1
                    except:
                        pass
        except:
            pass
```

### /Users/sheriftito/Downloads/psychsync/app/services/ai_enhanced_analytics.py:662
**Severity:** high | **Category:** database
**Suggested fix:** `except Exception as e:`
```
            params = {"org_id": organization_id, "team_id": team_id, "days": time_period_days}
            result = await self.db.execute(query, params)
            return [str(row[0]) for row in result.fetchall()]
        except:
            return []

    async def _serialize_insight(self, insight: AIInsight) -> dict[str, Any]:
```

### /Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/health.py:380
**Severity:** high | **Category:** database
**Suggested fix:** `except Exception as e:`
```
                else {"since_date": seven_days_ago},
            )
            active_users = active_users_result.scalar() or 0
        except:
            # Fallback if user_activity_log table doesn't exist
            active_users = 0

```

### /Users/sheriftito/Downloads/psychsync/app/api/v1/endpoints/health.py:441
**Severity:** high | **Category:** database
**Suggested fix:** `except Exception as e:`
```
                    (completed_assessments / max(total_assessments, 1)) * 100, 2
                ),
            }
        except:
            # Tables might not exist in development
            assessment_metrics = {
                "total_assessments": 0,
```
