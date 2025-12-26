#!/usr/bin/env python3
"""
Small Mobile Viewport Testing (320px width)
Tests pages at very small mobile widths

Usage: python small_mobile_test.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List

def test_responsive_breakpoints() -> Dict:
    """Test how pages handle 320px width"""

    # Test key CSS files for 320px breakpoint support
    css_files = [
        "frontend/src/index.css",
        "frontend/src/App.css",
        "frontend/src/styles/pwa.css"
    ]

    breakpoint_analysis = {
        "has_320px_breakpoint": False,
        "has_small_mobile_support": False,
        "breakpoint_issues": [],
        "responsive_patterns": {}
    }

    for css_file in css_files:
        css_path = Path(css_file)
        if css_path.exists():
            try:
                content = css_path.read_text()

                # Check for 320px specific breakpoints
                if re.search(r'320px|@media[^{]*320', content):
                    breakpoint_analysis["has_320px_breakpoint"] = True

                # Check for general small mobile support
                if re.search(r'(max-width:\s*[23]\d\dpx|min-width:\s*320px)', content):
                    breakpoint_analysis["has_small_mobile_support"] = True

                # Find problematic patterns at small sizes
                fixed_widths = re.findall(r'width:\s*([4-9]\d\d|1000+)px', content)
                if fixed_widths:
                    breakpoint_analysis["breakpoint_issues"].extend([
                        f"Fixed width {width} will break at 320px" for width in fixed_widths[:3]
                    ])

                # Look for responsive patterns
                breakpoint_analysis["responsive_patterns"][css_file] = {
                    "flexbox_count": len(re.findall(r'display:\s*flex', content)),
                    "grid_count": len(re.findall(r'display:\s*grid', content)),
                    "media_queries": len(re.findall(r'@media', content)),
                    "viewport_units": len(re.findall(r'(vw|vh|vmin|vmax)', content))
                }

            except Exception as e:
                breakpoint_analysis["breakpoint_issues"].append(f"Error reading {css_file}: {e}")

    return breakpoint_analysis

def analyze_component_mobile_readiness() -> Dict:
    """Analyze key components for small mobile readiness"""

    # Key components that matter for mobile
    key_components = [
        "frontend/src/components/layout/DashboardLayout.tsx",
        "frontend/src/components/common/Button.tsx",
        "frontend/src/components/ui/Card.tsx",
        "frontend/src/components/NavBar.tsx",
        "frontend/src/pages/Login.tsx",
        "frontend/src/pages/Dashboard.tsx"
    ]

    component_analysis = {}

    for component in key_components:
        comp_path = Path(component)
        if comp_path.exists():
            try:
                content = comp_path.read_text()
                rel_path = str(comp_path.relative_to(Path("frontend/src")))

                analysis = {
                    "has_responsive_classes": False,
                    "has_mobile_breakpoints": False,
                    "has_fixed_dimensions": False,
                    "has_touch_friendly_sizes": False,
                    "issues": [],
                    "good_practices": []
                }

                # Check for responsive classes
                if re.search(r'(sm:|md:|lg:|xl:|mobile|responsive)', content):
                    analysis["has_responsive_classes"] = True

                # Check for mobile-specific logic
                if re.search(r'(isMobile|mobileMenu|touch|320px|375px)', content):
                    analysis["has_mobile_breakpoints"] = True

                # Look for problematic fixed dimensions
                fixed_patterns = re.findall(r'(width|height|size)=["\']?\d{3,}["\']?', content)
                if fixed_patterns:
                    analysis["has_fixed_dimensions"] = True
                    analysis["issues"].extend([f"Fixed dimension: {pattern}" for pattern in fixed_patterns[:3]])

                # Check for touch-friendly button sizes (44px minimum)
                if re.search(r'(p-4|p-6|py-4|px-6|w-12|h-12|min-h-|min-w-)', content):
                    analysis["has_touch_friendly_sizes"] = True

                # Look for good practices
                if 'max-w-md' in content or 'max-w-sm' in content:
                    analysis["good_practices"].append("Uses max-width for containers")

                if 'grid-cols-1' in content:
                    analysis["good_practices"].append("Single column layout for mobile")

                if 'px-4' in content or 'p-4' in content:
                    analysis["good_practices"].append("Proper mobile padding")

                component_analysis[rel_path] = analysis

            except Exception as e:
                component_analysis[component] = {"error": str(e)}

    return component_analysis

def generate_small_mobile_recommendations(breakpoint_analysis: Dict, component_analysis: Dict) -> List[Dict]:
    """Generate specific recommendations for 320px width optimization"""

    recommendations = []

    # Check if 320px breakpoint is supported
    if not breakpoint_analysis["has_320px_breakpoint"]:
        recommendations.append({
            "priority": "high",
            "category": "breakpoints",
            "description": "Missing 320px breakpoint support",
            "solution": "Add @media (max-width: 320px) styles for very small mobile devices",
            "code_example": "@media (max-width: 320px) { /* Small mobile styles */ }"
        })

    # Check for general mobile support
    if not breakpoint_analysis["has_small_mobile_support"]:
        recommendations.append({
            "priority": "high",
            "category": "mobile_support",
            "description": "No general small mobile support detected",
            "solution": "Implement responsive design for screens below 375px"
        })

    # Check component readiness
    components_with_fixed_sizes = [name for name, data in component_analysis.items()
                                  if data.get("has_fixed_dimensions", False)]

    if components_with_fixed_sizes:
        recommendations.append({
            "priority": "critical",
            "category": "components",
            "description": f"Components with fixed sizes: {', '.join(components_with_fixed_sizes)}",
            "solution": "Replace fixed dimensions with responsive units or min/max constraints"
        })

    # Check touch targets
    components_without_touch_friendly = [name for name, data in component_analysis.items()
                                        if not data.get("has_touch_friendly_sizes", False)]

    if components_without_touch_friendly:
        recommendations.append({
            "priority": "medium",
            "category": "touch_targets",
            "description": f"Components may have small touch targets: {', '.join(components_without_touch_friendly)}",
            "solution": "Ensure minimum touch target size of 44x44px for mobile usability"
        })

    # Check responsive class usage
    components_without_responsive = [name for name, data in component_analysis.items()
                                    if not data.get("has_responsive_classes", False)]

    if len(components_without_responsive) > len(component_analysis) * 0.5:
        recommendations.append({
            "priority": "medium",
            "category": "responsive_classes",
            "description": "Many components lack responsive styling",
            "solution": "Add Tailwind responsive variants (sm:, md:, lg:) to components"
        })

    # Add specific 320px recommendations
    recommendations.append({
        "priority": "medium",
        "category": "320px_specific",
        "description": "Optimize for 320px width devices",
        "solution": "Test on actual small devices and adjust: reduce font sizes, increase padding, simplify navigation",
        "code_example": "/* 320px specific optimizations */\n.text-xs { font-size: 0.75rem; }\n.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }"
    })

    return recommendations

def main():
    """Main function for 320px mobile testing"""
    print("📱 SMALL MOBILE VIEWPORT TESTING (320px width)")
    print("=" * 50)
    print("Testing readiness for very small mobile devices...")
    print()

    # Analyze breakpoints
    print("🔍 Analyzing CSS breakpoints...")
    breakpoint_analysis = test_responsive_breakpoints()

    # Analyze components
    print("🧩 Analyzing component mobile readiness...")
    component_analysis = analyze_component_mobile_readiness()

    # Generate recommendations
    recommendations = generate_small_mobile_recommendations(breakpoint_analysis, component_analysis)

    # Print results
    print("\n📊 320px WIDTH READINESS ANALYSIS")
    print("-" * 40)

    print(f"✅ Has 320px breakpoint: {'Yes' if breakpoint_analysis['has_320px_breakpoint'] else 'No'}")
    print(f"✅ Has small mobile support: {'Yes' if breakpoint_analysis['has_small_mobile_support'] else 'No'}")
    print(f"⚠️  Breakpoint issues: {len(breakpoint_analysis['breakpoint_issues'])}")

    if breakpoint_analysis['breakpoint_issues']:
        print("   Issues:")
        for issue in breakpoint_analysis['breakpoint_issues'][:3]:
            print(f"    • {issue}")

    print(f"\n🧩 COMPONENT ANALYSIS")
    print(f"   Total components analyzed: {len(component_analysis)}")

    responsive_components = sum(1 for data in component_analysis.values()
                               if data.get("has_responsive_classes", False))
    mobile_optimized = sum(1 for data in component_analysis.values()
                         if data.get("has_mobile_breakpoints", False))

    print(f"   Responsive classes: {responsive_components}/{len(component_analysis)}")
    print(f"   Mobile-optimized: {mobile_optimized}/{len(component_analysis)}")

    # Show problematic components
    problematic = [(name, data) for name, data in component_analysis.items()
                   if data.get("issues") and not isinstance(data, dict) or "error" not in str(data)]

    if problematic:
        print(f"\n⚠️  COMPONENTS NEEDING ATTENTION:")
        for name, data in problematic[:5]:
            issues_count = len(data.get("issues", []))
            print(f"   • {name}: {issues_count} issues")

    # Show good examples
    good_examples = [(name, data) for name, data in component_analysis.items()
                    if data.get("good_practices") and not data.get("issues")]

    if good_examples:
        print(f"\n✅ GOOD EXAMPLES:")
        for name, data in good_examples[:3]:
            practices = data.get("good_practices", [])
            print(f"   • {name}: {', '.join(practices)}")

    # Recommendations
    print(f"\n💡 320px OPTIMIZATION RECOMMENDATIONS")
    for rec in recommendations:
        priority_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "ℹ️",
            "low": "💡"
        }
        print(f"   {priority_emoji.get(rec['priority'], '•')} {rec['description']}")
        if rec.get("solution"):
            print(f"      → {rec['solution']}")
        if rec.get("code_example"):
            print(f"      📝 {rec['code_example']}")

    # Calculate readiness score
    score = 100
    if not breakpoint_analysis["has_320px_breakpoint"]:
        score -= 30
    if not breakpoint_analysis["has_small_mobile_support"]:
        score -= 20
    if len(breakpoint_analysis["breakpoint_issues"]) > 3:
        score -= 15
    if responsive_components < len(component_analysis) * 0.7:
        score -= 25

    print(f"\n🎯 320px READINESS SCORE: {max(0, score)}/100")

    # Save report
    report = {
        "test_type": "320px_small_mobile",
        "timestamp": "2025-12-02",
        "readiness_score": max(0, score),
        "breakpoint_analysis": breakpoint_analysis,
        "component_analysis": component_analysis,
        "recommendations": recommendations
    }

    report_file = Path("small_mobile_320px_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()