#!/usr/bin/env python3
"""
Documentation Completeness Assessment Agent

Scans codebase and checks if all modules, functions, and APIs are properly documented.
Identifies gaps in documentation and generates reports.

Features:
- Checks for missing docstrings on functions and classes
- Validates OpenAPI/Swagger spec completeness
- Scans for missing README files in modules
- Checks parameter documentation completeness
- Assesses example code presence
- Generates documentation coverage reports

Usage:
    python agents/doc_completeness_agent.py --code-path app/
    python agents/doc_completeness_agent.py --code-path app/ --output reports/doc_coverage.json
    python agents/doc_completeness_agent.py --code-path app/ --min-coverage 80
"""

import argparse
import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class DocstringChecker:
    """Checks docstring completeness in Python code"""

    def __init__(self):
        self.total_functions = 0
        self.documented_functions = 0
        self.total_classes = 0
        self.documented_classes = 0
        self.total_modules = 0
        self.documented_modules = 0
        self.issues = []

    def check_file(self, file_path: str) -> Dict:
        """Check docstring coverage in a single file"""
        try:
            with open(file_path, "r") as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=file_path)

            result = {
                "file": file_path,
                "module_docstring": self._has_module_docstring(tree),
                "functions": [],
                "classes": [],
                "coverage": 0.0,
            }

            if result["module_docstring"]:
                self.documented_modules += 1
            self.total_modules += 1

            # Check functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._check_function(node)
                    result["functions"].append(func_info)

                    if func_info["has_docstring"]:
                        self.documented_functions += 1
                    self.total_functions += 1

                elif isinstance(node, ast.ClassDef):
                    class_info = self._check_class(node)
                    result["classes"].append(class_info)

                    if class_info["has_docstring"]:
                        self.documented_classes += 1
                    self.total_classes += 1

            # Calculate coverage
            total_items = len(result["functions"]) + len(result["classes"])
            documented_items = sum(
                1 for f in result["functions"] if f["has_docstring"]
            ) + sum(1 for c in result["classes"] if c["has_docstring"])

            result["coverage"] = (
                (documented_items / total_items * 100) if total_items > 0 else 100
            )

            return result

        except Exception as e:
            return {
                "file": file_path,
                "error": str(e),
                "functions": [],
                "classes": [],
                "coverage": 0.0,
            }

    def _has_module_docstring(self, tree: ast.AST) -> bool:
        """Check if module has docstring"""
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            return True
        return False

    def _check_function(self, func_node: ast.FunctionDef) -> Dict:
        """Check function docstring"""
        has_docstring = ast.get_docstring(func_node) is not None
        function_name = func_node.name

        # Check if private function (exempt from some checks)
        is_private = function_name.startswith("_")

        # Check if it has parameters
        has_params = len(func_node.args.args) > 0
        params = [
            arg.arg for arg in func_node.args.args if arg.arg not in ["self", "cls"]
        ]

        docstring = ast.get_docstring(func_node)
        doc_issues = []

        if docstring:
            # Check for parameter documentation
            if params:
                # Check if all parameters are documented
                documented_params = []
                for param in params:
                    if (
                        f":param {param}:" in docstring
                        or f"Args:\n    {param}" in docstring
                    ):
                        documented_params.append(param)

                missing_params = set(params) - set(documented_params)
                if missing_params:
                    doc_issues.append(
                        f"Missing parameter docs: {', '.join(missing_params)}"
                    )

            # Check for return documentation
            if (
                func_node.returns
                and ":return:" not in docstring
                and "Returns:" not in docstring
            ):
                doc_issues.append("Missing return documentation")

                # Check for raises documentation
                if "raise" in ast.unparse(func_node).lower():
                    doc_issues.append("Has raises but no raises documentation")
        else:
            if not is_private:
                doc_issues.append("No docstring")

        return {
            "name": function_name,
            "line": func_node.lineno,
            "is_private": is_private,
            "has_docstring": has_docstring,
            "parameters": params,
            "parameter_count": len(params),
            "has_return": func_node.returns is not None,
            "issues": doc_issues,
        }

    def _check_class(self, class_node: ast.ClassDef) -> Dict:
        """Check class docstring"""
        has_docstring = ast.get_docstring(class_node) is not None
        class_name = class_node.name

        # Count methods
        methods = []
        public_methods = []

        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                if not item.name.startswith("_"):
                    public_methods.append(item.name)

        return {
            "name": class_name,
            "line": class_node.lineno,
            "has_docstring": has_docstring,
            "total_methods": len(methods),
            "public_methods": len(public_methods),
        }

    def get_summary(self) -> Dict:
        """Get overall documentation summary"""
        function_coverage = (
            (self.documented_functions / self.total_functions * 100)
            if self.total_functions > 0
            else 100
        )
        class_coverage = (
            (self.documented_classes / self.total_classes * 100)
            if self.total_classes > 0
            else 100
        )
        module_coverage = (
            (self.documented_modules / self.total_modules * 100)
            if self.total_modules > 0
            else 100
        )

        return {
            "total_modules": self.total_modules,
            "documented_modules": self.documented_modules,
            "module_coverage": module_coverage,
            "total_functions": self.total_functions,
            "documented_functions": self.documented_functions,
            "function_coverage": function_coverage,
            "total_classes": self.total_classes,
            "documented_classes": self.documented_classes,
            "class_coverage": class_coverage,
            "overall_coverage": (function_coverage + class_coverage + module_coverage)
            / 3,
        }


