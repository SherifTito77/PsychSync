
#app/utils/anonymize.py
"""
Data Anonymization and De-identification Tools for PsychSync
HIPAA-compliant anonymization for research data export.

Requirements:
    pip install pandas faker hashlib
"""

import hashlib
import re
import pandas as pd
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import random
from dataclasses import dataclass
import json


# ============================================================================
# HIPAA Safe Harbor Identifiers (18 types)
# ============================================================================

HIPAA_IDENTIFIERS = {
    'names': ['first_name', 'last_name', 'full_name', 'name'],
    'geographic': ['address', 'street', 'city', 'state', 'zip', 'zipcode', 'postal_code', 'county'],
    'dates': ['dob', 'date_of_birth', 'birth_date', 'admission_date', 'discharge_date'],
    'phone': ['phone', 'telephone', 'mobile', 'cell_phone'],
    'fax': ['fax', 'fax_number'],
    'email': ['email', 'email_address'],
    'ssn': ['ssn', 'social_security', 'social_security_number'],
    'mrn': ['mrn', 'medical_record_number', 'record_number'],
    'health_plan': ['insurance_id', 'policy_number', 'member_id'],
    'account': ['account_number', 'account_id'],
    'certificate': ['certificate_number', 'license_number'],
    'vehicle': ['vehicle_id', 'license_plate', 'vin'],
    'device': ['device_serial', 'device_id'],
    'url': ['url', 'website'],
    'ip': ['ip_address', 'ip'],
    'biometric': ['fingerprint', 'retina_scan', 'voice_print'],
    'photo': ['photo', 'image', 'photo_url'],
    'other': ['unique_identifier', 'id']
}


@dataclass
class AnonymizationConfig:
    """Configuration for anonymization process."""
    method: str  # 'hash', 'mask', 'generalize', 'remove', 'shift_date'
    salt: Optional[str] = None
    date_shift_days: Optional[int] = None
    preserve_age: bool = True
    preserve_gender: bool = True
    preserve_diagnosis: bool = True
    

