#!/usr/bin/env python3
"""
API Contract Drift Detection Agent

Monitors API endpoints and detects when implementations drift from their
OpenAPI/Swagger specifications. This prevents breaking changes and ensures
API documentation stays in sync with code.

Usage:
    python agents/api_contract_agent.py --api-path app/api/v1/api.py --spec-path openapi.json
    python agents/api_contract_agent.py --watch --interval 300  # Continuous monitoring
"""

import argparse
import ast
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import subprocess
import hashlib


class APIEndpoint:
    """Represents a single API endpoint"""
    def __init__(self, path: str, method: str, function_name: str = None):
        self.path = path
        self.method = method.lower()
        self.function_name = function_name
        self.parameters = []
        self.return_type = None
        self.status_codes = []
        self.file_path = None
        self.line_number = None

    def __hash__(self):
        return hash((self.path, self.method))

    def __eq__(self, other):
        if not isinstance(other, APIEndpoint):
            return False
        return self.path == other.path and self.method == other.method

    def __repr__(self):
        return f"APIEndpoint({self.method.upper()} {self.path})"


class OpenAPISpecParser:
    """Parses OpenAPI/Swagger specifications"""

    def __init__(self, spec_path: str):
        self.spec_path = spec_path
        self.spec = self._load_spec()
        self.endpoints = self._extract_endpoints()

    def _load_spec(self) -> Dict:
        """Load OpenAPI spec from JSON or YAML file"""
        if not os.path.exists(self.spec_path):
            raise FileNotFoundError(f"Spec file not found: {self.spec_path}")

        with open(self.spec_path, 'r') as f:
            if self.spec_path.endswith('.json'):
                return json.load(f)
            elif self.spec_path.endswith('.yaml') or self.spec_path.endswith('.yml'):
                import yaml
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported spec format: {self.spec_path}")

    def _extract_endpoints(self) -> Dict[str, APIEndpoint]:
        """Extract all endpoints from OpenAPI spec"""
        endpoints = {}

        if 'paths' not in self.spec:
            return endpoints

        for path, methods in self.spec['paths'].items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                    endpoint_key = f"{method.lower()}:{path}"
                    endpoint = APIEndpoint(path, method.lower())

                    # Extract parameters
                    if 'parameters' in details:
                        endpoint.parameters = [p['name'] for p in details['parameters']]

                    # Extract response status codes
                    if 'responses' in details:
                        endpoint.status_codes = list(details['responses'].keys())

                    # Extract operation ID (function name hint)
                    endpoint.function_name = details.get('operationId')

                    endpoints[endpoint_key] = endpoint

        return endpoints

    def get_endpoints(self) -> Dict[str, APIEndpoint]:
        """Get all endpoints from spec"""
        return self.endpoints