class READMEChecker:
    """Checks for README files in project"""

    def __init__(self, code_path: str):
        self.code_path = code_path
        self.readme_files = []
        self.missing_readme = []

    def scan(self):
        """Scan for missing README files"""
        print(f"📄 Scanning for README files...")

        # Check for root README
        root_readme = Path(self.code_path).parent / "README.md"
        if not root_readme.exists():
            self.missing_readme.append("README.md (root)")

        # Check for README in subdirectories
        for root, dirs, files in os.walk(self.code_path):
            # Skip hidden directories and common excludes
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", "venv", "env", ".git"]
            ]

            # Check if directory has a README
            if any(f.startswith("README") for f in files):
                readme_path = os.path.join(
                    root, next(f for f in files if f.startswith("README"))
                )
                self.readme_files.append(readme_path)
            else:
                # Check if this is a meaningful directory (has Python files)
                py_files = [f for f in files if f.endswith(".py")]
                if py_files:
                    self.missing_readme.append(root)

    def get_summary(self) -> Dict:
        """Get README summary"""
        return {
            "readme_files_found": len(self.readme_files),
            "directories_missing_readme": len(self.missing_readme),
            "missing_readme_paths": self.missing_readme[:10],  # First 10
        }


class OpenAPISpecChecker:
    """Checks OpenAPI/Swagger spec completeness"""

    def __init__(self, spec_path: str = None):
        self.spec_path = spec_path
        self.spec = None
        self.issues = []

        if spec_path and os.path.exists(spec_path):
            self._load_spec()

    def _load_spec(self):
        """Load OpenAPI spec"""
        with open(self.spec_path, "r") as f:
            if self.spec_path.endswith(".json"):
                self.spec = json.load(f)
            else:
                import yaml

                self.spec = yaml.safe_load(f)

    def check(self) -> Dict:
        """Check OpenAPI spec completeness"""
        if not self.spec:
            return {
                "exists": False,
                "completeness": 0,
                "issues": ["No OpenAPI spec found"],
            }

        issues = []
        score = 100

        # Check required fields
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in self.spec:
                issues.append(f"Missing required field: {field}")
                score -= 20

        # Check info completeness
        if "info" in self.spec:
            info = self.spec["info"]
            info_fields = ["title", "version", "description"]
            for field in info_fields:
                if field not in info:
                    issues.append(f"Missing info.{field}")
                    score -= 10

        # Check paths documentation
        if "paths" in self.spec:
            paths = self.spec["paths"]

            for path, methods in paths.items():
                for method, details in methods.items():
                    endpoint_details = details

                    # Check for summary and description
                    if "summary" not in endpoint_details:
                        issues.append(f"No summary for {method.upper()} {path}")
                        score -= 5

                    if "description" not in endpoint_details:
                        issues.append(f"No description for {method.upper()} {path}")
                        score -= 5

                    # Check for response documentation
                    if "responses" not in endpoint_details:
                        issues.append(
                            f"No responses documented for {method.upper()} {path}"
                        )
                        score -= 10
                    else:
                        responses = endpoint_details["responses"]
                        if "200" not in responses and "2XX" not in responses:
                            issues.append(
                                f"No success response documented for {method.upper()} {path}"
                            )
                            score -= 5

        # Check for security schemes
        if "components" in self.spec and "securitySchemes" in self.spec["components"]:
            if not self.spec["components"]["securitySchemes"]:
                issues.append("No security schemes defined")
                score -= 10
        else:
            issues.append("No security schemes defined")
            score -= 10

        # Check for tags
        if "tags" not in self.spec or not self.spec["tags"]:
            issues.append("No tags defined")
            score -= 10

        return {
            "exists": True,
            "completeness": max(0, score),
            "issues": issues,
            "total_issues": len(issues),
        }


