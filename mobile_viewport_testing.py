#!/usr/bin/env python3
"""
Mobile Viewport Usability Testing Script
Tests all PsychSync pages at mobile viewport widths < 390px

Usage:
    python mobile_viewport_testing.py [--width=375] [--headless] [--screenshot-dir=./screenshots]
"""

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("Error: selenium not installed. Install with: pip install selenium")
    exit(1)

# Page routes identified from App.tsx
PAGE_ROUTES = {
    # Public routes
    "login": "/login",
    "register": "/register",
    "verify_email": "/verify-email",
    "forgot_password": "/forgot-password",
    "anonymous_feedback": "/anonymous-feedback",
    "feedback_status": "/feedback-status",
    "public_landing": "/",

    # Protected routes (require authentication)
    "dashboard": "/dashboard",
    "profile": "/profile",
    "teams": "/teams",
    "assessments": "/assessments",
    "my_responses": "/responses/my-responses",
    "analytics": "/analytics",
    "settings": "/settings",
    "templates": "/templates",
    "team_optimizer": "/team-optimizer",
    "predictive_analytics": "/predictive-analytics",
    "reliability_validity": "/reliability-validity",
    "employee_safety": "/employee-safety",
    "quick_assessment": "/quick-assessment",
}

# Viewport sizes to test
VIEWPORT_SIZES = {
    "iphone_se": {"width": 375, "height": 667},
    "small_mobile": {"width": 320, "height": 568},
    "very_small_mobile": {"width": 280, "height": 653},
}

@dataclass
class UsabilityIssue:
    """Represents a usability issue found during testing"""
    page: str
    viewport: str
    issue_type: str
    description: str
    severity: str  # "critical", "major", "minor"
    element_selector: Optional[str] = None
    screenshot_path: Optional[str] = None

@dataclass
class PageTestResult:
    """Test results for a single page"""
    page: str
    route: str
    viewport: str
    load_success: bool
    load_time: float
    issues: List[UsabilityIssue]
    screenshot_path: Optional[str] = None
    width_overflow: bool = False
    horizontal_scroll: bool = False
    touch_targets_usable: bool = True
    text_readable: bool = True

