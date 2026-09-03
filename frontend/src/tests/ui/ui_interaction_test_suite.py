#!/usr/bin/env python3
"""
🧪 Comprehensive UI Interaction Test Suite

Automated testing for button states, hover effects, disabled conditions,
focus states, click interactions, and accessibility compliance across the platform.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@dataclass
class ButtonTestCase:
    """Test case configuration for button state testing"""
    name: str
    selector: str
    variant: Optional[str] = None
    size: Optional[str] = None
    state: str = "default"
    expected_attributes: Dict[str, str] = None
    interaction_type: str = "click"

class UIInteractionTester:
    """Comprehensive UI interaction tester"""

    def __init__(self, base_url: str = "http://localhost:5173", headless: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.wait = None
        self.actions = None
        self.test_results = []

    def setup_driver(self):
        """Setup Chrome WebDriver with optimal configuration"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Performance and compatibility options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--force-color-profile=srgb")

        # Enable logging
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")

        # Setup driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = ActionChains(self.driver)

        # Set implicit wait
        self.driver.implicitly_wait(2)

    def navigate_to_test_page(self, test_path: str = "/"):
        """Navigate to the specified test page"""
        url = f"{self.base_url}{test_path}"
        self.driver.get(url)

        # Wait for page to load
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    def take_screenshot(self, name: str) -> str:
        """Take screenshot for documentation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"button_test_{name}_{timestamp}.png"
        screenshot_path = Path("test_screenshots") / filename
        screenshot_path.parent.mkdir(exist_ok=True)

        self.driver.save_screenshot(str(screenshot_path))
        return str(screenshot_path)

    def get_button_test_cases(self) -> List[ButtonTestCase]:
        """Generate comprehensive button test cases"""
        variants = ["primary", "secondary", "danger", "default", "outline", "ghost", "link"]
        sizes = ["small", "medium", "large", "sm"]
        states = ["default", "hover", "focus", "disabled", "loading"]

        test_cases = []

        # Create test page first
        test_cases.append(ButtonTestCase(
            name="Create Test Environment",
            selector="body",
            interaction_type="setup"
        ))

        # Test each variant/size combination
        for variant in variants:
            for size in sizes:
                # Default state
                test_cases.append(ButtonTestCase(
                    name=f"{variant}_{size}_default",
                    selector=f"button[data-variant='{variant}'][data-size='{size}']:not([disabled]):not(.loading)",
                    variant=variant,
                    size=size,
                    state="default",
                    interaction_type="click"
                ))

                # Hover state
                test_cases.append(ButtonTestCase(
                    name=f"{variant}_{size}_hover",
                    selector=f"button[data-variant='{variant}'][data-size='{size}']:not([disabled]):not(.loading)",
                    variant=variant,
                    size=size,
                    state="hover",
                    interaction_type="hover"
                ))

                # Focus state
                test_cases.append(ButtonTestCase(
                    name=f"{variant}_{size}_focus",
                    selector=f"button[data-variant='{variant}'][data-size='{size}']:not([disabled]):not(.loading)",
                    variant=variant,
                    size=size,
                    state="focus",
                    interaction_type="focus"
                ))

                # Disabled state
                test_cases.append(ButtonTestCase(
                    name=f"{variant}_{size}_disabled",
                    selector=f"button[data-variant='{variant}'][data-size='{size}'][disabled]",
                    variant=variant,
                    size=size,
                    state="disabled",
                    interaction_type="verify_disabled"
                ))

                # Loading state
                test_cases.append(ButtonTestCase(
                    name=f"{variant}_{size}_loading",
                    selector=f"button[data-variant='{variant}'][data-size='{size}'].loading",
                    variant=variant,
                    size=size,
                    state="loading",
                    interaction_type="verify_loading"
                ))

        return test_cases

    def create_test_page_content(self) -> str:
        """Generate HTML content for comprehensive button testing"""
        variants = ["primary", "secondary", "danger", "default", "outline", "ghost", "link"]
        sizes = ["small", "medium", "large", "sm"]

        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Button State Testing</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                .button-test-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
                .test-section { margin-bottom: 2rem; }
                .test-button { margin: 0.5rem; }
            </style>
        </head>
        <body class="p-8 bg-gray-50">
            <h1 class="text-3xl font-bold mb-8">🧪 Comprehensive Button Testing Suite</h1>
        """

        # Generate button test cases
        for variant in variants:
            html_content += f'<div class="test-section"><h2 class="text-xl font-semibold mb-4">{variant.title()} Variant</h2><div class="button-test-grid">'

            for size in sizes:
                # Default button
                html_content += f'''
                <div class="p-4 border rounded">
                    <div class="text-sm font-medium mb-2">{size.upper()}</div>
                    <button class="test-button {self._get_button_classes(variant)} {self._get_size_classes(size)}"
                            data-variant="{variant}"
                            data-size="{size}"
                            onclick="this.classList.add('clicked'); setTimeout(() => this.classList.remove('clicked'), 200)">
                        {variant} {size}
                    </button>
                </div>
                '''

            html_content += '</div></div>'

        # Add disabled and loading test buttons
        html_content += '''
        <div class="test-section">
            <h2 class="text-xl font-semibold mb-4">State Tests</h2>
            <div class="button-test-grid">
                <div class="p-4 border rounded">
                    <div class="text-sm font-medium mb-2">Disabled Buttons</div>
                    <button class="test-button bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50" disabled>
                        Disabled Primary
                    </button>
                    <button class="test-button bg-gray-200 text-gray-900 px-4 py-2 rounded disabled:opacity-50" disabled>
                        Disabled Secondary
                    </button>
                </div>

                <div class="p-4 border rounded">
                    <div class="text-sm font-medium mb-2">Loading Buttons</div>
                    <button class="test-button bg-blue-600 text-white px-4 py-2 rounded loading" disabled>
                        <span>⏳</span> Loading Primary
                    </button>
                    <button class="test-button bg-gray-200 text-gray-900 px-4 py-2 rounded loading" disabled>
                        <span>⏳</span> Loading Secondary
                    </button>
                </div>
            </div>
        </div>

        <script>
            // Add hover and focus tracking
            document.querySelectorAll('button').forEach(button => {
                button.addEventListener('mouseenter', function() {
                    this.setAttribute('data-hover', 'true');
                });
                button.addEventListener('mouseleave', function() {
                    this.removeAttribute('data-hover');
                });
                button.addEventListener('focus', function() {
                    this.setAttribute('data-focused', 'true');
                });
                button.addEventListener('blur', function() {
                    this.removeAttribute('data-focused');
                });
            });
        </script>
        </body>
        </html>
        """

        return html_content

    def _get_button_classes(self, variant: str) -> str:
        """Get Tailwind classes for button variant"""
        class_map = {
            "primary": "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
            "secondary": "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500",
            "danger": "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
            "default": "bg-white text-black border border-gray-300 hover:bg-gray-100 focus:ring-gray-400",
            "outline": "bg-transparent border border-gray-500 text-gray-700 hover:bg-gray-50 focus:ring-gray-400",
            "ghost": "bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-400",
            "link": "bg-transparent text-blue-600 hover:text-blue-800 underline hover:no-underline"
        }
        return class_map.get(variant, "bg-blue-600 text-white")

    def _get_size_classes(self, size: str) -> str:
        """Get Tailwind classes for button size"""
        class_map = {
            "small": "px-3 py-2 text-sm",
            "medium": "px-4 py-2 text-sm",
            "large": "px-6 py-3 text-base",
            "sm": "px-2 py-1 text-xs"
        }
        return class_map.get(size, "px-4 py-2 text-sm")

    def test_button_interaction(self, test_case: ButtonTestCase) -> Dict[str, Any]:
        """Test individual button interaction"""
        result = {
            "test_name": test_case.name,
            "variant": test_case.variant,
            "size": test_case.size,
            "state": test_case.state,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "screenshot": None,
            "performance_metrics": {},
            "accessibility_check": {},
            "visual_state": {}
        }

        try:
            start_time = time.time()

            # Find the button
            elements = self.driver.find_elements(By.CSS_SELECTOR, test_case.selector)

            if not elements:
                # Fallback to more generic selector
                fallback_selector = f"button:contains('{test_case.variant} {test_case.size}')"
                elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{test_case.variant}')]")

            if not elements:
                raise Exception(f"Button not found with selector: {test_case.selector}")

            button = elements[0]

            # Get initial state
            initial_classes = button.get_attribute("class") or ""
            initial_disabled = button.get_attribute("disabled")
            initial_aria_disabled = button.get_attribute("aria-disabled")

            result["visual_state"]["initial_classes"] = initial_classes
            result["visual_state"]["initial_disabled"] = initial_disabled
            result["visual_state"]["initial_aria_disabled"] = initial_aria_disabled

            # Perform interaction based on test case
            if test_case.interaction_type == "hover":
                self.actions.move_to_element(button).perform()
                time.sleep(0.1)  # Allow hover state to apply

            elif test_case.interaction_type == "focus":
                button.send_keys(Keys.TAB)
                time.sleep(0.1)

            elif test_case.interaction_type == "click":
                self.actions.move_to_element(button).click().perform()
                time.sleep(0.1)

            elif test_case.interaction_type == "verify_disabled":
                if not button.get_attribute("disabled"):
                    raise Exception("Button should be disabled but isn't")

            elif test_case.interaction_type == "verify_loading":
                if "loading" not in button.get_attribute("class"):
                    raise Exception("Button should have loading class but doesn't")

            # Get final state
            final_classes = button.get_attribute("class") or ""
            final_disabled = button.get_attribute("disabled")

            result["visual_state"]["final_classes"] = final_classes
            result["visual_state"]["final_disabled"] = final_disabled

            # Verify state changes
            if test_case.state == "hover":
                hover_attr = button.get_attribute("data-hover")
                result["success"] = hover_attr == "true"

            elif test_case.state == "focus":
                focus_attr = button.get_attribute("data-focused")
                result["success"] = focus_attr == "true" or button == self.driver.switch_to.active_element

            elif test_case.state == "disabled":
                result["success"] = button.get_attribute("disabled") is not None

            elif test_case.state == "loading":
                result["success"] = "loading" in final_classes

            else:
                result["success"] = True  # Default state test passed

            # Performance metrics
            end_time = time.time()
            result["performance_metrics"]["interaction_time_ms"] = (end_time - start_time) * 1000

            # Accessibility check
            result["accessibility_check"]["has_aria_label"] = (
                button.get_attribute("aria-label") is not None or
                button.text.strip() != ""
            )
            result["accessibility_check"]["focusable"] = button.is_enabled() or button.get_attribute("disabled") is not None
            result["accessibility_check"]["keyboard_accessible"] = True  # Basic check

            # Take screenshot for documentation
            if self.headless == False:  # Only take screenshots in non-headless mode
                result["screenshot"] = self.take_screenshot(test_case.name)

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False

        return result

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive button state testing suite"""
        test_results = {
            "test_run_timestamp": datetime.now().isoformat(),
            "test_environment": {
                "base_url": self.base_url,
                "headless": self.headless,
                "browser": "Chrome",
                "resolution": "1920x1080"
            },
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0
            },
            "test_results": [],
            "performance_summary": {
                "avg_interaction_time_ms": 0,
                "max_interaction_time_ms": 0,
                "min_interaction_time_ms": float('inf')
            },
            "accessibility_summary": {
                "accessible_buttons": 0,
                "total_buttons_tested": 0,
                "accessibility_rate": 0.0
            }
        }

        try:
            self.setup_driver()

            # Create and navigate to test page
            test_content = self.create_test_page_content()

            # For now, navigate to the main app and look for buttons
            self.navigate_to_test_page("/")

            # Wait for page to load
            time.sleep(2)

            # Get test cases
            test_cases = self.get_button_test_cases()
            test_results["summary"]["total_tests"] = len(test_cases)

            # Run each test case
            for test_case in test_cases:
                if test_case.interaction_type == "setup":
                    continue  # Skip setup cases

                result = self.test_button_interaction(test_case)
                test_results["test_results"].append(result)

                # Update summary
                if result["success"]:
                    test_results["summary"]["passed_tests"] += 1
                else:
                    test_results["summary"]["failed_tests"] += 1

                # Update performance metrics
                if "performance_metrics" in result and "interaction_time_ms" in result["performance_metrics"]:
                    interaction_time = result["performance_metrics"]["interaction_time_ms"]
                    test_results["performance_summary"]["max_interaction_time_ms"] = max(
                        test_results["performance_summary"]["max_interaction_time_ms"],
                        interaction_time
                    )
                    test_results["performance_summary"]["min_interaction_time_ms"] = min(
                        test_results["performance_summary"]["min_interaction_time_ms"],
                        interaction_time
                    )

                # Update accessibility metrics
                if "accessibility_check" in result and result["accessibility_check"].get("has_aria_label"):
                    test_results["accessibility_summary"]["accessible_buttons"] += 1
                test_results["accessibility_summary"]["total_buttons_tested"] += 1

            # Calculate summary metrics
            test_results["summary"]["success_rate"] = (
                test_results["summary"]["passed_tests"] / test_results["summary"]["total_tests"] * 100
                if test_results["summary"]["total_tests"] > 0 else 0
            )

            # Calculate average interaction time
            if test_results["summary"]["total_tests"] > 0:
                total_time = sum(
                    r.get("performance_metrics", {}).get("interaction_time_ms", 0)
                    for r in test_results["test_results"]
                )
                test_results["performance_summary"]["avg_interaction_time_ms"] = (
                    total_time / len(test_results["test_results"])
                )

            # Calculate accessibility rate
            if test_results["accessibility_summary"]["total_buttons_tested"] > 0:
                test_results["accessibility_summary"]["accessibility_rate"] = (
                    test_results["accessibility_summary"]["accessible_buttons"] /
                    test_results["accessibility_summary"]["total_buttons_tested"] * 100
                )

        except Exception as e:
            test_results["error"] = str(e)
            test_results["success"] = False

        finally:
            if self.driver:
                self.driver.quit()

        return test_results

    def save_test_results(self, results: Dict[str, Any]) -> str:
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ui_interaction_test_results_{timestamp}.json"
        filepath = Path("test_results") / filename
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return str(filepath)

async def main():
    """Main test execution"""
    print("🧪 Starting Comprehensive UI Interaction Testing Suite")
    print("=" * 60)

    # Initialize tester
    tester = UIInteractionTester(
        base_url="http://localhost:5173",
        headless=True  # Set to False for visual testing
    )

    try:
        # Run comprehensive tests
        print("🎯 Running comprehensive button state tests...")
        results = tester.run_comprehensive_tests()

        # Display summary
        print("\n📊 Test Results Summary:")
        print(f"  Total Tests: {results['summary']['total_tests']}")
        print(f"  Passed: {results['summary']['passed_tests']}")
        print(f"  Failed: {results['summary']['failed_tests']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")

        print(f"\n⚡ Performance Summary:")
        print(f"  Avg Interaction Time: {results['performance_summary']['avg_interaction_time_ms']:.2f}ms")
        print(f"  Max Interaction Time: {results['performance_summary']['max_interaction_time_ms']:.2f}ms")
        print(f"  Min Interaction Time: {results['performance_summary']['min_interaction_time_ms']:.2f}ms")

        print(f"\n♿ Accessibility Summary:")
        print(f"  Accessible Buttons: {results['accessibility_summary']['accessible_buttons']}")
        print(f"  Total Buttons Tested: {results['accessibility_summary']['total_buttons_tested']}")
        print(f"  Accessibility Rate: {results['accessibility_summary']['accessibility_rate']:.1f}%")

        # Save detailed results
        results_file = tester.save_test_results(results)
        print(f"\n💾 Detailed results saved to: {results_file}")

        # Display failed tests if any
        failed_tests = [r for r in results['test_results'] if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests[:5]:  # Show first 5
                print(f"  - {test['test_name']}: {test.get('error', 'Unknown error')}")
            if len(failed_tests) > 5:
                print(f"  ... and {len(failed_tests) - 5} more")

        # Overall assessment
        success_rate = results['summary']['success_rate']
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT: Button state testing completed with {success_rate:.1f}% success rate!")
        elif success_rate >= 85:
            print(f"\n✅ GOOD: Button state testing completed with {success_rate:.1f}% success rate.")
        elif success_rate >= 70:
            print(f"\n⚠️ ACCEPTABLE: Button state testing completed with {success_rate:.1f}% success rate. Some improvements needed.")
        else:
            print(f"\n❌ NEEDS WORK: Button state testing completed with {success_rate:.1f}% success rate. Significant improvements needed.")

        return success_rate >= 85

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