class FastAPIParser:
    """Parses FastAPI route definitions from Python code"""

    def __init__(self, api_path: str):
        self.api_path = api_path
        self.endpoints = {}
        self._parse_api_file()

    def _parse_api_file(self):
        """Parse FastAPI routes from Python file or directory"""
        if not os.path.exists(self.api_path):
            raise FileNotFoundError(f"API path not found: {self.api_path}")

        if os.path.isfile(self.api_path):
            # Parse single file
            self._parse_single_file(self.api_path)
        elif os.path.isdir(self.api_path):
            # Parse all Python files in directory
            for filename in os.listdir(self.api_path):
                if filename.endswith('.py') and not filename.startswith('__'):
                    file_path = os.path.join(self.api_path, filename)
                    self._parse_single_file(file_path)

    def _parse_single_file(self, file_path: str):
        """Parse FastAPI routes from a single Python file"""
        try:
            with open(file_path, 'r') as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            # Find all @router decorators
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self._extract_endpoint_from_function(node, file_path)
        except SyntaxError as e:
            print(f"⚠️  Skipping {file_path}: Syntax error - {e}")
        except Exception as e:
            print(f"⚠️  Skipping {file_path}: {e}")

    def _extract_endpoint_from_function(self, func_node, file_path: str):
        """Extract endpoint info from function with @router decorator"""
        for decorator in func_node.decorator_list:
            # Handle @router.get("/path"), @router.post("/path"), etc.
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr') and decorator.func.attr in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                    method = decorator.func.attr

                    # Extract path from decorator arguments
                    path = self._extract_path(decorator)

                    if path:
                        endpoint_key = f"{method}:{path}"
                        endpoint = APIEndpoint(path, method, func_node.name)
                        endpoint.file_path = file_path
                        endpoint.line_number = func_node.lineno

                        # Extract parameters from function signature
                        endpoint.parameters = self._extract_parameters(func_node)

                        # Extract return type
                        if func_node.returns:
                            try:
                                endpoint.return_type = ast.unparse(func_node.returns)
                            except:
                                endpoint.return_type = None

                        # Extract status codes from docstring
                        endpoint.status_codes = self._extract_status_codes(func_node)

                        self.endpoints[endpoint_key] = endpoint

    def _extract_path(self, decorator) -> Optional[str]:
        """Extract path string from @router decorator"""
        for arg in decorator.args:
            if isinstance(arg, ast.Constant):
                if isinstance(arg.value, str):
                    return arg.value
            elif isinstance(arg, ast.Str):  # Python < 3.8
                return arg.s

        # Check keyword arguments
        for keyword in decorator.keywords:
            if keyword.arg == 'path':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value

        return None

    def _extract_parameters(self, func_node) -> List[str]:
        """Extract parameter names from function signature"""
        params = []

        # Get positional and keyword parameters
        for arg in func_node.args.args:
            if arg.arg not in ['self', 'request', 'db', 'current_user', 'token']:
                params.append(arg.arg)

        return params

    def _extract_status_codes(self, func_node) -> List[str]:
        """Extract documented status codes from docstring"""
        status_codes = []

        if func_node.body and isinstance(func_node.body[0], ast.Expr):
            if isinstance(func_node.body[0].value, ast.Constant):
                docstring = func_node.body[0].value.value
                if isinstance(docstring, str):
                    # Look for status codes in docstring (e.g., "200:", "404:")
                    lines = docstring.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and line[0].isdigit() and ':' in line:
                            status_code = line.split(':')[0]
                            if status_code not in status_codes:
                                status_codes.append(status_code)

        return status_codes

    def get_endpoints(self) -> Dict[str, APIEndpoint]:
        """Get all endpoints from FastAPI code"""
        return self.endpoints