class MobileViewportTester:
    """Tests mobile viewport usability for web pages"""

    def __init__(self, base_url: str = "http://localhost:5173", screenshot_dir: str = "./screenshots"):
        self.base_url = base_url
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.driver: Optional[webdriver.Chrome] = None
        self.results: List[PageTestResult] = []

    def setup_driver(self, headless: bool = True) -> None:
        """Initialize Chrome WebDriver with mobile emulation"""
        options = Options()

        if headless:
            options.add_argument("--headless")

        # Mobile-specific options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1")

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            print("✅ Chrome WebDriver initialized successfully")
        except WebDriverException as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("Please ensure Chrome is installed and chromedriver is available")
            raise

    def set_viewport(self, width: int, height: int) -> None:
        """Set browser viewport size"""
        if self.driver:
            self.driver.set_window_size(width, height)

    def take_screenshot(self, filename: str) -> str:
        """Take screenshot and return file path"""
        if not self.driver:
            return ""

        screenshot_path = self.screenshot_dir / filename
        self.driver.save_screenshot(str(screenshot_path))
        return str(screenshot_path)

    def check_horizontal_scroll(self) -> Tuple[bool, int]:
        """Check if page has horizontal scroll"""
        try:
            # Get page dimensions
            page_width = self.driver.execute_script("return document.body.scrollWidth")
            viewport_width = self.driver.execute_script("return window.innerWidth")

            has_horizontal_scroll = page_width > viewport_width
            overflow_amount = max(0, page_width - viewport_width)

            return has_horizontal_scroll, overflow_amount
        except:
            return False, 0

    def check_touch_targets(self) -> Tuple[bool, List[str]]:
        """Check if touch targets meet minimum size requirements (44px)"""
        try:
            # Find interactive elements
            interactive_selectors = [
                "button", "a", "input[type='button']", "input[type='submit']",
                "[role='button']", ".btn", "clickable-element"
            ]

            issues = []
            usable = True

            for selector in interactive_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        size = element.size
                        if size.width < 44 or size.height < 44:
                            issues.append(f"Touch target too small: {size.width}x{size.height}px")
                            usable = False
                except:
                    continue

            return usable, issues
        except:
            return True, []

    def check_text_readability(self) -> Tuple[bool, List[str]]:
        """Check for text readability issues"""
        try:
            issues = []

            # Check for text overflow
            overflow_elements = self.driver.execute_script("""
                var elements = document.querySelectorAll('*');
                var issues = [];
                elements.forEach(function(el) {
                    if (el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight) {
                        if (el.textContent.trim().length > 0) {
                            issues.push(el.tagName + '#' + (el.id || '') + '.' + (el.className || ''));
                        }
                    }
                });
                return issues;
            """)

            if overflow_elements:
                issues.extend([f"Text overflow in: {elem}" for elem in overflow_elements])

            # Check font sizes
            small_text = self.driver.execute_script("""
                var elements = document.querySelectorAll('*');
                var smallElements = [];
                elements.forEach(function(el) {
                    if (el.textContent && el.textContent.trim().length > 0) {
                        var styles = window.getComputedStyle(el);
                        var fontSize = parseFloat(styles.fontSize);
                        if (fontSize < 14) {
                            smallElements.push(el.tagName + ': ' + fontSize + 'px');
                        }
                    }
                });
                return smallElements;
            """)

            if small_text:
                issues.extend([f"Text too small: {elem}" for elem in small_text])

            return len(issues) == 0, issues
        except:
            return True, []

    def test_page(self, page_name: str, route: str, viewport_name: str, viewport_size: Dict) -> PageTestResult:
        """Test a single page at specific viewport size"""
        print(f"🔍 Testing {page_name} at {viewport_size['width']}x{viewport_size['height']} ({viewport_name})")

        # Set viewport
        self.set_viewport(viewport_size['width'], viewport_size['height'])
        time.sleep(0.5)

        # Navigate to page
        start_time = time.time()
        load_success = True
        issues = []

        try:
            url = urljoin(self.base_url, route)
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            load_time = time.time() - start_time

            # Take initial screenshot
            screenshot_name = f"{page_name}_{viewport_name}_{int(time.time())}.png"
            screenshot_path = self.take_screenshot(screenshot_name)

            # Check for common mobile usability issues
            has_horiz_scroll, overflow_amount = self.check_horizontal_scroll()
            if has_horiz_scroll:
                issues.append(UsabilityIssue(
                    page=page_name,
                    viewport=viewport_name,
                    issue_type="horizontal_scroll",
                    description=f"Page scrolls horizontally by {overflow_amount}px",
                    severity="critical"
                ))

            touch_usable, touch_issues = self.check_touch_targets()
            if not touch_usable:
                for issue in touch_issues:
                    issues.append(UsabilityIssue(
                        page=page_name,
                        viewport=viewport_name,
                        issue_type="touch_target",
                        description=issue,
                        severity="major"
                    ))

            text_readable, text_issues = self.check_text_readability()
            if not text_readable:
                for issue in text_issues:
                    issues.append(UsabilityIssue(
                        page=page_name,
                        viewport=viewport_name,
                        issue_type="text_readability",
                        description=issue,
                        severity="minor"
                    ))

            # Check for viewport meta tag
            try:
                viewport_meta = self.driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
                viewport_content = viewport_meta.get_attribute("content")
                if "width=device-width" not in viewport_content:
                    issues.append(UsabilityIssue(
                        page=page_name,
                        viewport=viewport_name,
                        issue_type="viewport_meta",
                        description="Missing or improper viewport meta tag",
                        severity="critical"
                    ))
            except:
                issues.append(UsabilityIssue(
                    page=page_name,
                    viewport=viewport_name,
                    issue_type="viewport_meta",
                    description="No viewport meta tag found",
                    severity="critical"
                ))

        except TimeoutException:
            load_success = False
            load_time = time.time() - start_time
            issues.append(UsabilityIssue(
                page=page_name,
                viewport=viewport_name,
                issue_type="load_timeout",
                description="Page failed to load within timeout",
                severity="critical"
            ))
        except Exception as e:
            load_success = False
            load_time = time.time() - start_time
            issues.append(UsabilityIssue(
                page=page_name,
                viewport=viewport_name,
                issue_type="load_error",
                description=f"Page load error: {str(e)}",
                severity="critical"
            ))

        return PageTestResult(
            page=page_name,
            route=route,
            viewport=viewport_name,
            load_success=load_success,
            load_time=load_time,
            issues=issues,
            screenshot_path=screenshot_path,
            width_overflow=has_horiz_scroll if 'has_horiz_scroll' in locals() else False,
            horizontal_scroll=has_horiz_scroll if 'has_horiz_scroll' in locals() else False,
            touch_targets_usable=touch_usable if 'touch_usable' in locals() else True,
            text_readable=text_readable if 'text_readable' in locals() else True
        )

    def run_all_tests(self, viewports: List[str] = None) -> None:
        """Run tests on all pages for specified viewports"""
        if not viewports:
            viewports = ["iphone_se", "small_mobile"]

        print(f"🚀 Starting mobile viewport testing for {len(PAGE_ROUTES)} pages")
        print(f"📱 Testing viewports: {', '.join(viewports)}")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"📸 Screenshots will be saved to: {self.screenshot_dir}")
        print()

        for viewport_name in viewports:
            viewport_size = VIEWPORT_SIZES[viewport_name]
            print(f"📱 Testing viewport: {viewport_name} ({viewport_size['width']}x{viewport_size['height']})")
            print("-" * 60)

            for page_name, route in PAGE_ROUTES.items():
                result = self.test_page(page_name, route, viewport_name, viewport_size)
                self.results.append(result)

                # Print immediate results
                if result.load_success:
                    if result.issues:
                        critical_count = sum(1 for issue in result.issues if issue.severity == "critical")
                        major_count = sum(1 for issue in result.issues if issue.severity == "major")
                        minor_count = sum(1 for issue in result.issues if issue.severity == "minor")
                        print(f"⚠️  {page_name}: {critical_count} critical, {major_count} major, {minor_count} minor issues")
                    else:
                        print(f"✅ {page_name}: No issues ({result.load_time:.1f}s)")
                else:
                    print(f"❌ {page_name}: Failed to load")

            print()

    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_pages = len(PAGE_ROUTES)
        total_tests = len(self.results)

        # Count issues by severity
        critical_issues = sum(len([r for r in result.issues if r.severity == "critical"]) for result in self.results)
        major_issues = sum(len([r for r in result.issues if r.severity == "major"]) for result in self.results)
        minor_issues = sum(len([r for r in result.issues if r.severity == "minor"]) for result in self.results)

        # Calculate success rate
        successful_loads = sum(1 for result in self.results if result.load_success)
        success_rate = (successful_loads / total_tests) * 100 if total_tests > 0 else 0

        # Group issues by type
        issue_types = {}
        for result in self.results:
            for issue in result.issues:
                if issue.issue_type not in issue_types:
                    issue_types[issue.issue_type] = []
                issue_types[issue.issue_type].append(issue)

        # Find most problematic pages
        page_scores = {}
        for result in self.results:
            if result.page not in page_scores:
                page_scores[result.page] = {"issues": 0, "critical": 0, "load_success": True}

            page_scores[result.page]["issues"] += len(result.issues)
            page_scores[result.page]["critical"] += sum(1 for issue in result.issues if issue.severity == "critical")
            if not result.load_success:
                page_scores[result.page]["load_success"] = False

        most_problematic = sorted(page_scores.items(), key=lambda x: (x[1]["critical"], x[1]["issues"]), reverse=True)

        return {
            "summary": {
                "total_pages": total_pages,
                "total_tests": total_tests,
                "success_rate": round(success_rate, 1),
                "critical_issues": critical_issues,
                "major_issues": major_issues,
                "minor_issues": minor_issues,
                "pages_with_failures": total_pages - len([p for p, score in page_scores.items() if score["load_success"]])
            },
            "issue_breakdown": issue_types,
            "most_problematic_pages": most_problematic[:10],
            "detailed_results": [
                {
                    "page": result.page,
                    "route": result.route,
                    "viewport": result.viewport,
                    "load_success": result.load_success,
                    "load_time": result.load_time,
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "description": issue.description
                        } for issue in result.issues
                    ]
                } for result in self.results
            ]
        }

    def save_report(self, report: Dict, filename: str = "mobile_viewport_test_report.json") -> None:
        """Save test report to JSON file"""
        report_path = self.screenshot_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📊 Test report saved to: {report_path}")

    def print_summary(self, report: Dict) -> None:
        """Print test summary to console"""
        summary = report["summary"]

        print("📱 MOBILE VIEWPORT USABILITY TEST SUMMARY")
        print("=" * 50)
        print(f"📊 Total Pages Tested: {summary['total_pages']}")
        print(f"✅ Success Rate: {summary['success_rate']}%")
        print(f"⚠️  Critical Issues: {summary['critical_issues']}")
        print(f"⚠️  Major Issues: {summary['major_issues']}")
        print(f"ℹ️  Minor Issues: {summary['minor_issues']}")
        print(f"❌ Pages with Failures: {summary['pages_with_failures']}")
        print()

        if report["most_problematic_pages"]:
            print("🚨 MOST PROBLEMATIC PAGES:")
            for page_name, issues in report["most_problematic_pages"][:5]:
                if issues["critical"] > 0 or not issues["load_success"]:
                    status = "❌ FAILED TO LOAD" if not issues["load_success"] else f"{issues['critical']} critical issues"
                    print(f"  • {page_name}: {status}")
            print()

        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if summary["critical_issues"] > 0:
            print("  • Fix critical issues immediately - they block mobile users")
        if summary["major_issues"] > 0:
            print("  • Address major issues to improve mobile experience")
        if summary["pages_with_failures"] > 0:
            print("  • Investigate page load failures")
        if summary["success_rate"] < 100:
            print("  • Improve mobile error handling and fallbacks")

        if summary["critical_issues"] == 0 and summary["major_issues"] == 0 and summary["pages_with_failures"] == 0:
            print("  🎉 Excellent mobile compatibility! All pages passed basic usability tests.")

    def cleanup(self) -> None:
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Test mobile viewport usability")
    parser.add_argument("--base-url", default="http://localhost:5173", help="Base URL to test")
    parser.add_argument("--width", type=int, default=375, help="Viewport width to test")
    parser.add_argument("--height", type=int, default=667, help="Viewport height to test")
    parser.add_argument("--headless", action="store_true", default=True, help="Run headless")
    parser.add_argument("--screenshot-dir", default="./screenshots", help="Screenshot directory")
    parser.add_argument("--viewport", choices=["iphone_se", "small_mobile", "very_small_mobile"],
                       default=["iphone_se", "small_mobile"], nargs="+",
                       help="Viewports to test")

    args = parser.parse_args()

    tester = MobileViewportTester(args.base_url, args.screenshot_dir)

    try:
        tester.setup_driver(headless=args.headless)

        # Add custom viewport if specified
        if args.width != 375:
            VIEWPORT_SIZES["custom"] = {"width": args.width, "height": args.height}
            if "custom" not in args.viewport:
                args.viewport.append("custom")

        tester.run_all_tests(args.viewport)

        report = tester.generate_report()
        tester.save_report(report)
        tester.print_summary(report)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1
    finally:
        tester.cleanup()

    return 0

if __name__ == "__main__":
    exit(main())