class DocumentationReporter:
    """Generates documentation completeness report"""

    def __init__(
        self,
        code_path: str,
        output_path: str = "reports/doc_coverage.json",
        spec_path: str = None,
    ):
        self.code_path = code_path
        self.output_path = output_path
        self.checker = DocstringChecker()
        self.readme_checker = READMEChecker(code_path)

        # Auto-detect OpenAPI spec if not provided
        if spec_path is None:
            # Try common locations
            for possible_spec in [
                "openapi.json",
                "swagger.json",
                "openapi.yaml",
                "swagger.yaml",
            ]:
                if os.path.exists(possible_spec):
                    spec_path = possible_spec
                    break
                # Also try relative to code path
                code_dir_spec = os.path.join(os.path.dirname(code_path), possible_spec)
                if os.path.exists(code_dir_spec):
                    spec_path = code_dir_spec
                    break

        self.spec_checker = OpenAPISpecChecker(spec_path)

    def scan_all(self) -> Dict:
        """Scan all documentation aspects"""
        print(f"📚 Documentation Completeness Assessment")
        print(f"   Code path: {self.code_path}")
        print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'-'*60}")

        # Scan Python files for docstrings
        print(f"\n📝 Scanning Python files...")
        file_results = []

        for root, dirs, files in os.walk(self.code_path):
            # Skip common excludes
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["__pycache__", "node_modules", "venv", "env"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    result = self.checker.check_file(file_path)
                    file_results.append(result)

                    # Collect issues
                    for func in result["functions"]:
                        for issue in func["issues"]:
                            self.checker.issues.append(
                                {
                                    "file": file_path,
                                    "function": func["name"],
                                    "line": func["line"],
                                    "issue": issue,
                                    "severity": (
                                        "minor" if "No docstring" in issue else "info"
                                    ),
                                }
                            )

        # Check README files
        print(f"\n📄 Checking README files...")
        self.readme_checker.scan()

        # Check OpenAPI spec
        print(f"\n📋 Checking OpenAPI spec...")
        spec_result = self.spec_checker.check()

        # Generate summary
        docstring_summary = self.checker.get_summary()
        readme_summary = self.readme_checker.get_summary()

        overall_score = (
            docstring_summary["overall_coverage"] * 0.5
            + (100 - readme_summary["directories_missing_readme"] * 2)  # 50% weight
            * 0.3
            + spec_result["completeness"] * 0.2  # 30% weight  # 20% weight
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "docstring_coverage": docstring_summary,
            "readme_coverage": readme_summary,
            "openapi_spec": spec_result,
            "files_scanned": len(file_results),
            "total_issues": len(self.checker.issues),
            "issues_by_severity": {
                "minor": sum(
                    1 for i in self.checker.issues if i["severity"] == "minor"
                ),
                "info": sum(1 for i in self.checker.issues if i["severity"] == "info"),
            },
            "recommendations": self._generate_recommendations(
                docstring_summary, readme_summary, spec_result
            ),
        }

        # Save report
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

        return report

    def _generate_recommendations(
        self, docstring_summary, readme_summary, spec_result
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if docstring_summary["overall_coverage"] < 80:
            recommendations.append("Improve docstring coverage to above 80%")

        if docstring_summary["function_coverage"] < 70:
            recommendations.append("Add docstrings to all public functions")

        if docstring_summary["class_coverage"] < 70:
            recommendations.append("Add docstrings to all classes")

        if readme_summary["directories_missing_readme"] > 5:
            recommendations.append(
                f"Add README files to {readme_summary['directories_missing_readme']} directories"
            )

        if not spec_result["exists"]:
            recommendations.append("Create OpenAPI/Swagger specification")
        elif spec_result["completeness"] < 70:
            recommendations.append(
                "Improve OpenAPI spec completeness (add descriptions, examples, etc.)"
            )

        return recommendations

    def _print_summary(self, report: Dict):
        """Print formatted summary"""
        print(f"\n{'='*60}")
        print(f"DOCUMENTATION COVERAGE REPORT")
        print(f"{'='*60}")

        print(f"\n📊 Overall Score: {report['overall_score']:.1f}/100")

        print(f"\n📝 Docstring Coverage:")
        print(f"   Modules: {report['docstring_coverage']['module_coverage']:.1f}%")
        print(f"   Functions: {report['docstring_coverage']['function_coverage']:.1f}%")
        print(f"   Classes: {report['docstring_coverage']['class_coverage']:.1f}%")
        print(f"   Overall: {report['docstring_coverage']['overall_coverage']:.1f}%")

        print(f"\n📄 README Files:")
        print(f"   Found: {report['readme_coverage']['readme_files_found']}")
        print(f"   Missing: {report['readme_coverage']['directories_missing_readme']}")

        print(f"\n📋 OpenAPI Spec:")
        if report["openapi_spec"]["exists"]:
            print(f"   Completeness: {report['openapi_spec']['completeness']:.1f}/100")
            print(f"   Issues: {report['openapi_spec']['total_issues']}")
        else:
            print(f"   No spec found")

        print(f"\n📂 Files Scanned: {report['files_scanned']}")
        print(f"   Total Issues: {report['total_issues']}")

        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        print(f"\n{'='*60}\n")

        # Exit with error if coverage is too low
        if report["overall_score"] < 50:
            print("❌ Documentation coverage below 50%. Please improve.")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Documentation Completeness Assessment Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan codebase for documentation gaps
  python agents/doc_completeness_agent.py --code-path app/

  # Generate report with custom output path
  python agents/doc_completeness_agent.py --code-path app/ --output reports/docs.json

  # Fail if coverage below threshold
  python agents/doc_completeness_agent.py --code-path app/ --min-coverage 80
        """,
    )

    parser.add_argument("--code-path", required=True, help="Path to code directory")
    parser.add_argument(
        "--output", default="reports/doc_coverage.json", help="Output report path"
    )
    parser.add_argument(
        "--spec-path",
        default=None,
        help="Path to OpenAPI/Swagger spec (auto-detected if not provided)",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0,
        help="Minimum acceptable coverage score (0-100)",
    )

    args = parser.parse_args()

    reporter = DocumentationReporter(args.code_path, args.output, args.spec_path)
    report = reporter.scan_all()

    if report["overall_score"] < args.min_coverage:
        sys.exit(1)


if __name__ == "__main__":
    main()
