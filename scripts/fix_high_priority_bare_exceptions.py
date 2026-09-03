#!/usr/bin/env python3
"""
Targeted fix for HIGH priority bare exception handlers.

This script fixes specific files that were identified in the analysis.
"""

import re
from pathlib import Path


def fix_file(file_path: Path) -> int:
    """Fix bare exceptions in a single file. Returns number of fixes."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines(keepends=True)
    except Exception:
        return 0

    fixes_count = 0

    for i, line in enumerate(lines):
        except (OSError, IOError, ValueError) as e:
        if re.search(r'except\s*:\s*$', line):
            # Get context (previous 5 lines)
            context_start = max(0, i - 5)
            context = ''.join(lines[context_start:i + 2]).lower()

            # Determine appropriate exception type based on context
            if '.json()' in context or 'json.loads' in context or 'json.dump' in context:
                new_exception = 'except Exception as e:'
            elif any(kw in context for kw in ['requests.', 'response.', 'httpx.', 'fetch(', 'async def']):
                new_exception = 'except Exception as e:'
            elif any(kw in context for kw in ['session.execute', 'db.execute', '.fetch', '.commit']):
                new_exception = 'except Exception as e:'
            elif any(kw in context for kw in ['open(', 'file.read', 'file.write']):
                new_exception = 'except (OSError, IOError) as e:'
            else:
                new_exception = 'except Exception as e:'

            # Get indentation
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + new_exception + '\n'

            # Apply fix
            lines[i] = new_line
            fixes_count += 1
            print(f"  ✓ Fixed {file_path.name}:{i + 1}")

    # Write back
    if fixes_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return fixes_count


def main():
    """Main entry point."""

    root_dir = Path(__file__).parent.parent

    # Target files from the analysis
    target_files = [
        "test_end_to_end_validation.py",
        "psychsync_platform_regression_suite.py",
        "comprehensive_rate_limiting_tests.py",
        "jwt_token_test_suite.py",
        "comprehensive_jwt_tests.py",
        "available_endpoints_test.py",
        "postman_test_runner.py",
        "test_dashboard_widgets.py",
        "simple_gdpr_test.py",
        "quick_api_test.py",
        "api_security_test_suite.py",
        "nosql_injection_tester.py",
        "update_all_remaining_assessments.py",
        "advanced_business_logic_attacks.py",
        "clear_mbti_cache.py",
        "test_live_validation.py",
        "live_permission_demo.py",
        "internal_api_security_test.py",
        "tests/pwa_comprehensive_test_suite.py",
        "tests/integration_test_runner.py",
        "app/api/v1/endpoints/health.py",
        "app/services/ai_enhanced_analytics.py",
    ]

    print("🔧 Fixing HIGH priority bare exception handlers...\n")

    total_fixes = 0

    for file_name in target_files:
        for py_file in root_dir.rglob(file_name):
            if py_file.is_file():
                print(f"📄 Processing: {py_file.relative_to(root_dir)}")
                fixes = fix_file(py_file)
                total_fixes += fixes
                if fixes > 0:
                    print(f"   Applied {fixes} fix(es)\n")
                break  # Only fix first match

    print(f"\n✅ Complete! Applied {total_fixes} fixes")
    print("\n📊 Summary:")
    print(f"   • Fixed bare 'except:' clauses")
    print(f"   • Replaced with context-appropriate exception types")
    print(f"   • Programs can now be safely interrupted with Ctrl+C")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
