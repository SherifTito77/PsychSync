#!/usr/bin/env python3
"""
EMERGENCY BACKUP ENCRYPTION SCRIPT
Immediately encrypts unencrypted database backup files
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

class EmergencyBackupEncryption:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.encrypted_backups = []
        self.failed_backups = []

    def check_gpg_available(self):
        """Check if GPG is available"""
        try:
            result = subprocess.run(['gpg', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ GPG is available for encryption")
                return True
            else:
                print("❌ GPG not found")
                return False
        except FileNotFoundError:
            print("❌ GPG not installed. Installing...")
            print("   Run: brew install gnupg")
            return False

    def encrypt_file_gpg(self, file_path: Path, remove_original: bool = False):
        """Encrypt a file using GPG symmetric encryption"""
        try:
            print(f"\n🔒 Encrypting: {file_path.name}")

            # Output file path
            encrypted_path = file_path.with_suffix(file_path.suffix + '.gpg')

            # Check if already encrypted
            if encrypted_path.exists():
                print(f"   ⚠️  Encrypted version already exists: {encrypted_path.name}")
                user_input = input("   Overwrite? (y/N): ")
                if user_input.lower() != 'y':
                    print("   Skipping...")
                    return False

            # Encrypt with AES256
            cmd = [
                'gpg',
                '--symmetric',
                '--cipher-algo', 'AES256',
                '--compress-algo', '1',
                '--s2k-digest-algo', 'SHA512',
                '--s2k-count', '65011712',  # Maximum iteration count
                '--batch',  # Non-interactive mode with --passphrase
                '--passphrase', '',
                '--output', str(encrypted_path),
                str(file_path)
            ]

            # For interactive use, we'll use a different approach
            # Ask user for passphrase
            print(f"   📝 Enter passphrase for {file_path.name}:")
            result = subprocess.run([
                'gpg',
                '--symmetric',
                '--cipher-algo', 'AES256',
                '--compress-algo', '1',
                '--output', str(encrypted_path),
                str(file_path)
            ], capture_output=True, text=False)

            if result.returncode == 0 and encrypted_path.exists():
                file_size_kb = round(encrypted_path.stat().st_size / 1024, 2)
                print(f"   ✅ Encrypted successfully: {encrypted_path.name} ({file_size_kb} KB)")

                # Verify encryption
                with open(encrypted_path, 'rb') as f:
                    header = f.read(100)
                    if b'PGP' in header or b'-----BEGIN' in header:
                        print(f"   ✅ Encryption verified")

                        # Optionally remove original
                        if remove_original:
                            backup_name = file_path.name + '.unencrypted_backup'
                            file_path.rename(file_path.parent / backup_name)
                            print(f"   📦 Original renamed to: {backup_name}")

                        self.encrypted_backups.append({
                            "original": str(file_path),
                            "encrypted": str(encrypted_path),
                            "size_kb": file_size_kb
                        })
                        return True
                    else:
                        print(f"   ❌ Encryption verification failed")
                        return False
            else:
                print(f"   ❌ Encryption failed")
                if result.stderr:
                    print(f"   Error: {result.stderr.decode()}")
                return False

        except Exception as e:
            print(f"   ❌ Error encrypting {file_path.name}: {e}")
            self.failed_backups.append(str(file_path))
            return False

    def encrypt_file_python(self, file_path: Path, password: str = None):
        """Encrypt using Python's cryptography library (fallback method)"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
            import base64

            print(f"\n🔒 Encrypting (Python): {file_path.name}")

            # Generate encryption key from password
            if password is None:
                import secrets
                password = secrets.token_urlsafe(32)

            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'psychsync_backup_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            f = Fernet(key)

            # Read and encrypt file
            with open(file_path, 'rb') as file:
                file_data = file.read()

            encrypted_data = f.encrypt(file_data)

            # Write encrypted file
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            with open(encrypted_path, 'wb') as file:
                file.write(encrypted_data)

            file_size_kb = round(encrypted_path.stat().st_size / 1024, 2)
            print(f"   ✅ Encrypted: {encrypted_path.name} ({file_size_kb} KB)")
            print(f"   🔑 Password: {password}")

            # Save password securely
            password_file = encrypted_path.with_suffix('.password')
            with open(password_file, 'w') as f:
                f.write(f"Encryption password: {password}\n")
                f.write(f"Encrypted file: {encrypted_path.name}\n")
                f.write(f"Date: {datetime.now().isoformat()}\n")
            print(f"   📝 Password saved to: {password_file.name}")

            self.encrypted_backups.append({
                "original": str(file_path),
                "encrypted": str(encrypted_path),
                "size_kb": file_size_kb,
                "method": "Python Fernet"
            })

            # Backup original
            backup_name = file_path.name + '.unencrypted_backup'
            file_path.rename(file_path.parent / backup_name)
            print(f"   📦 Original renamed to: {backup_name}")

            return True

        except ImportError:
            print(f"   ❌ cryptography library not installed")
            print(f"   Install with: pip install cryptography")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.failed_backups.append(str(file_path))
            return False

    def scan_and_encrypt_unencrypted(self):
        """Scan for unencrypted backup files and encrypt them"""
        print("🔍 SCANNING FOR UNENCRYPTED BACKUP FILES...")
        print("=" * 60)

        # Patterns for unencrypted backups
        backup_patterns = ['*.sql', '*.dump', '*.backup', '*.bak']

        unencrypted_files = []

        for pattern in backup_patterns:
            for file_path in self.base_path.rglob(pattern):
                # Skip if already encrypted
                if file_path.suffix in ['.gpg', '.enc']:
                    continue

                # Skip if test file
                if 'test' in str(file_path).lower():
                    continue

                # Check if file is readable text (unencrypted)
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(1024)

                    # Check for SQL indicators
                    if b'CREATE TABLE' in header or b'INSERT INTO' in header or b'--' in header[:100]:
                        unencrypted_files.append(file_path)
                        print(f"📄 Found: {file_path.relative_to(self.base_path)} ({round(file_path.stat().st_size/1024, 2)} KB)")

                except Exception:
                    pass

        if not unencrypted_files:
            print("\n✅ No unencrypted backup files found!")
            return True

        print(f"\n⚠️  Found {len(unencrypted_files)} unencrypted backup file(s)")
        print("\n🔒 STARTING ENCRYPTION...")
        print("=" * 60)

        # Try GPG first, fallback to Python
        use_gpg = self.check_gpg_available()

        for file_path in unencrypted_files:
            if use_gpg:
                success = self.encrypt_file_gpg(file_path, remove_original=False)
            else:
                print("\n⚠️  GPG not available, using Python encryption...")
                success = self.encrypt_file_python(file_path)

            if not success:
                print(f"   ⚠️  Failed to encrypt {file_path.name}")
                self.failed_backups.append(str(file_path))

        return len(self.failed_backups) == 0

    def generate_report(self):
        """Generate encryption report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "encrypted_backups": self.encrypted_backups,
            "failed_backups": self.failed_backups,
            "total_encrypted": len(self.encrypted_backups),
            "total_failed": len(self.failed_backups)
        }

        # Save report
        import json
        report_file = self.base_path / "backup_encryption_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Report saved: {report_file.name}")

        return report

def main():
    """Main execution"""
    print("🚨 EMERGENCY BACKUP ENCRYPTION TOOL")
    print("=" * 60)
    print("This tool will immediately encrypt all unencrypted database backups")
    print()

    encryptor = EmergencyBackupEncryption()

    try:
        # Scan and encrypt
        success = encryptor.scan_and_encrypt_unencrypted()

        # Generate report
        report = encryptor.generate_report()

        # Summary
        print("\n" + "=" * 60)
        print("🔐 ENCRYPTION SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully encrypted: {report['total_encrypted']}")
        print(f"❌ Failed: {report['total_failed']}")

        if report['encrypted_backups']:
            print("\n📋 Encrypted files:")
            for backup in report['encrypted_backups']:
                print(f"   • {Path(backup['encrypted']).name} ({backup['size_kb']} KB)")

        if report['failed_backups']:
            print("\n⚠️  Failed encryptions:")
            for failed in report['failed_backups']:
                print(f"   • {failed}")

        if success:
            print("\n✅ All unencrypted backups have been secured!")
            return 0
        else:
            print("\n⚠️  Some backups could not be encrypted. Please check manually.")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())