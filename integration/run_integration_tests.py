#!/usr/bin/env python3
"""
Integration Test Runner
Executes all integration tests and generates comprehensive report
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Add the integration directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_sendgrid_integration import main as test_sendgrid
from test_sso_integration import main as test_sso
from test_webhook_retry_logic import main as test_webhook_retry
from test_api_downtime_handling import main as test_api_downtime
from test_ai_recommendations_after_team_sync import main as test_ai_recommendations

class IntegrationTestRunner:
    """Comprehensive integration test runner"""

    def __init__(self):
        self.test_modules = [
            ('SendGrid Email Integration', test_sendgrid),
            ('SSO Integration', test_sso),
            ('API Downtime Handling', test_api_downtime),
            ('AI Recommendations After Team Sync', test_ai_recommendations),
            ('Webhook Retry Logic', test_webhook_retry)
        ]
        self.results = {}
        self.start_time = None

    async def run_module_tests(self, module_name: str, test_function) -> Dict[str, Any]:
        """Run tests for a specific module"""
        print(f"\n{'='*80}")
        print(f"RUNNING {module_name.upper()}")
        print('='*80)

        try:
            start_time = time.time()
            result = await test_function()
            end_time = time.time()

            return {
                'module_name': module_name,
                'success': True,
                'execution_time': end_time - start_time,
                'results': result,
                'error': None
            }

        except Exception as e:
            end_time = time.time()
            return {
                'module_name': module_name,
                'success': False,
                'execution_time': end_time - start_time,
                'results': None,
                'error': str(e)
            }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 STARTING COMPREHENSIVE INTEGRATION TESTING")
        print(f"Started at: {datetime.now().isoformat()}")

        self.start_time = time.time()

        # Run each module
        for module_name, test_function in self.test_modules:
            result = await self.run_module_tests(module_name, test_function)
            self.results[module_name] = result

            status = "✅" if result['success'] else "❌"
            print(f"{status} {module_name}: {result['execution_time']:.3f}s")

            if result['error']:
                print(f"   Error: {result['error']}")

        end_time = time.time()
        total_time = end_time - self.start_time

        # Generate comprehensive report
        report = self._generate_report(total_time)

        # Save results
        await self._save_results(report)

        return report

    def _generate_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive integration test report"""
        successful_modules = sum(1 for r in self.results.values() if r['success'])
        total_modules = len(self.results)

        # Calculate overall metrics
        total_tests = 0
        total_successful_tests = 0
        module_summaries = {}

        for module_name, result in self.results.items():
            if result['success'] and result['results']:
                module_data = result['results']

                if 'summary' in module_data:
                    summary = module_data['summary']
                    total_tests += summary.get('total_tests', 0)
                    total_successful_tests += summary.get('successful_tests', 0)

                    module_summaries[module_name] = {
                        'total_tests': summary.get('total_tests', 0),
                        'successful_tests': summary.get('successful_tests', 0),
                        'success_rate': summary.get('success_rate', 0),
                        'average_response_time': summary.get('average_response_time', 0)
                    }
                else:
                    module_summaries[module_name] = {
                        'error': 'No summary found in results'
                    }
            else:
                module_summaries[module_name] = {
                    'error': result.get('error', 'Module execution failed')
                }

        # Generate assessment
        overall_success_rate = (total_successful_tests / total_tests * 100) if total_tests > 0 else 0

        # Assessment levels
        if overall_success_rate >= 95:
            assessment = "EXCELLENT"
            assessment_icon = "🏆"
        elif overall_success_rate >= 85:
            assessment = "GOOD"
            assessment_icon = "✅"
        elif overall_success_rate >= 70:
            assessment = "ACCEPTABLE"
            assessment_icon = "⚠️"
        else:
            assessment = "NEEDS IMPROVEMENT"
            assessment_icon = "❌"

        return {
            'execution_summary': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_execution_time': total_time,
                'modules_tested': total_modules,
                'successful_modules': successful_modules,
                'module_success_rate': (successful_modules / total_modules) * 100
            },
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': total_successful_tests,
                'failed_tests': total_tests - total_successful_tests,
                'overall_success_rate': overall_success_rate,
                'assessment': assessment,
                'assessment_icon': assessment_icon
            },
            'module_results': module_summaries,
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations(overall_success_rate, module_summaries)
        }

    def _generate_recommendations(self, overall_success_rate: float, module_summaries: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        if overall_success_rate >= 95:
            recommendations.append("🎉 Excellent integration health! All systems are production-ready.")
            recommendations.append("📈 Consider implementing automated integration testing in CI/CD pipeline.")
            recommendations.append("🔄 Set up regular integration test monitoring for continued reliability.")
        elif overall_success_rate >= 85:
            recommendations.append("✅ Good integration health. Address minor issues before production deployment.")
            recommendations.append("🔧 Focus on fixing failed tests to achieve optimal reliability.")
            recommendations.append("📊 Implement additional monitoring for integration points.")
        else:
            recommendations.append("⚠️ Integration health needs improvement before production deployment.")
            recommendations.append("🚨 Address critical integration failures immediately.")
            recommendations.append("🔍 Conduct thorough investigation of failed integration points.")

        # Module-specific recommendations
        for module_name, summary in module_summaries.items():
            if 'error' in summary:
                recommendations.append(f"🔧 Fix {module_name} execution errors: {summary['error']}")
            elif summary.get('success_rate', 0) < 90:
                recommendations.append(f"⚡ Improve {module_name} test success rate ({summary.get('success_rate', 0):.1f}%)")

        return recommendations

    async def _save_results(self, report: Dict[str, Any]):
        """Save comprehensive results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main report
        main_report_file = f"integration_test_report_{timestamp}.json"
        with open(main_report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Save individual module results
        for module_name, result in self.results.items():
            if result['success'] and result['results']:
                module_file = f"{module_name.lower().replace(' ', '_')}_results_{timestamp}.json"
                with open(module_file, 'w') as f:
                    json.dump(result['results'], f, indent=2, default=str)

        # Generate HTML report
        html_file = f"integration_test_report_{timestamp}.html"
        self._generate_html_report(report, html_file)

        print(f"\n📄 Reports saved:")
        print(f"  Main Report: {main_report_file}")
        print(f"  HTML Report: {html_file}")

    def _generate_html_report(self, report: Dict[str, Any], filename: str):
        """Generate HTML report with charts and visualizations"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Integration Test Report - PsychSync</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .assessment {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .excellent {{ background-color: #d4edda; color: #155724; }}
        .good {{ background-color: #d1ecf1; color: #0c5460; }}
        .acceptable {{ background-color: #fff3cd; color: #856404; }}
        .poor {{ background-color: #f8d7da; color: #721c24; }}
        .module-results {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .module-header {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .recommendations {{
            background: #e7f3ff;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        }}
        .recommendation {{
            margin: 10px 0;
            padding: 5px 0;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
            text-align: center;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 PsychSync Integration Test Report</h1>
        <p>Comprehensive Integration Testing Results</p>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <div class="summary">
        <div class="metric-card">
            <div class="metric-value">{report['test_summary']['total_tests']}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report['test_summary']['successful_tests']}</div>
            <div class="metric-label">Successful Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report['test_summary']['overall_success_rate']:.1f}%</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report['execution_summary']['total_execution_time']:.2f}s</div>
            <div class="metric-label">Execution Time</div>
        </div>
    </div>

    <div class="assessment {report['test_summary']['assessment'].lower()}">
        {report['test_summary']['assessment_icon']} {report['test_summary']['assessment']}
    </div>

    <div class="module-results">
        <div class="module-header">Module Results</div>
        {self._generate_module_html(report['module_results'])}
    </div>

    <div class="recommendations">
        <div class="module-header">📋 Recommendations</div>
        {self._generate_recommendations_html(report['recommendations'])}
    </div>

    <div class="timestamp">
        Report generated using PsychSync Integration Testing Framework<br>
        Total execution time: {report['execution_summary']['total_execution_time']:.2f} seconds
    </div>
</body>
</html>
        """

        with open(filename, 'w') as f:
            f.write(html_content)

    def _generate_module_html(self, module_results: Dict[str, Any]) -> str:
        """Generate HTML for module results"""
        html = ""
        for module_name, summary in module_results.items():
            if 'error' in summary:
                html += f"""
                <div style="margin: 15px 0; padding: 10px; background: #f8d7da; border-radius: 5px;">
                    <strong>❌ {module_name}</strong><br>
                    Error: {summary['error']}
                </div>
                """
            else:
                success_rate = summary.get('success_rate', 0)
                status_icon = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
                html += f"""
                <div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                    <strong>{status_icon} {module_name}</strong><br>
                    Tests: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}
                    ({success_rate:.1f}% success)<br>
                    Avg Response Time: {summary.get('average_response_time', 0):.3f}s
                </div>
                """
        return html

    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations"""
        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        return html

# Main execution
async def main():
    """Run all integration tests"""
    runner = IntegrationTestRunner()
    report = await runner.run_all_tests()

    # Print final summary
    print("\n" + "="*80)
    print("INTEGRATION TESTING COMPLETE")
    print("="*80)

    exec_summary = report['execution_summary']
    test_summary = report['test_summary']

    print(f"Execution Time: {exec_summary['total_execution_time']:.2f} seconds")
    print(f"Modules Tested: {exec_summary['modules_tested']}")
    print(f"Successful Modules: {exec_summary['successful_modules']}")
    print(f"Module Success Rate: {exec_summary['module_success_rate']:.1f}%")
    print(f"Total Tests: {test_summary['total_tests']}")
    print(f"Successful Tests: {test_summary['successful_tests']}")
    print(f"Overall Success Rate: {test_summary['overall_success_rate']:.1f}%")
    print(f"Assessment: {test_summary['assessment_icon']} {test_summary['assessment']}")

    print("\n📋 Key Recommendations:")
    for rec in report['recommendations'][:3]:  # Show top 3
        print(f"  {rec}")

    return report

if __name__ == "__main__":
    asyncio.run(main())