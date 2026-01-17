#!/usr/bin/env python3
"""
Simple Mobile Viewport Analysis Script
Analyzes React components for mobile responsiveness patterns without requiring browser automation

Usage: python simple_mobile_check.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

def analyze_css_files() -> Dict:
    """Analyze CSS files for mobile responsiveness patterns"""
    css_dir = Path("frontend/src")
    results = {
        "responsive_patterns": {},
        "breakpoints": set(),
        "mobile_utilities": [],
        "potential_issues": []
    }

    # Find CSS and SCSS files
    css_files = list(css_dir.rglob("*.css")) + list(css_dir.rglob("*.scss"))

    responsive_patterns = {
        "media_queries": [],
        "mobile_first": [],
        "flexbox": [],
        "grid": [],
        "viewport_units": []
    }

    for css_file in css_files:
        try:
            content = css_file.read_text()

            # Check for media queries
            media_queries = re.findall(r'@media[^{]+\{', content)
            for mq in media_queries:
                responsive_patterns["media_queries"].append({
                    "file": str(css_file),
                    "query": mq.strip()
                })

                # Extract breakpoints
                bp_match = re.search(r'(\d+)px', mq)
                if bp_match:
                    results["breakpoints"].add(int(bp_match.group(1)))

            # Check for mobile-first patterns
            if "min-width" in content and "max-width" in content:
                responsive_patterns["mobile_first"].append(str(css_file))

            # Check for responsive units
            if re.search(r'(vw|vh|vmin|vmax)', content):
                responsive_patterns["viewport_units"].append(str(css_file))

            # Check for flexbox
            if "display:\s*flex" in content or "display:flex" in content:
                responsive_patterns["flexbox"].append(str(css_file))

            # Check for CSS Grid
            if "display:\s*grid" in content or "display:grid" in content:
                responsive_patterns["grid"].append(str(css_file))

        except Exception as e:
            print(f"Error reading {css_file}: {e}")

    results["responsive_patterns"] = responsive_patterns
    results["breakpoints"] = sorted(list(results["breakpoints"]))
    return results

def analyze_react_components() -> Dict:
    """Analyze React components for mobile responsiveness"""
    src_dir = Path("frontend/src")
    components = {}

    # Find all TSX files
    tsx_files = list(src_dir.rglob("*.tsx"))

    mobile_responsive_indicators = {
        "responsive_hooks": ["useWindowSize", "useMediaQuery", "useBreakpoint"],
        "responsive_props": ["mobile", "responsive", "viewport", "breakpoint"],
        "responsive_classes": ["mobile", "responsive", "sm:", "md:", "lg:", "xl:"],
        "touch_handlers": ["onTouchStart", "onTouchEnd", "onTouchMove"],
        "viewport_meta": ["viewport", "user-scalable", "width=device-width"]
    }

    for tsx_file in tsx_files:
        try:
            content = tsx_file.read_text()
            relative_path = str(tsx_file.relative_to(src_dir))

            component_analysis = {
                "file": relative_path,
                "uses_responsive_hooks": [],
                "uses_responsive_props": [],
                "uses_responsive_classes": [],
                "has_touch_handlers": [],
                "has_responsive_logic": False,
                "potential_issues": []
            }

            # Check for responsive patterns
            for hook in mobile_responsive_indicators["responsive_hooks"]:
                if hook in content:
                    component_analysis["uses_responsive_hooks"].append(hook)
                    component_analysis["has_responsive_logic"] = True

            # Check for responsive props
            for prop in mobile_responsive_indicators["responsive_props"]:
                if f"{prop}=" in content or f" {prop}:" in content:
                    component_analysis["uses_responsive_props"].append(prop)

            # Check for responsive class names
            for class_name in mobile_responsive_indicators["responsive_classes"]:
                if class_name in content:
                    component_analysis["uses_responsive_classes"].append(class_name)
                    component_analysis["has_responsive_logic"] = True

            # Check for touch handlers
            for handler in mobile_responsive_indicators["touch_handlers"]:
                if handler in content:
                    component_analysis["has_touch_handlers"].append(handler)

            # Look for potential mobile issues
            issues = []

            # Fixed widths (problematic for mobile)
            fixed_widths = re.findall(r'width:\s*\d+px', content)
            if fixed_widths:
                issues.extend([f"Fixed width found: {width}" for width in fixed_widths[:3]])

            # Hard-coded positions
            if re.search(r'(left|right|top|bottom):\s*\d+px', content):
                issues.append("Hard-coded positioning found")

            # Small touch targets
            small_buttons = re.findall(r'(height|width|size):\s*([1-3]\d)px', content)
            if small_buttons:
                issues.extend([f"Small touch target: {size}px" for _, size in small_buttons])

            component_analysis["potential_issues"] = issues[:3]  # Limit to top 3 issues

            components[relative_path] = component_analysis

        except Exception as e:
            print(f"Error analyzing {tsx_file}: {e}")

    return components

def check_tailwind_config() -> Dict:
    """Check Tailwind CSS configuration for mobile utilities"""
    tailwind_files = [
        "frontend/tailwind.config.js",
        "frontend/tailwind.config.ts",
        "frontend/postcss.config.js"
    ]

    config_analysis = {
        "found_configs": [],
        "mobile_breakpoints": [],
        "mobile_first": False,
        "has_touch_utilities": False
    }

    for config_file in tailwind_files:
        config_path = Path(config_file)
        if config_path.exists():
            config_analysis["found_configs"].append(config_file)

            try:
                content = config_path.read_text()

                # Look for mobile breakpoints
                bp_match = re.search(r'"?sm"?\s*:\s*[\'"]?(\d+)px', content)
                if bp_match:
                    config_analysis["mobile_breakpoints"].append(int(bp_match.group(1)))

                # Check for mobile-first configuration
                if "screens" in content and "sm" in content:
                    config_analysis["mobile_first"] = True

                # Check for touch utilities
                if any(keyword in content for keyword in ["touch", "tap", "mobile"]):
                    config_analysis["has_touch_utilities"] = True

            except Exception as e:
                print(f"Error reading {config_file}: {e}")

    return config_analysis

def check_viewport_meta() -> bool:
    """Check if index.html has proper viewport meta tag"""
    index_file = Path("frontend/index.html")

    if not index_file.exists():
        return False

    try:
        content = index_file.read_text()

        # Look for viewport meta tag
        viewport_match = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*>', content, re.IGNORECASE)
        if viewport_match:
            viewport_tag = viewport_match.group(0)

            # Check for mobile-friendly attributes
            has_width_device_width = "width=device-width" in viewport_tag
            has_user_scalable = "user-scalable" in viewport_tag

            return has_width_device_width
    except Exception as e:
        print(f"Error reading index.html: {e}")

    return False

def generate_mobile_report() -> Dict:
    """Generate comprehensive mobile responsiveness report"""
    print("🔍 Analyzing mobile responsiveness...")

    # Analyze different aspects
    css_analysis = analyze_css_files()
    component_analysis = analyze_react_components()
    tailwind_analysis = check_tailwind_config()
    has_viewport_meta = check_viewport_meta()

    # Calculate scores
    total_components = len(component_analysis)
    responsive_components = sum(1 for comp in component_analysis.values() if comp["has_responsive_logic"])
    mobile_responsive_rate = (responsive_components / total_components * 100) if total_components > 0 else 0

    # Count issues
    total_issues = sum(len(comp["potential_issues"]) for comp in component_analysis.values())
    components_with_issues = sum(1 for comp in component_analysis.values() if comp["potential_issues"])

    # Find most problematic components
    problematic_components = sorted(
        [(name, comp) for name, comp in component_analysis.items() if comp["potential_issues"]],
        key=lambda x: len(x[1]["potential_issues"]),
        reverse=True
    )[:5]

    # Find best practices examples
    good_examples = sorted(
        [(name, comp) for name, comp in component_analysis.items() if comp["has_responsive_logic"] and not comp["potential_issues"]],
        key=lambda x: len(x[1]["uses_responsive_classes"]) + len(x[1]["uses_responsive_hooks"]),
        reverse=True
    )[:5]

    report = {
        "summary": {
            "total_components_analyzed": total_components,
            "responsive_components": responsive_components,
            "mobile_responsive_rate": round(mobile_responsive_rate, 1),
            "total_issues_found": total_issues,
            "components_with_issues": components_with_issues,
            "has_viewport_meta": has_viewport_meta,
            "css_media_queries": len(css_analysis["responsive_patterns"]["media_queries"]),
            "breakpoints_defined": css_analysis["breakpoints"]
        },
        "css_analysis": css_analysis,
        "component_analysis": component_analysis,
        "tailwind_config": tailwind_analysis,
        "most_problematic_components": problematic_components,
        "best_practice_examples": good_examples,
        "recommendations": []
    }

    # Generate recommendations
    recommendations = []

    if not has_viewport_meta:
        recommendations.append({
            "priority": "critical",
            "category": "viewport",
            "description": "Add proper viewport meta tag to index.html",
            "code": '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        })

    if mobile_responsive_rate < 80:
        recommendations.append({
            "priority": "high",
            "category": "components",
            "description": f"Only {mobile_responsive_rate:.1f}% of components are mobile-responsive",
            "code": "Implement responsive design patterns in more components"
        })

    if components_with_issues > 5:
        recommendations.append({
            "priority": "medium",
            "category": "issues",
            "description": f"Fix {total_issues} mobile usability issues across {components_with_issues} components",
            "code": "Review components for fixed widths, hard-coded positioning, and small touch targets"
        })

    if not css_analysis["breakpoints"]:
        recommendations.append({
            "priority": "high",
            "category": "css",
            "description": "No responsive breakpoints defined in CSS",
            "code": "@media (max-width: 768px) { /* Mobile styles */ }"
        })

    if not any(comp["has_touch_handlers"] for comp in component_analysis.values()):
        recommendations.append({
            "priority": "low",
            "category": "touch",
            "description": "Consider adding touch handlers for mobile interactions",
            "code": "onTouchStart, onTouchEnd for better mobile UX"
        })

    report["recommendations"] = recommendations

    return report

def print_report(report: Dict) -> None:
    """Print formatted report to console"""
    summary = report["summary"]

    print("📱 MOBILE RESPONSIVENESS ANALYSIS REPORT")
    print("=" * 50)
    print(f"📊 Components Analyzed: {summary['total_components_analyzed']}")
    print(f"✅ Mobile-Responsive: {summary['responsive_components']} ({summary['mobile_responsive_rate']}%)")
    print(f"⚠️  Issues Found: {summary['total_issues_found']}")
    print(f"📱 Viewport Meta: {'✅' if summary['has_viewport_meta'] else '❌ Missing'}")
    print(f"🎯 CSS Media Queries: {summary['css_media_queries']}")
    print(f"📏 Breakpoints: {len(summary['breakpoints_defined'])} defined")
    print()

    # Show problematic components
    if report["most_problematic_components"]:
        print("🚨 COMPONENTS NEEDING ATTENTION:")
        for name, comp in report["most_problematic_components"]:
            print(f"  • {name}: {len(comp['potential_issues'])} issues")
            for issue in comp["potential_issues"][:2]:
                print(f"    - {issue}")
        print()

    # Show best practices
    if report["best_practice_examples"]:
        print("✅ GOOD EXAMPLES:")
        for name, comp in report["best_practice_examples"]:
            features = []
            if comp["uses_responsive_hooks"]:
                features.append("hooks")
            if comp["uses_responsive_classes"]:
                features.append("responsive classes")
            if comp["has_touch_handlers"]:
                features.append("touch handlers")

            print(f"  • {name}: {', '.join(features)}")
        print()

    # Show recommendations
    if report["recommendations"]:
        print("💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "ℹ️", "low": "💡"}
            print(f"  {priority_emoji.get(rec['priority'], '•')} {rec['description']}")
            if rec.get('code'):
                print(f"    → {rec['code']}")
        print()

    # Overall score
    score = 100
    if not summary['has_viewport_meta']:
        score -= 20
    if summary['mobile_responsive_rate'] < 80:
        score -= 30
    if summary['total_issues_found'] > 10:
        score -= 20
    if not summary['breakpoints_defined']:
        score -= 15

    print(f"🎯 OVERALL MOBILE SCORE: {max(0, score)}/100")

def main():
    """Main function to run mobile analysis"""
    report = generate_mobile_report()
    print_report(report)

    # Save detailed report
    report_file = Path("mobile_responsiveness_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
