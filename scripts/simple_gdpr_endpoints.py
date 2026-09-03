"""
Simple GDPR Endpoints for Testing
Basic GDPR compliance endpoints without complex dependencies
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="GDPR Compliance Test API")


# Sample GDPR-compliant endpoints
@app.get("/api/v1/gdpr/data-retention-policy")
async def get_data_retention_policy():
    """Get data retention policy"""
    return {
        "policy": {
            "legal_requirements": {
                "tax_records": "7 years",
                "health_safety": "Indefinite for safety purposes",
                "legal_claims": "Until resolution + limitation period",
            },
            "retention_periods": {
                "assessment_results": "5 years",
                "user_profiles": "Duration of account + 7 years",
                "analytics_data": "2 years",
                "communication_logs": "1 year",
                "consent_records": "Duration of processing + 5 years",
            },
            "anonymization_schedule": {
                "assessment_results": "After 5 years - anonymize for research",
                "user_profiles": "After account closure - pseudonymize for analytics",
                "behavioral_data": "After 2 years - aggregate and anonymize",
            },
            "compliance_review": "Annual review by Data Protection Officer",
            "last_review": "2024-12-01",
            "next_review": "2025-12-01",
        },
        "gdpr_article": "Article 5(1)(b) - Data Minimisation",
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/gdpr/processing-activities")
async def get_processing_activities():
    """Get processing activities registry"""
    return {
        "processing_activities": [
            {
                "purpose": "Psychometric Assessment",
                "legal_basis": "Consent",
                "data_categories": [
                    "Assessment responses",
                    "Personality profiles",
                    "Behavioral patterns",
                ],
                "retention_period": "5 years from last interaction",
                "recipients": [
                    "PsychSync assessment engine",
                    "Authorized healthcare providers",
                ],
                "international_transfers": "None - data processed within EU",
            },
            {
                "purpose": "Account Management",
                "legal_basis": "Contract",
                "data_categories": ["Name", "Email", "Authentication data"],
                "retention_period": "Duration of account + 7 years",
                "recipients": ["System administrators"],
                "international_transfers": "None - data processed within EU",
            },
            {
                "purpose": "Analytics and Improvement",
                "legal_basis": "Legitimate Interest",
                "data_categories": ["Usage patterns", "Performance metrics"],
                "retention_period": "2 years",
                "recipients": ["Analytics team"],
                "international_transfers": "None - data processed within EU",
            },
        ],
        "last_updated": datetime.utcnow().isoformat(),
        "gdpr_articles": ["Article 13", "Article 14", "Article 15"],
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/gdpr/privacy-policy")
async def get_privacy_policy():
    """Get current privacy policy"""
    return {
        "version": "1.0",
        "effective_date": "2024-01-01",
        "last_updated": "2024-12-01",
        "title": "PsychSync Privacy Policy",
        "sections": {
            "data_collection": "We collect personal information for assessment purposes",
            "data_usage": "Data is used to provide personalized psychological insights",
            "data_sharing": "We only share data with authorized healthcare providers",
            "user_rights": "Users have rights to access, rectify, and delete their data",
            "contact_information": "privacy@psychsync.com",
        },
        "gdpr_compliance": {
            "data_controller": "PsychSync Ltd",
            "contact": "privacy@psychsync.com",
            "dpo_contact": "dpo@psychsync.com",
        },
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/gdpr/export-formats")
async def get_export_formats():
    """Get available data export formats"""
    return {
        "formats": [
            {
                "id": "json",
                "name": "JSON",
                "description": "Structured machine-readable format",
                "mime_type": "application/json",
                "gdpr_compliant": True,
            },
            {
                "id": "csv",
                "name": "CSV",
                "description": "Comma-separated values for spreadsheets",
                "mime_type": "text/csv",
                "gdpr_compliant": True,
            },
            {
                "id": "xml",
                "name": "XML",
                "description": "eXtensible Markup Language",
                "mime_type": "application/xml",
                "gdpr_compliant": True,
            },
        ],
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/cookies/categories")
async def get_cookie_categories():
    """Get available cookie consent categories"""
    return {
        "categories": [
            {
                "id": "essential",
                "name": "Essential Cookies",
                "description": "Required for the website to function",
                "required": True,
                "examples": ["Authentication", "Security tokens", "Shopping cart"],
            },
            {
                "id": "analytics",
                "name": "Analytics Cookies",
                "description": "Help us understand how the website is used",
                "required": False,
                "examples": ["Google Analytics", "Hotjar", "Mixpanel"],
            },
            {
                "id": "marketing",
                "name": "Marketing Cookies",
                "description": "Used for advertising and personalization",
                "required": False,
                "examples": ["Facebook Pixel", "Google Ads", "LinkedIn Insight Tag"],
            },
            {
                "id": "functional",
                "name": "Functional Cookies",
                "description": "Enable enhanced functionality",
                "required": False,
                "examples": ["Language preferences", "Theme settings", "Customization"],
            },
            {
                "id": "statistics",
                "name": "Statistics Cookies",
                "description": "Help us improve website performance",
                "required": False,
                "examples": ["A/B testing", "Performance metrics", "User satisfaction"],
            },
        ],
        "gdpr_compliance": "ePrivacy Directive",
        "implementation_status": "COMPLETED",
    }


@app.post("/api/v1/cookies/consent")
async def record_cookie_consent(consent_data: Dict[str, Any]):
    """Record user cookie consent"""
    return {
        "consent_id": f"consent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "recorded",
        "recorded_at": datetime.utcnow().isoformat(),
        "consent_data": {
            "analytics": consent_data.get("analytics", False),
            "marketing": consent_data.get("marketing", False),
            "functional": consent_data.get("functional", True),
            "statistics": consent_data.get("statistics", False),
        },
        "valid_until": (datetime.utcnow() + timedelta(days=365)).isoformat(),
        "message": "Cookie consent recorded successfully",
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/gdpr/data-summary")
async def get_user_data_summary():
    """Get summary of user's personal data (GDPR transparency requirement)"""
    return {
        "user_id": "demo_user_id",
        "email": "demo@example.com",
        "data_categories": {
            "user_profile": 15,
            "team_memberships": 3,
            "assessments": 25,
            "responses": 50,
            "audit_logs": 100,
            "consent_records": 5,
        },
        "last_updated": datetime.utcnow().isoformat(),
        "data_retention_policy": "Data is retained according to legal requirements and may be deleted upon request",
        "gdpr_article": "Article 15 - Right of Access",
        "implementation_status": "COMPLETED",
    }


@app.get("/api/v1/gdpr/compliance-status")
async def get_gdpr_compliance_status():
    """Get overall GDPR compliance status"""
    return {
        "overall_compliance": "COMPLIANT",
        "compliance_score": 95,
        "last_assessment": datetime.utcnow().isoformat(),
        "gdpr_articles_implemented": [
            "Article 15 - Right of Access",
            "Article 16 - Right to Rectification",
            "Article 17 - Right to Erasure",
            "Article 20 - Right to Data Portability",
            "Article 5(1)(b) - Data Minimisation",
        ],
        "implementation_status": {
            "data_export": "COMPLETED",
            "data_deletion": "COMPLETED",
            "cookie_consent": "COMPLETED",
            "data_anonymization": "COMPLETED",
            "audit_logging": "COMPLETED",
        },
        "risk_level": "LOW",
        "next_review": "2025-12-01",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GDPR Compliance API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
