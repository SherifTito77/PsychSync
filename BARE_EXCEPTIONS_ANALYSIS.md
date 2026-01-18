# Bare Exception Handler Analysis Report

**Total findings:** 128


## By Severity

- **HIGH**: 6 occurrences
- **MEDIUM**: 103 occurrences
- **LOW**: 19 occurrences

## By Category

- **api**: 6 occurrences
- **file_ops**: 9 occurrences
- **other**: 94 occurrences
- **test**: 19 occurrences

## Top Files With Most Issues

- /Users/sheriftito/Downloads/psychsync/simple_cve_scanner.py: 6 issues
- /Users/sheriftito/Downloads/psychsync/monitoring/exporters/business_metrics_exporter.py: 4 issues
- /Users/sheriftito/Downloads/psychsync/ssh_brute_force_test.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/network_layer_security_audit.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/master_cicd_integration_pipeline_with_pwa.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/app/core/deployment_automation.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/app/services/log_aggregation_service.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/app/services/email_fetching_service.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/app/services/free_email_connector_service.py: 3 issues
- /Users/sheriftito/Downloads/psychsync/test_mbti_frontend_debug.py: 2 issues

## Critical & High Priority Details


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