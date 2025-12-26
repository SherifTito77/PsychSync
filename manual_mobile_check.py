#!/usr/bin/env python3
"""
Manual Mobile Viewport Testing Script
Tests basic mobile usability without browser automation

Usage: python manual_mobile_check.py
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set

def test_page_load(base_url: str, route: str) -> Dict:
    """Test if a page loads successfully"""
    try:
        import requests
        url = f"{base_url.rstrip('/')}/{route.lstrip('/')}"
        response = requests.get(url, timeout=10)

        return {
            "url": url,
            "status_code": response.status_code,
            "loads_successfully": response.status_code == 200,
            "content_length": len(response.content),
            "has_viewport_meta": 'width=device-width' in response.text,
            "has_responsive_meta": 'responsive' in response.text.lower(),
        }
    except Exception as e:
        return {
            "url": f"{base_url.rstrip('/')}/{route.lstrip('/')}",
            "status_code": 0,
            "loads_successfully": False,
            "content_length": 0,
            "has_viewport_meta": False,
            "has_responsive_meta": False,
            "error": str(e)
        }

def analyze_css_for_responsive_patterns() -> Dict:
    """Analyze CSS files for responsive patterns"""
    css_dir = Path("frontend/src")
    responsive_indicators = {
        "media_queries": 0,
        "flexbox_usage": 0,
        "grid_usage": 0,
        "responsive_units": 0,
        "mobile_breakpoints": set(),
        "issues": []
    }

    css_files = list(css_dir.rglob("*.css")) + list(css_dir.rglob("*.scss"))

    for css_file in css_files:
        try:
            content = css_file.read_text()

            # Count media queries
            media_queries = len(re.findall(r'@media[^{]+\{', content))
            responsive_indicators["media_queries"] += media_queries

            # Extract breakpoints
            bp_matches = re.findall(r'(\d+)px', content)
            for bp in bp_matches:
                bp_int = int(bp)
                if 320 <= bp_int <= 768:  # Mobile range
                    responsive_indicators["mobile_breakpoints"].add(bp_int)

            # Check for flexbox and grid
            responsive_indicators["flexbox_usage"] += len(re.findall(r'display:\s*flex', content))
            responsive_indicators["grid_usage"] += len(re.findall(r'display:\s*grid', content))

            # Check for responsive units
            responsive_indicators["responsive_units"] += len(re.findall(r'(vw|vh|vmin|vmax|rem|em)', content))

            # Look for problematic patterns
            if re.search(r'overflow:\s*auto', content):
                responsive_indicators["issues"].append(f"Potential overflow in {css_file.name}")

        except Exception as e:
            responsive_indicators["issues"].append(f"Error analyzing {css_file.name}: {e}")

    responsive_indicators["mobile_breakpoints"] = sorted(list(responsive_indicators["mobile_breakpoints"]))
    return responsive_indicators

def check_critical_pages_mobile_readiness() -> Dict:
    """Check critical pages for mobile readiness"""
    base_url = "http://localhost:5173"

    critical_routes = [
        ("/", "Landing Page"),
        ("/login", "Login"),
        ("/register", "Register"),
        ("/dashboard", "Dashboard"),
        ("/teams", "Teams"),
        ("/assessments", "Assessments"),
        ("/settings", "Settings"),
    ]

    results = {}

    print("🔍 Testing critical pages at 375px width simulation...")

    for route, name in critical_routes:
        print(f"  Testing {name}: {route}")

        # Test page load
        page_result = test_page_load(base_url, route)
        page_result["name"] = name
        page_result["route"] = route

        # Analyze the page content for mobile issues
        if page_result["loads_successfully"]:
            try:
                import requests
                response = requests.get(f"{base_url.rstrip('/')}/{route.lstrip('/')}")
                content = response.text

                # Check for mobile-friendly indicators
                mobile_analysis = {
                    "has_mobile_nav": "mobile-menu" in content.lower(),
                    "has_touch_friendly": "touch" in content.lower(),
                    "has_responsive_images": "srcset" in content,
                    "has_fixed_widths": len(re.findall(r'width:\s*\d+px', content)) > 0,
                    "has_responsive_grid": "grid-cols-" in content or "md:grid-cols-" in content,
                    "has_mobile_padding": "px-4" in content or "p-4" in content,
                }

                page_result.update(mobile_analysis)

                # Calculate mobile score
                mobile_score = 0
                max_score = 7

                if page_result.get("has_viewport_meta", False):
                    mobile_score += 2
                if page_result.get("has_mobile_nav", False):
                    mobile_score += 1
                if page_result.get("has_responsive_grid", False):
                    mobile_score += 1
                if page_result.get("has_mobile_padding", False):
                    mobile_score += 1
                if not page_result.get("has_fixed_widths", False):
                    mobile_score += 1
                if page_result.get("has_responsive_images", False):
                    mobile_score += 1

                page_result["mobile_score"] = mobile_score
                page_result["mobile_score_percent"] = round((mobile_score / max_score) * 100, 1)

            except Exception as e:
                page_result["mobile_score"] = 0
                page_result["mobile_score_percent"] = 0
                page_result["analysis_error"] = str(e)

        results[name] = page_result

    return results

def generate_recommendations(critical_pages: Dict, css_analysis: Dict) -> List[Dict]:
    """Generate mobile optimization recommendations"""
    recommendations = []

    # Analyze critical pages
    failing_pages = [name for name, data in critical_pages.items()
                    if data.get("mobile_score_percent", 0) < 70]

    if failing_pages:
        recommendations.append({
            "priority": "critical",
            "category": "pages",
            "description": f"{len(failing_pages)} critical pages have poor mobile readiness",
            "affected_pages": failing_pages,
            "solution": "Implement responsive design patterns for these core pages"
        })

    # Check CSS responsiveness
    if css_analysis["media_queries"] < 10:
        recommendations.append({
            "priority": "high",
            "category": "css",
            "description": f"Only {css_analysis['media_queries']} media queries found",
            "solution": "Add responsive breakpoints at 375px, 414px, and 768px"
        })

    if len(css_analysis["mobile_breakpoints"]) < 3:
        recommendations.append({
            "priority": "high",
            "category": "breakpoints",
            "description": "Insufficient mobile breakpoints defined",
            "solution": "Define breakpoints for: 320px (very small), 375px (iPhone SE), 414px (iPhone Pro)"
        })

    # Check for fixed width issues
    pages_with_fixed_widths = [name for name, data in critical_pages.items()
                              if data.get("has_fixed_widths", False)]

    if pages_with_fixed_widths:
        recommendations.append({
            "priority": "medium",
            "category": "layout",
            "description": f"Pages with fixed widths that break mobile: {', '.join(pages_with_fixed_widths)}",
            "solution": "Replace fixed widths with responsive units or max-width constraints"
        })

    # Check for viewport meta
    pages_without_viewport = [name for name, data in critical_pages.items()
                             if not data.get("has_viewport_meta", False)]

    if pages_without_viewport:
        recommendations.append({
            "priority": "critical",
            "category": "viewport",
            "description": f"Pages missing viewport meta: {', '.join(pages_without_viewport)}",
            "solution": "Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        })

    # Add positive recommendations if doing well
    all_pages_good = all(data.get("mobile_score_percent", 0) >= 80 for data in critical_pages.values())
    if all_pages_good:
        recommendations.append({
            "priority": "info",
            "category": "overall",
            "description": "All critical pages have good mobile readiness",
            "solution": "Continue monitoring and test on real devices"
        })

    return recommendations

def main():
    """Main testing function"""
    print("📱 Manual Mobile Viewport Usability Testing")
    print("=" * 50)
    print("Testing without browser automation...")
    print()

    # Test critical pages
    critical_pages = check_critical_pages_mobile_readiness()

    # Analyze CSS
    print("\n🎨 Analyzing CSS for responsive patterns...")
    css_analysis = analyze_css_for_responsive_patterns()

    # Generate recommendations
    recommendations = generate_recommendations(critical_pages, css_analysis)

    # Print results
    print("\n📊 CRITICAL PAGES MOBILE READINESS")
    print("-" * 40)

    total_score = 0
    page_count = 0

    for name, data in critical_pages.items():
        if data.get("loads_successfully", False):
            score = data.get("mobile_score_percent", 0)
            total_score += score
            page_count += 1

            score_emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"{score_emoji} {name}: {score}% mobile ready")

            # Show issues
            if score < 80:
                issues = []
                if not data.get("has_viewport_meta", False):
                    issues.append("no viewport meta")
                if data.get("has_fixed_widths", False):
                    issues.append("fixed widths")
                if not data.get("has_mobile_nav", False):
                    issues.append("no mobile nav")

                if issues:
                    print(f"    Issues: {', '.join(issues)}")
        else:
            print(f"❌ {name}: Failed to load ({data.get('status_code', 'unknown')})")

    if page_count > 0:
        overall_score = round(total_score / page_count, 1)
        print(f"\n🎯 OVERALL MOBILE READINESS: {overall_score}%")

    # CSS Analysis
    print(f"\n🎨 CSS RESPONSIVENESS ANALYSIS")
    print(f"   Media Queries: {css_analysis['media_queries']}")
    print(f"   Mobile Breakpoints: {css_analysis['mobile_breakpoints']}")
    print(f"   Flexbox Usage: {css_analysis['flexbox_usage']}")
    print(f"   Grid Usage: {css_analysis['grid_usage']}")

    # Recommendations
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS")
        for rec in recommendations:
            priority_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "ℹ️",
                "low": "💡",
                "info": "✅"
            }
            print(f"   {priority_emoji.get(rec['priority'], '•')} {rec['description']}")
            print(f"      → {rec['solution']}")

    # Save detailed report
    report = {
        "timestamp": "2025-12-02",
        "overall_score": overall_score if page_count > 0 else 0,
        "critical_pages": critical_pages,
        "css_analysis": css_analysis,
        "recommendations": recommendations
    }

    report_file = Path("manual_mobile_test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()