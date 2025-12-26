#!/usr/bin/env python3
"""
SECURE RANDOM REPLACEMENT SCRIPT
Automatically finds and replaces insecure random usage with secrets module

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Security-sensitive patterns that require cryptographically secure random
SECURE_PATTERNS = {
    'token': r'\brandom\.(randint|choice|uniform)\([^)]*\).*token',
    'password': r'\brandom\.[^(]+\([^)]*\).*password',
    'key': r'\brandom\.[^(]+\([^)]*\).*key',
    'secret': r'\brandom\.[^(]+\([^)]*\).*secret',
    'session': r'\brandom\.[^(]+\([^)]*\).*session',
    'csrf': r'\brandom\.[^(]+\([^)]*\).*csrf',
    'nonce': r'\brandom\.[^(]+\([^)]*\).*nonce',
    'salt': r'\brandom\.[^(]+\([^)]*\).*salt',
    'otp': r'\brandom\.[^(]+\([^)]*\).*otp',
    'code': r'\brandom\.[^(]+\([^)]*\).*verification.*code',
}

# Files to exclude (test files, demos, etc.)
EXCLUDED_PATTERNS = [
    'test', 'spec', 'mock', 'fixture', 'demo', 'example',
    '__pycache__', '.venv', 'venv', 'node_modules'
]


class InsecureRandomFixer:
    """Find and fix insecure random usage"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixes_applied: List[Dict] = []
        self.skipped: List[Dict] = []
        self.errors: List[Dict] = []

    def is_excluded(self, file_path: Path) -> bool:
        """Check if file should be excluded from fixes"""
        path_str = str(file_path)

        for pattern in EXCLUDED_PATTERNS:
            if pattern in path_str:
                return True

        # Exclude files in common non-source directories
        parts = file_path.parts
        if any(excl in str(parts) for excl in ['__', 'venv', 'node_modules', '.git']):
            return True

        return False

    def find_insecure_random_usage(self, file_path: Path) -> List[Dict]:
        """Find all insecure random usage in a file"""
        findings = []

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            # Pattern 1: random.randint() in security contexts
            for pattern_name, pattern in SECURE_PATTERNS.items():
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            'line_num': line_num,
                            'type': 'security_context',
                            'pattern': pattern_name,
                            'line': line.strip(),
                            'severity': 'CRITICAL'
                        })

            # Pattern 2: random module imports (check if used for security)
            import_matches = re.finditer(r'^import random$|^from random import', content, re.MULTILINE)
            for match in import_matches:
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    'line_num': line_num,
                    'type': 'import',
                    'line': match.group(0).strip(),
                    'severity': 'WARNING'
                })

            # Pattern 3: Direct usage of random functions
            direct_patterns = [
                (r'\brandom\.random\(\)', 'secrets.SystemRandom().random()', 'secrets.randbelow(256) / 256'),
                (r'\brandom\.randint\((\d+),\s*(\d+)\)', 'random.randint(min, max)', 'secrets.randbelow(max - min) + min'),
                (r'\brandom\.choice\(([^)]+)\)', 'random.choice()', 'secrets.choice()'),
                (r'\brandom\.sample\(([^)]+)\)', 'secrets.SystemRandom().sample()', 'secrets.SystemRandom().sample()'),
                (r'\brandom\.shuffle\(([^)]+)\)', 'random.shuffle()', 'secrets.SystemRandom().shuffle()'),
                (r'\brandom\.randrange\(([^)]+)\)', 'random.randrange()', 'secrets.randbelow()'),
                (r'\brandom\.bytes\((\d+)\)', 'random.bytes(n)', 'secrets.token_bytes(n)'),
            ]

            for pattern, name, replacement in direct_patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    line = lines[line_num - 1].strip()

                    findings.append({
                        'line_num': line_num,
                        'type': 'direct_usage',
                        'function': name,
                        'line': line,
                        'replacement': replacement,
                        'severity': 'HIGH'
                    })

        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })

        return findings

    def suggest_fix(self, line: str, finding: Dict) -> str:
        """Suggest a fix for insecure random usage"""
        func = finding.get('function', '')
        replacement = finding.get('replacement', '')

        if replacement:
            return replacement

        # Generate specific suggestions based on pattern
        if 'randint' in line:
            # Extract min and max
            match = re.search(r'randint\((\d+),\s*(\d+)\)', line)
            if match:
                min_val, max_val = match.groups()
                return f"secrets.randbelow({max_val} - {min_val}) + {min_val}"

        if 'choice' in line:
            return 'secrets.choice()'

        if 'random()' in line:
            return 'secrets.SystemRandom().random()'

        if 'bytes' in line:
            return 'secrets.token_bytes()'

        return '# TODO: Replace with secrets module equivalent'

    def apply_fixes(self, dry_run: bool = False) -> Dict:
        """Scan and apply fixes to all Python files"""
        print("=" * 80)
        print("🔒 INSECURE RANDOM REPLACEMENT TOOL")
        print("=" * 80)

        all_findings = []

        # Find all Python files
        py_files = list(self.project_root.rglob("*.py"))
        py_files = [f for f in py_files if not self.is_excluded(f)]

        print(f"\n🔍 Scanning {len(py_files)} Python files...")
        print(f"   (Excluding test files and non-production code)\n")

        for file_path in py_files:
            findings = self.find_insecure_random_usage(file_path)

            if findings:
                all_findings.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'findings': findings
                })

        # Generate report
        total_findings = sum(len(f['findings']) for f in all_findings)
        critical_findings = sum(
            1 for f in all_findings
            for finding in f['findings']
            if finding.get('severity') == 'CRITICAL'
        )
        high_findings = sum(
            1 for f in all_findings
            for finding in f['findings']
            if finding.get('severity') == 'HIGH'
        )

        print(f"📊 SCAN RESULTS:")
        print(f"   Files with issues: {len(all_findings)}")
        print(f"   Total findings: {total_findings}")
        print(f"   Critical severity: {critical_findings}")
        print(f"   High severity: {high_findings}")

        if all_findings:
            print(f"\n🔴 CRITICAL SECURITY ISSUES FOUND:\n")

            for file_info in all_findings[:20]:  # Show first 20
                file = file_info['file']
                findings = file_info['findings']

                # Only show files with CRITICAL or HIGH findings
                critical = [f for f in findings if f.get('severity') in ['CRITICAL', 'HIGH']]
                if not critical:
                    continue

                print(f"\n📁 {file}")

                for finding in critical[:5]:  # Show first 5 per file
                    print(f"   Line {finding['line_num']}: {finding.get('severity', 'UNKNOWN')}")
                    print(f"   └─ {finding['line'][:80]}")

                    if 'replacement' in finding:
                        print(f"   └─ 💡 Replace with: {finding['replacement']}")
                    elif 'function' in finding:
                        suggestion = self.suggest_fix(finding['line'], finding)
                        print(f"   └─ 💡 Suggestion: {suggestion}")

            if len(all_findings) > 20:
                print(f"\n   ... and {len(all_findings) - 20} more files")

        # Generate automatic fix script
        if not dry_run:
            self.generate_fix_script(all_findings)

        return {
            'total_files': len(py_files),
            'files_with_issues': len(all_findings),
            'total_findings': total_findings,
            'critical': critical_findings,
            'high': high_findings,
            'errors': len(self.errors)
        }

    def generate_fix_script(self, findings: List[Dict]):
        """Generate a script to apply fixes automatically"""

        script_path = self.project_root / "apply_security_fixes.sh"

        # Create Python script instead of shell for better file handling
        fix_script_path = self.project_root / "apply_random_fixes.py"

        script_content = '''#!/usr/bin/env python3
"""
AUTO-GENERATED SECURE RANDOM REPLACEMENT SCRIPT
This script was generated by fix_insecure_random.py

RUN THIS SCRIPT TO APPLY SECURITY FIXES
"""

import re
from pathlib import Path

# Mapping of insecure patterns to secure replacements
REPLACEMENTS = [
    # Token generation
    (r'random\.randint\((\d+),\s*(\d+)\).*?(?:token|key)', lambda m: f"secrets.token_{16 if 'token' in m.group(0) else 'bytes'}(32)"),

    # Password/security related
    (r'random\.choice\([^)]+\).*?(?:password|secret|key)', 'secrets.token_urlsafe(32)'),

    # Generic high-security needs
    (r'random\.random\(\)', 'secrets.SystemRandom().random()'),
    (r'random\.randint\((\d+),\s*(\d+)\)', r'secrets.randbelow(\2 - \1) + \1'),
    (r'random\.choice\(([^)]+)\)', r'secrets.choice(\1)'),
]

def apply_fixes(file_path: Path):
    """Apply fixes to a single file"""
    try:
        content = file_path.read_text()
        original_content = content

        for pattern, replacement in REPLACEMENTS:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            else:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        if content != original_content:
            # Backup original
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            backup_path.write_text(original_content)

            # Write fixed content
            file_path.write_text(content)
            print(f"✅ Fixed: {file_path}")

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

if __name__ == "__main__":
    project_root = Path(__file__).parent

    print("🔧 Applying secure random fixes...")
    print("⚠️  Backups will be created as .backup files")
    print()

    # Apply fixes to all Python files (excluding tests)
    for py_file in project_root.rglob("*.py"):
        if 'test' not in str(py_file) and 'venv' not in str(py_file):
            apply_fixes(py_file)

    print()
    print("✨ Fixes applied! Review changes and remove .backup files when satisfied.")
'''

        fix_script_path.write_text(script_content)
        fix_script_path.chmod(0o755)

        print(f"\n✅ Generated fix script: {fix_script_path.name}")
        print(f"   Review and run: python {fix_script_path.name}")


def main():
    """Main entry point"""
    project_root = Path(os.path.dirname(os.path.abspath(__file__)))
    fixer = InsecureRandomFixer(project_root)

    # Dry run - just scan and report
    results = fixer.apply_fixes(dry_run=False)

    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print(f"\nFiles scanned: {results['total_files']}")
    print(f"Files with issues: {results['files_with_issues']}")
    print(f"Total findings: {results['total_findings']}")
    print(f"Critical issues: {results['critical']}")
    print(f"High severity: {results['high']}")

    if results['total_findings'] > 0:
        print("\n🔴 ACTION REQUIRED:")
        print("   1. Review the findings above")
        print("   2. Run 'python apply_random_fixes.py' to apply automatic fixes")
        print("   3. Manually review and test the changes")
        print("   4. Remove .backup files when satisfied")
        sys.exit(1)
    else:
        print("\n✅ No insecure random usage found!")
        sys.exit(0)


if __name__ == "__main__":
    main()