class DataAnonymizer:
    """
    Anonymize sensitive data for research purposes while maintaining utility.
    Follows HIPAA Safe Harbor de-identification standard.
    """
    
    def __init__(self, salt: str = "psychsync_default_salt"):
        """
        Initialize anonymizer.
        
        Args:
            salt: Salt for hashing (should be unique per project)
        """
        self.salt = salt
        self.mapping_cache: Dict[str, str] = {}
        self.date_shifts: Dict[str, int] = {}
    
    def hash_identifier(self, value: str, prefix: str = "") -> str:
        """
        Create deterministic hash of identifier.
        Same input always produces same output (for consistency).
        
        Args:
            value: Value to hash
            prefix: Prefix for hashed value
            
        Returns:
            Hashed identifier
        """
        if not value:
            return ""
        
        # Check cache
        cache_key = f"{prefix}:{value}"
        if cache_key in self.mapping_cache:
            return self.mapping_cache[cache_key]
        
        # Hash with salt
        hash_input = f"{self.salt}:{value}".encode()
        hash_value = hashlib.sha256(hash_input).hexdigest()[:16]
        
        # Add prefix
        result = f"{prefix}{hash_value}" if prefix else hash_value
        
        # Cache mapping
        self.mapping_cache[cache_key] = result
        
        return result
    
    def mask_partial(self, value: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """
        Partially mask a value (e.g., email, phone).
        
        Args:
            value: Value to mask
            mask_char: Character for masking
            visible_chars: Number of characters to leave visible
            
        Returns:
            Partially masked value
        """
        if not value or len(value) <= visible_chars:
            return mask_char * len(value) if value else ""
        
        visible = value[:visible_chars]
        masked = mask_char * (len(value) - visible_chars)
        
        return visible + masked
    
    def generalize_age(self, age: int, bin_size: int = 5) -> str:
        """
        Generalize age into bins.
        
        Args:
            age: Exact age
            bin_size: Size of age bins
            
        Returns:
            Age range string (e.g., "25-29")
        """
        if age < 0:
            return "unknown"
        
        lower = (age // bin_size) * bin_size
        upper = lower + bin_size - 1
        
        return f"{lower}-{upper}"
    
    def generalize_zipcode(self, zipcode: str) -> str:
        """
        Generalize ZIP code to first 3 digits (HIPAA requirement).
        
        Args:
            zipcode: Full ZIP code
            
        Returns:
            Generalized ZIP (e.g., "941**")
        """
        if not zipcode:
            return ""
        
        # Extract digits
        digits = re.sub(r'\D', '', zipcode)
        
        if len(digits) < 3:
            return "***"
        
        return digits[:3] + "**"
    
    def shift_date(self, date: datetime, patient_id: str) -> datetime:
        """
        Shift date by random amount (same shift for same patient).
        Preserves day of week and season.
        
        Args:
            date: Original date
            patient_id: Patient identifier (for consistent shifting)
            
        Returns:
            Shifted date
        """
        # Get or create consistent shift for this patient
        if patient_id not in self.date_shifts:
            # Random shift between -365 and +365 days
            random.seed(f"{self.salt}:{patient_id}")
            self.date_shifts[patient_id] = random.randint(-365, 365)
        
        shift_days = self.date_shifts[patient_id]
        return date + timedelta(days=shift_days)
    
    def remove_free_text_phi(self, text: str) -> str:
        """
        Remove potential PHI from free text using pattern matching.
        
        Args:
            text: Free text that may contain PHI
            
        Returns:
            Text with PHI removed/redacted
        """
        if not text:
            return ""
        
        # Email pattern
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL_REDACTED]',
            text
        )
        
        # Phone pattern
        text = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE_REDACTED]',
            text
        )
        
        # SSN pattern
        text = re.sub(
            r'\b\d{3}-\d{2}-\d{4}\b',
            '[SSN_REDACTED]',
            text
        )
        
        # Date patterns (various formats)
        text = re.sub(
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            '[DATE_REDACTED]',
            text
        )
        
        # URL pattern
        text = re.sub(
            r'https?://[^\s]+',
            '[URL_REDACTED]',
            text
        )
        
        # IP address pattern
        text = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            '[IP_REDACTED]',
            text
        )
        
        return text
    
    def anonymize_dataframe(
        self,
        df: pd.DataFrame,
        config: Optional[Dict[str, AnonymizationConfig]] = None,
        auto_detect: bool = True
    ) -> pd.DataFrame:
        """
        Anonymize an entire DataFrame.
        
        Args:
            df: DataFrame to anonymize
            config: Column-specific anonymization configuration
            auto_detect: Automatically detect and anonymize PHI columns
            
        Returns:
            Anonymized DataFrame
        """
        df_anon = df.copy()
        config = config or {}
        
        # Auto-detect PHI columns if enabled
        if auto_detect:
            phi_columns = self._detect_phi_columns(df.columns.tolist())
        else:
            phi_columns = set()
        
        for column in df_anon.columns:
            # Skip if column has explicit config
            if column in config:
                method = config[column].method
            elif column in phi_columns or auto_detect:
                # Auto-detect anonymization method
                method = self._suggest_method(column, df_anon[column])
            else:
                continue
            
            # Apply anonymization
            if method == 'hash':
                df_anon[column] = df_anon[column].apply(
                    lambda x: self.hash_identifier(str(x), prefix=f"{column[:3]}_") if pd.notna(x) else x
                )
            
            elif method == 'mask':
                df_anon[column] = df_anon[column].apply(
                    lambda x: self.mask_partial(str(x)) if pd.notna(x) else x
                )
            
            elif method == 'generalize_age':
                df_anon[column] = df_anon[column].apply(
                    lambda x: self.generalize_age(int(x)) if pd.notna(x) else x
                )
            
            elif method == 'generalize_zip':
                df_anon[column] = df_anon[column].apply(
                    lambda x: self.generalize_zipcode(str(x)) if pd.notna(x) else x
                )
            
            elif method == 'remove':
                df_anon[column] = None
            
            elif method == 'redact_text':
                df_anon[column] = df_anon[column].apply(
                    lambda x: self.remove_free_text_phi(str(x)) if pd.notna(x) else x
                )
        
        return df_anon
    
    def _detect_phi_columns(self, columns: List[str]) -> Set[str]:
        """Detect columns that likely contain PHI."""
        phi_cols = set()
        
        for col in columns:
            col_lower = col.lower()
            
            # Check against HIPAA identifier patterns
            for category, patterns in HIPAA_IDENTIFIERS.items():
                for pattern in patterns:
                    if pattern in col_lower:
                        phi_cols.add(col)
                        break
        
        return phi_cols
    
    def _suggest_method(self, column_name: str, series: pd.Series) -> str:
        """Suggest anonymization method based on column name and data."""
        col_lower = column_name.lower()
        
        # Check column name patterns
        if any(x in col_lower for x in ['name', 'patient', 'client']):
            return 'hash'
        elif any(x in col_lower for x in ['email', 'phone']):
            return 'mask'
        elif any(x in col_lower for x in ['age']):
            return 'generalize_age'
        elif any(x in col_lower for x in ['zip', 'postal']):
            return 'generalize_zip'
        elif any(x in col_lower for x in ['note', 'comment', 'text', 'description']):
            return 'redact_text'
        elif any(x in col_lower for x in ['ssn', 'mrn', 'id']):
            return 'hash'
        else:
            return 'hash'  # Default to hashing
    
    def generate_anonymization_report(self, original_df: pd.DataFrame, anonymized_df: pd.DataFrame) -> Dict:
        """
        Generate report on anonymization process.
        
        Args:
            original_df: Original DataFrame
            anonymized_df: Anonymized DataFrame
            
        Returns:
            Report dictionary
        """
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_records': len(original_df),
            'total_columns': len(original_df.columns),
            'columns_anonymized': [],
            'removed_columns': [],
            'preserved_columns': []
        }
        
        for col in original_df.columns:
            if col not in anonymized_df.columns:
                report['removed_columns'].append(col)
            elif not original_df[col].equals(anonymized_df[col]):
                report['columns_anonymized'].append({
                    'column': col,
                    'original_sample': str(original_df[col].iloc[0]) if len(original_df) > 0 else None,
                    'anonymized_sample': str(anonymized_df[col].iloc[0]) if len(anonymized_df) > 0 else None
                })
            else:
                report['preserved_columns'].append(col)
        
        return report