class ContractDriftDetector:
    """Detects drift between API spec and implementation"""

    def __init__(self, spec_parser: OpenAPISpecParser, impl_parser: FastAPIParser):
        self.spec_parser = spec_parser
        self.impl_parser = impl_parser
        self.drifts = []

    def detect_drifts(self) -> List[Dict]:
        """Detect all contract drifts"""
        self.drifts = []

        spec_endpoints = self.spec_parser.get_endpoints()
        impl_endpoints = self.impl_parser.get_endpoints()

        spec_keys = set(spec_endpoints.keys())
        impl_keys = set(impl_endpoints.keys())

        # 1. Endpoints in spec but not in implementation
        for key in spec_keys - impl_keys:
            endpoint = spec_endpoints[key]
            self.drifts.append({
                'type': 'missing_implementation',
                'severity': 'critical',
                'message': f"Endpoint documented but not implemented: {endpoint.method.upper()} {endpoint.path}",
                'endpoint': {
                    'method': endpoint.method,
                    'path': endpoint.path,
                    'function_name': endpoint.function_name
                },
                'recommendation': f"Implement {endpoint.method.upper()} {endpoint.path} in FastAPI routes"
            })

        # 2. Endpoints in implementation but not in spec
        for key in impl_keys - spec_keys:
            endpoint = impl_endpoints[key]
            self.drifts.append({
                'type': 'missing_documentation',
                'severity': 'warning',
                'message': f"Endpoint implemented but not documented: {endpoint.method.upper()} {endpoint.path}",
                'endpoint': {
                    'method': endpoint.method,
                    'path': endpoint.path,
                    'function_name': endpoint.function_name,
                    'file_path': endpoint.file_path,
                    'line_number': endpoint.line_number
                },
                'recommendation': f"Add {endpoint.method.upper()} {endpoint.path} to OpenAPI spec",
                'file': endpoint.file_path,
                'line': endpoint.line_number
            })

        # 3. Parameter mismatches
        for key in spec_keys & impl_keys:
            spec_endpoint = spec_endpoints[key]
            impl_endpoint = impl_endpoints[key]

            spec_params = set(spec_endpoint.parameters)
            impl_params = set(impl_endpoint.parameters)

            if spec_params != impl_params:
                missing_in_impl = spec_params - impl_params
                missing_in_spec = impl_params - spec_params

                if missing_in_impl:
                    self.drifts.append({
                        'type': 'parameter_mismatch',
                        'severity': 'error',
                        'message': f"Parameters in spec but not in implementation: {missing_in_impl}",
                        'endpoint': {
                            'method': impl_endpoint.method,
                            'path': impl_endpoint.path,
                            'function_name': impl_endpoint.function_name
                        },
                        'recommendation': f"Add parameters to {impl_endpoint.method.upper()} {impl_endpoint.path} function"
                    })

                if missing_in_spec:
                    self.drifts.append({
                        'type': 'parameter_mismatch',
                        'severity': 'warning',
                        'message': f"Parameters in implementation but not in spec: {missing_in_spec}",
                        'endpoint': {
                            'method': impl_endpoint.method,
                            'path': impl_endpoint.path,
                            'function_name': impl_endpoint.function_name
                        },
                        'recommendation': f"Update OpenAPI spec with missing parameters: {missing_in_spec}"
                    })

        # 4. Status code mismatches
        for key in spec_keys & impl_keys:
            spec_endpoint = spec_endpoints[key]
            impl_endpoint = impl_endpoints[key]

            spec_codes = set(spec_endpoint.status_codes)
            impl_codes = set(impl_endpoint.status_codes)

            if spec_codes and impl_codes and spec_codes != impl_codes:
                self.drifts.append({
                    'type': 'status_code_mismatch',
                    'severity': 'info',
                    'message': f"Status codes differ between spec and implementation: {impl_endpoint.method.upper()} {impl_endpoint.path}",
                    'endpoint': {
                        'method': impl_endpoint.method,
                        'path': impl_endpoint.path,
                        'function_name': impl_endpoint.function_name
                    },
                    'spec_codes': list(spec_codes),
                    'impl_codes': list(impl_codes),
                    'recommendation': "Align documented status codes with actual implementation"
                })

        return self.drifts

    def generate_report(self) -> Dict:
        """Generate comprehensive drift report"""
        drifts = self.detect_drifts()

        severity_counts = {
            'critical': sum(1 for d in drifts if d['severity'] == 'critical'),
            'error': sum(1 for d in drifts if d['severity'] == 'error'),
            'warning': sum(1 for d in drifts if d['severity'] == 'warning'),
            'info': sum(1 for d in drifts if d['severity'] == 'info')
        }

        total_drifts = len(drifts)

        return {
            'timestamp': datetime.now().isoformat(),
            'total_drifts': total_drifts,
            'severity_breakdown': severity_counts,
            'health_score': max(0, 100 - (total_drifts * 5)),
            'drifts': drifts,
            'summary': self._generate_summary(drifts)
        }

    def _generate_summary(self, drifts: List[Dict]) -> str:
        """Generate human-readable summary"""
        if not drifts:
            return "✅ No contract drift detected. API implementation matches specification."

        critical = sum(1 for d in drifts if d['severity'] == 'critical')
        error = sum(1 for d in drifts if d['severity'] == 'error')
        warning = sum(1 for d in drifts if d['severity'] == 'warning')

        if critical > 0:
            return f"🚨 CRITICAL: {critical} endpoints documented but not implemented!"
        elif error > 0:
            return f"⚠️  ATTENTION NEEDED: {error} parameter mismatches detected."
        elif warning > 0:
            return f"📝 IMPROVEMENTS: {warning} endpoints need documentation updates."
        else:
            return f"ℹ️  {len(drifts)} minor issues detected."

    def save_report(self, output_path: str = 'reports/api_contract_drift.json'):
        """Save drift report to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        report = self.generate_report()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✅ Report saved to: {output_path}")
        print(f"   Total drifts: {report['total_drifts']}")
        print(f"   Health score: {report['health_score']}/100")
        print(f"\n{report['summary']}")

        return report


def watch_for_drifts(api_path: str, spec_path: str, interval: int = 300):
    """Continuously watch for API contract drifts"""
    print(f"🔍 Watching for API contract drifts (checking every {interval}s)...")
    print(f"   API file: {api_path}")
    print(f"   Spec file: {spec_path}")

    # Store previous file hashes
    api_hash = hashlib.md5(open(api_path, 'rb').read()).hexdigest()
    spec_hash = hashlib.md5(open(spec_path, 'rb').read()).hexdigest()

    while True:
        try:
            # Check if files changed
            current_api_hash = hashlib.md5(open(api_path, 'rb').read()).hexdigest()
            current_spec_hash = hashlib.md5(open(spec_path, 'rb').read()).hexdigest()

            if current_api_hash != api_hash or current_spec_hash != spec_hash:
                print(f"\n🔄 Change detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Re-parse and detect drifts
                spec_parser = OpenAPISpecParser(spec_path)
                impl_parser = FastAPIParser(api_path)
                detector = ContractDriftDetector(spec_parser, impl_parser)
                report = detector.save_report()

                # Update hashes
                api_hash = current_api_hash
                spec_hash = current_spec_hash

                # Send alert if critical drifts detected
                critical_count = report['severity_breakdown']['critical']
                if critical_count > 0:
                    print(f"🚨 ALERT: {critical_count} critical drift(s) detected!")
                    # TODO: Send Slack/email notification

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\n✅ Stopped watching for drifts.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description='API Contract Drift Detection Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single scan
  python agents/api_contract_agent.py --api-path app/api/v1/api.py --spec-path openapi.json

  # Continuous monitoring
  python agents/api_contract_agent.py --api-path app/api/v1/api.py --spec-path openapi.json --watch --interval 300

  # Generate report with custom output path
  python agents/api_contract_agent.py --api-path app/api/v1/api.py --spec-path openapi.json --output reports/drift.json
        """
    )

    parser.add_argument('--api-path', required=True, help='Path to FastAPI routes file')
    parser.add_argument('--spec-path', required=True, help='Path to OpenAPI spec file')
    parser.add_argument('--output', default='reports/api_contract_drift.json', help='Output report path')
    parser.add_argument('--watch', action='store_true', help='Enable continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300)')

    args = parser.parse_args()

    if args.watch:
        watch_for_drifts(args.api_path, args.spec_path, args.interval)
    else:
        # Single scan
        print(f"🔍 Scanning for API contract drifts...")
        print(f"   API file: {args.api_path}")
        print(f"   Spec file: {args.spec_path}")

        try:
            spec_parser = OpenAPISpecParser(args.spec_path)
            impl_parser = FastAPIParser(args.api_path)
            detector = ContractDriftDetector(spec_parser, impl_parser)
            report = detector.save_report(args.output)

            # Print summary to console
            print(f"\n{'='*60}")
            print(f"API CONTRACT DRIFT REPORT")
            print(f"{'='*60}")
            print(f"Health Score: {report['health_score']}/100")
            print(f"Total Drifts: {report['total_drifts']}")
            print(f"\nSeverity Breakdown:")
            for severity, count in report['severity_breakdown'].items():
                if count > 0:
                    print(f"  {severity.upper()}: {count}")
            print(f"\n{report['summary']}")
            print(f"{'='*60}\n")

            # Exit with error code if critical drifts found
            if report['severity_breakdown']['critical'] > 0:
                sys.exit(1)

        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