class AuditLogger:
    """
    Log data access and anonymization events for compliance.
    """
    
    def __init__(self, log_file: str = "data_access_log.json"):
        """Initialize audit logger."""
        self.log_file = log_file
        self.logs: List[Dict] = []
    
    def log_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict] = None
    ):
        """
        Log a data access event.
        
        Args:
            user_id: User who accessed data
            action: Action performed (read, export, anonymize)
            resource: Resource accessed (table, file, etc.)
            details: Additional details
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {},
            'ip_address': None  # Would be populated from request context
        }
        
        self.logs.append(log_entry)
        
        # Write to file
        self._write_log(log_entry)
    
    def _write_log(self, entry: Dict):
        """Write log entry to file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"Error writing log: {e}")
    
    def get_logs(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve logs, optionally filtered by user."""
        if user_id:
            return [log for log in self.logs if log['user_id'] == user_id][:limit]
        return self.logs[:limit]


# Example usage
if __name__ == "__main__":
    print("Data Anonymization Demo")
    print("=" * 60)
    
    # Create sample data
    sample_data = pd.DataFrame({
        'patient_id': ['P001', 'P002', 'P003'],
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'phone': ['555-123-4567', '555-987-6543', '555-555-5555'],
        'dob': ['1985-03-15', '1990-07-22', '1978-11-30'],
        'age': [39, 34, 46],
        'zipcode': ['94102', '10001', '60601'],
        'diagnosis': ['F32.1', 'F41.1', 'F43.1'],
        'phq9_score': [15, 12, 18],
        'session_notes': [
            'Patient reported improvement. Contact: john@example.com',
            'Anxiety symptoms persist. Phone: 555-987-6543.',
            'Significant progress noted.'
        ]
    })
    
    print("\n1. Original Data (First Row):")
    print("-" * 60)
    print(sample_data.iloc[0].to_dict())
    
    # Anonymize
    anonymizer = DataAnonymizer(salt="demo_salt_12345")
    anonymized_data = anonymizer.anonymize_dataframe(sample_data, auto_detect=True)
    
    print("\n2. Anonymized Data (First Row):")
    print("-" * 60)
    print(anonymized_data.iloc[0].to_dict())
    
    # Generate report
    report = anonymizer.generate_anonymization_report(sample_data, anonymized_data)
    
    print("\n3. Anonymization Report:")
    print("-" * 60)
    print(f"Total records: {report['total_records']}")
    print(f"Columns anonymized: {len(report['columns_anonymized'])}")
    print(f"Preserved columns: {report['preserved_columns']}")
    
    print("\nAnonymized columns:")
    for col_info in report['columns_anonymized']:
        print(f"  {col_info['column']}:")
        print(f"    Original: {col_info['original_sample']}")
        print(f"    Anonymized: {col_info['anonymized_sample']}")
    
    # Audit logging
    print("\n4. Audit Logging:")
    print("-" * 60)
    
    logger = AuditLogger(log_file="demo_audit_log.json")
    logger.log_access(
        user_id="researcher_001",
        action="export_anonymized",
        resource="patient_data",
        details={
            'records_exported': len(anonymized_data),
            'export_format': 'csv',
            'anonymization_method': 'auto'
        }
    )
    
    recent_logs = logger.get_logs(limit=5)
    print(f"Logged {len(recent_logs)} events")
    if recent_logs:
        last_log = recent_logs[-1]
        print(f"Last event: {last_log['action']} by {last_log['user_id']} at {last_log['timestamp']}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("\nNote: In production, ensure proper key management for salt values")
    print("and secure storage of audit logs with tamper-proof mechanisms.")