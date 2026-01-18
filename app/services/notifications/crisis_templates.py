# app/services/notifications/crisis_templates.py
"""
Crisis notification templates for email, SMS, and push notifications
HIPAA-compliant, immediate delivery for crisis situations

@author PsychSync Clinical Team
@version 1.0.0
"""

from typing import Dict, Optional
from datetime import datetime


class CrisisNotificationTemplates:
    """
    Templates for crisis intervention notifications
    All templates designed for immediate, clear communication

    Features:
    - HTML and plain text versions
    - Mobile-responsive
    - Accessibility-compliant
    - HIPAA-compliant disclaimers
    - Multi-language support ready
    """

    # ========================================================================
    # LEVEL 1: CRITICAL - IMMEDIATE DANGER
    # ========================================================================

    @staticmethod
    def critical_alert_email(user_name: str, screening_type: str, score: int) -> Dict[str, str]:
        """
        Email sent immediately when CRITICAL risk detected

        Args:
            user_name: Patient's name
            screening_type: Type of screening (PHQ9, GAD7, etc.)
            score: Assessment score

        Returns:
            Dictionary with subject, html_body, and text_body
        """
        return {
            "subject": "🚨 URGENT: Immediate Mental Health Support Available",
            "html_body": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Immediate Support Available</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .critical-banner {{ background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); color: white; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 24px; }}
        .crisis-box {{ background: #FEF2F2; border-left: 4px solid #DC2626; padding: 24px; margin: 24px 0; border-radius: 8px; }}
        .button {{ display: inline-block; padding: 16px 32px; background: #DC2626; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 12px 6px; transition: background 0.3s; }}
        .button:hover {{ background: #B91C1C; }}
        .resource-list {{ background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .resource-item {{ padding: 16px; border-bottom: 1px solid #E5E7EB; }}
        .resource-item:last-child {{ border-bottom: none; }}
        .resource-title {{ font-weight: bold; color: #DC2626; font-size: 18px; margin-bottom: 4px; }}
        .resource-desc {{ color: #6B7280; font-size: 14px; margin-top: 4px; }}
        .icon {{ font-size: 24px; margin-right: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="critical-banner">
            <h1 style="margin: 0; font-size: 28px;">🚨 IMMEDIATE SUPPORT NEEDED</h1>
            <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">We're Here to Help - Right Now</p>
        </div>

        <p>Dear {user_name},</p>

        <div class="crisis-box">
            <h2 style="color: #DC2626; margin-top: 0; font-size: 22px;">You're Not Alone - Help is Available Immediately</h2>
            <p style="font-size: 17px; font-weight: 500; line-height: 1.6; margin: 16px 0;">
                Your recent <strong>{screening_type}</strong> assessment (Score: {score}) indicates you may be experiencing significant distress.
                <strong style="color: #DC2626;">You don't have to face this alone - help is available right now.</strong>
            </p>
        </div>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 16px 0;">🚨 GET IMMEDIATE SUPPORT:</h3>

        <div class="resource-list">
            <div class="resource-item">
                <div class="resource-title">
                    <span class="icon">📞</span>988 Suicide & Crisis Lifeline
                </div>
                <p class="resource-desc">Available 24/7 - Free, Confidential, Supportive</p>
                <a href="tel:988" class="button" style="display: block; text-align: center; margin: 16px 0 8px 0;">Call 988 Now</a>
            </div>

            <div class="resource-item">
                <div class="resource-title">
                    <span class="icon">💬</span>Crisis Text Line
                </div>
                <p class="resource-desc">Text-based support available 24/7</p>
                <p style="font-size: 18px; font-weight: bold; color: #DC2626; margin: 8px 0;">Text "HELLO" to 741741</p>
            </div>

            <div class="resource-item">
                <div class="resource-title">
                    <span class="icon">🏥</span>Emergency Services
                </div>
                <p class="resource-desc">If you are in immediate danger</p>
                <a href="tel:911" class="button" style="background: #059669; display: block; text-align: center; margin: 16px 0 8px 0;">Call 911</a>
            </div>

            <div class="resource-item">
                <div class="resource-title">
                    <span class="icon">🌐</span>Online Chat Support
                </div>
                <p class="resource-desc">Connect with a crisis counselor online</p>
                <a href="https://suicidepreventionlifeline.org/chat/" target="_blank" class="button" style="background: #2563EB; display: block; text-align: center; margin: 16px 0 8px 0;">Start Live Chat</a>
            </div>
        </div>

        <div style="background: #EFF6FF; border-left: 4px solid #2563EB; padding: 24px; margin: 24px 0; border-radius: 8px;">
            <h3 style="color: #1E40AF; margin-top: 0; font-size: 18px;">What Happens Next:</h3>
            <ol style="color: #1E3A8A; line-height: 1.8; padding-left: 20px;">
                <li style="margin-bottom: 8px;"><strong>A licensed clinician will contact you within 2 hours</strong></li>
                <li style="margin-bottom: 8px;">We'll help you create a personalized safety plan</li>
                <li style="margin-bottom: 8px;">We'll connect you with appropriate mental health services</li>
                <li style="margin-bottom: 8px;">We'll schedule follow-up support and check-ins</li>
                <li>You're never alone - we're with you every step of the way</li>
            </ol>
        </div>

        <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border-left: 4px solid #059669; padding: 24px; margin: 24px 0; border-radius: 8px;">
            <p style="margin: 0; color: #065F46; font-size: 17px; font-weight: 500;">
                <strong style="font-size: 20px;">💚 You Matter</strong><br>
                Crisis feelings are temporary, but your life has permanent value.
                With the right support, things can and will get better.
                We're here to help you through this moment.
            </p>
        </div>

        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 32px 0;">

        <div style="font-size: 13px; color: #6B7280; line-height: 1.6;">
            <p style="margin: 0 0 8px 0;"><strong>Confidential & Secure:</strong></p>
            <p style="margin: 0 0 16px 0;">
                This message is confidential and protected under HIPAA. Your privacy and safety are our top priorities.
            </p>
            <p style="margin: 0 0 8px 0;">If you did not complete a mental health assessment with PsychSync, please disregard this message.</p>
        </div>

        <div style="text-align: center; padding: 24px 0; border-top: 1px solid #E5E7EB;">
            <p style="margin: 0; color: #374151; font-weight: 500;">PsychSync Clinical Team</p>
            <p style="margin: 8px 0; color: #6B7280; font-size: 14px;">
                📞 24/7 Support Line: <strong>1-800-PSYCHSYNC</strong><br>
                📧 <a href="mailto:crisis@psychsync.ai" style="color: #2563EB;">crisis@psychsync.ai</a>
            </p>
        </div>
    </div>
</body>
</html>
            """,
            "text_body": f"""
🚨 IMMEDIATE SUPPORT NEEDED

Dear {user_name},

Your recent {screening_type} assessment (Score: {score}) indicates you may be experiencing significant distress.

You don't have to face this alone - help is available RIGHT NOW.

🚨 GET IMMEDIATE SUPPORT:

📞 988 Suicide & Crisis Lifeline
   Call or text 988 - Available 24/7
   Free, Confidential, Supportive

💬 Crisis Text Line
   Text HELLO to 741741
   Available 24/7

🏥 Emergency Services
   Call 911 if you are in immediate danger
   For life-threatening emergencies

🌐 Online Chat Support
   https://suicidepreventionlifeline.org/chat/
   Connect with a crisis counselor online

WHAT HAPPENS NEXT:
1. A licensed clinician will contact you within 2 hours
2. We'll help you create a safety plan
3. We'll connect you with appropriate services
4. We'll schedule follow-up support

💚 YOU MATTER
Crisis feelings are temporary. Your life has permanent value.
With support, things can and will get better.
We're here to help you through this.

PsychSync Clinical Team
24/7 Support: 1-800-PSYCHSYNC
crisis@psychsync.ai

This message is confidential and protected under HIPAA.
            """
        }

    @staticmethod
    def critical_alert_sms(user_name: str, screening_type: str) -> str:
        """
        SMS sent immediately for CRITICAL alerts (160 char limit optimized)

        Args:
            user_name: Patient's name
            screening_type: Type of screening

        Returns:
            SMS message text
        """
        # ✅ FIX: Proper username validation (prevent crash on empty string)
        first_name = user_name.split()[0] if user_name and ' ' in user_name else user_name or "Friend"
        return (
            f"🚨 {first_name}, immediate support available. "
            f"Your {screening_type} indicates you may need help right now. "
            f"Call 988 (Suicide & Crisis Lifeline) or text HELLO to 741741. "
            f"You're not alone - we're here 24/7."
        )

    # ========================================================================
    # LEVEL 2: HIGH RISK - URGENT SUPPORT
    # ========================================================================

    @staticmethod
    def high_risk_email(user_name: str, screening_type: str, score: int, severity: str) -> Dict[str, str]:
        """
        Email for HIGH risk - urgent but not immediate danger

        Args:
            user_name: Patient's name
            screening_type: Type of screening
            score: Assessment score
            severity: Severity level

        Returns:
            Dictionary with subject, html_body, and text_body
        """
        recommendations_list = """
            <ul>
                <li>Schedule an appointment with a mental health professional</li>
                <li>Consider talking to a trusted friend or family member</li>
                <li>Practice stress-reduction techniques (deep breathing, meditation)</li>
                <li>Maintain a regular sleep schedule and healthy routine</li>
                <li>Avoid alcohol and drugs, which can worsen symptoms</li>
            </ul>
        """

        return {
            "subject": "⚠️ Important: Mental Health Support & Resources Available",
            "html_body": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mental Health Support Available</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .warning-banner {{ background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 24px; text-align: center; border-radius: 12px; margin-bottom: 24px; }}
        .info-box {{ background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 20px; margin: 16px 0; border-radius: 8px; }}
        .button {{ display: inline-block; padding: 14px 28px; background: #2563EB; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 8px 4px; transition: background 0.3s; }}
        .button:hover {{ background: #1D4ED8; }}
        .resource-box {{ background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 16px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="warning-banner">
            <h1 style="margin: 0; font-size: 26px;">⚠️ Support & Resources Available</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.95;">You're Not Alone - Help is Here</p>
        </div>

        <p>Dear {user_name},</p>

        <p>Thank you for completing the <strong>{screening_type}</strong> assessment. Your results indicate you may be experiencing <strong style="color: #D97706;">{severity}</strong> symptoms that would benefit from professional support.</p>

        <div class="info-box">
            <h3 style="color: #D97706; margin-top: 0; font-size: 20px;">A Clinician Will Contact You Within 2 Hours</h3>
            <p style="margin: 8px 0; color: #92400E;">
                We take your well-being seriously. One of our licensed mental health professionals will reach out to discuss your results and available support options. You don't have to wait - help is available now.
            </p>
        </div>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">📞 24/7 Support Available Now:</h3>

        <div class="resource-box">
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0 0 8px 0; color: #DC2626;">988 Suicide & Crisis Lifeline</h4>
                <p style="margin: 0; font-size: 14px; color: #6B7280;">Call or text 988 anytime - Free & Confidential</p>
            </div>
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0 0 8px 0; color: #DC2626;">Crisis Text Line</h4>
                <p style="margin: 0; font-size: 14px; color: #6B7280;">Text "HELLO" to 741741 - Available 24/7</p>
            </div>
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0 0 8px 0; color: #2563EB;">SAMHSA Helpline</h4>
                <p style="margin: 0; font-size: 14px; color: #6B7280;">1-800-662-4357 - Treatment referrals & information</p>
            </div>
        </div>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">📋 Create Your Safety Plan:</h3>
        <p style="color: #4B5563;">Consider creating a safety plan with these steps:</p>
        <ol style="color: #4B5563; line-height: 1.8; padding-left: 20px;">
            <li>Identify warning signs when you're struggling</li>
            <li>List coping strategies that have helped before</li>
            <li>Write down contacts of supportive people</li>
            <li>Keep crisis hotline numbers easily accessible</li>
            <li>Make your environment safe (remove harmful items)</li>
            <li>Schedule activities that bring you comfort</li>
        </ol>

        <a href="https://www.psychsync.ai/safety-plan" class="button" style="display: inline-block; margin-top: 16px;">
            Create Your Safety Plan Now
        </a>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">🧘 Self-Care Resources:</h3>
        <div style="background: #EFF6FF; padding: 20px; border-radius: 8px;">
            <ul style="margin: 0; padding-left: 20px; color: #1E3A8A; line-height: 1.8;">
                <li><strong>Guided meditation apps:</strong> Calm, Headspace, Insight Timer</li>
                <li><strong>Deep breathing exercises:</strong> 4-7-8 technique (4 in, 7 hold, 8 out)</li>
                <li><strong>Connect with loved ones:</strong> Reach out to trusted friends/family</li>
                <li><strong>Maintain routine:</strong> Regular sleep, meals, and gentle exercise</li>
                <li><strong>Limit alcohol/caffeine:</strong> Can worsen anxiety and depression</li>
            </ul>
        </div>

        <div style="background: #DBEAFE; border-left: 4px solid #2563EB; padding: 20px; margin: 24px 0; border-radius: 8px;">
            <p style="margin: 0; color: #1E40AF; font-size: 16px;">
                <strong>💡 Remember:</strong> Seeking help is a sign of strength, not weakness.
                Many people experience mental health challenges, and effective treatments are available.
                You deserve to feel better.
            </p>
        </div>

        <p style="margin: 24px 0 16px 0; color: #374151;">We're here to support you every step of the way.</p>

        <p style="margin: 0;">Best regards,<br>
        <strong>The PsychSync Clinical Team</strong></p>

        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 32px 0;">

        <div style="font-size: 13px; color: #6B7280;">
            <p style="margin: 0 0 8px 0;">Questions? Contact us:</p>
            <p style="margin: 0;">
                📞 1-800-PSYCHSYNC | 📧 <a href="mailto:support@psychsync.ai" style="color: #2563EB;">support@psychsync.ai</a><br>
                Confidential & HIPAA-compliant
            </p>
        </div>
    </div>
</body>
</html>
            """,
            "text_body": f"""
Support & Resources Available

Dear {user_name},

Your {screening_type} assessment (Score: {score}) indicates {severity} symptoms.

A CLINICIAN WILL CONTACT YOU WITHIN 2 HOURS to discuss your results and support options.

24/7 SUPPORT AVAILABLE NOW:
• 988 Suicide & Crisis Lifeline - Call or text 988
• Crisis Text Line - Text HELLO to 741741
• SAMHSA Helpline - 1-800-662-4357

CREATE YOUR SAFETY PLAN:
Visit psychsync.ai/safety-plan to create your personalized safety plan

RECOMMENDED ACTIONS:
• Schedule appointment with mental health professional
• Talk to a trusted friend or family member
• Practice stress-reduction (deep breathing, meditation)
• Maintain regular sleep and healthy routine
• Avoid alcohol and drugs

REMEMBER:
Seeking help is a sign of STRENGTH, not weakness.
Effective treatments are available.
You deserve to feel better.

We're here to support you every step of the way.

Best regards,
The PsychSync Clinical Team

1-800-PSYCHSYNC | support@psychsync.ai
Confidential & HIPAA-compliant
            """
        }

    @staticmethod
    def high_risk_sms(user_name: str, screening_type: str) -> str:
        """SMS for HIGH risk"""
        # ✅ FIX: Proper username validation
        first_name = user_name.split()[0] if user_name and ' ' in user_name else user_name or "Friend"
        return (
            f"{first_name}, your assessment indicates you may benefit from support. "
            f"A clinician will call within 2 hours. "
            f"24/7 support: Call 988 or text HELLO to 741741. "
            f"You're not alone."
        )

    # ========================================================================
    # LEVEL 3: MODERATE RISK - STANDARD SUPPORT
    # ========================================================================

    @staticmethod
    def moderate_risk_email(
        user_name: str,
        screening_type: str,
        score: int,
        recommendations: list
    ) -> Dict[str, str]:
        """Email for MODERATE risk"""
        recs_html = "".join([f"<li>{rec}</li>" for rec in recommendations])

        return {
            "subject": f"Your {screening_type} Assessment Results - PsychSync",
            "html_body": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Assessment Results</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: white; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 24px; }}
        .info-box {{ background: #EFF6FF; border-left: 4px solid #2563EB; padding: 20px; margin: 16px 0; border-radius: 8px; }}
        .button {{ display: inline-block; padding: 14px 28px; background: #2563EB; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 8px 4px; transition: background 0.3s; }}
        .button:hover {{ background: #1D4ED8; }}
        .button-green {{ background: #059669; }}
        .button-green:hover {{ background: #047857; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); color: white; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">Your {screening_type} Results</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Thank You for Taking This Step</p>
        </div>

        <p>Dear {user_name},</p>

        <p>Thank you for completing your mental health assessment. Based on your responses, here are your personalized results and recommendations:</p>

        <div class="score-circle">
            <div style="text-align: center;">
                <div style="font-size: 42px; font-weight: bold;">{score}</div>
                <div style="font-size: 14px; opacity: 0.9;">Your Score</div>
            </div>
        </div>

        <div class="info-box">
            <h3 style="color: #1E40AF; margin-top: 0; font-size: 20px;">Recommended Next Steps:</h3>
            <ul style="color: #1E3A8A; line-height: 1.8;">{recs_html}</ul>
        </div>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">Resources Available to You:</h3>

        <div style="margin-bottom: 24px;">
            <h4 style="color: #2563EB; margin: 0 0 12px 0;">🧑‍⚕️ Professional Support:</h4>
            <ul style="color: #4B5563; line-height: 1.8; padding-left: 20px;">
                <li><strong>Schedule a consultation</strong> - Connect with our mental health professionals</li>
                <li><strong>Employee Assistance Program (EAP)</strong> - Free counseling sessions available</li>
                <li><strong>Therapist directory</strong> - Find licensed providers in your area</li>
                <li><strong>Insurance coverage</strong> - Many insurance plans cover mental health services</li>
            </ul>
            <a href="https://www.psychsync.ai/schedule" class="button" style="display: inline-block; margin-top: 12px;">
                Schedule Consultation
            </a>
        </div>

        <div style="margin-bottom: 24px;">
            <h4 style="color: #2563EB; margin: 0 0 12px 0;">📚 Self-Help Resources:</h4>
            <ul style="color: #4B5563; line-height: 1.8; padding-left: 20px;">
                <li>Evidence-based cognitive behavioral therapy (CBT) worksheets</li>
                <li>Mindfulness and meditation guides (Calm, Headspace, Insight Timer)</li>
                <li>Stress management techniques (progressive muscle relaxation)</li>
                <li>Sleep hygiene tips and resources</li>
                <li>Anxiety and depression workbooks</li>
            </ul>
            <a href="https://www.psychsync.ai/resources" class="button button-green" style="display: inline-block; margin-top: 12px;">
                Browse Resources
            </a>
        </div>

        <div style="margin-bottom: 24px;">
            <h4 style="color: #2563EB; margin: 0 0 12px 0;">🤝 Support Communities:</h4>
            <ul style="color: #4B5563; line-height: 1.8; padding-left: 20px;">
                <li>Online support groups (anonymous, moderated)</li>
                <li>Peer support networks</li>
                <li>Weekly wellness webinars</li>
                <li>Mindfulness group sessions</li>
            </ul>
        </div>

        <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0; font-size: 14px; color: #374151;">
                <strong>Important:</strong> This screening is not a diagnosis.
                Results should be reviewed with a licensed mental health professional for comprehensive assessment.
                Only a qualified healthcare provider can diagnose mental health conditions.
            </p>
        </div>

        <div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 20px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0; color: #92400E; font-size: 16px;">
                <strong>💚 Your Mental Health Matters</strong><br>
                Taking this assessment shows courage and self-awareness.
                Mental health is just as important as physical health,
                and seeking support when you need it is a sign of strength.
                We're here to support your well-being journey.
            </p>
        </div>

        <p style="margin: 24px 0 16px 0;">We're here to support you every step of the way.</p>

        <p style="margin: 0;">Best regards,<br>
        <strong>The PsychSync Team</strong></p>

        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 32px 0;">

        <div style="font-size: 13px; color: #6B7280;">
            <p style="margin: 0;">
                Questions? <a href="mailto:support@psychsync.ai" style="color: #2563EB;">support@psychsync.ai</a><br>
                Confidential & HIPAA-compliant | <a href="https://www.psychsync.ai" style="color: #2563EB;">www.psychsync.ai</a>
            </p>
        </div>
    </div>
</body>
</html>
            """,
            "text_body": f"""
Your {screening_type} Assessment Results

Dear {user_name},

Thank you for completing your mental health assessment.
Your Score: {score}

BASED ON YOUR RESULTS, THESE NEXT STEPS ARE RECOMMENDED:
{chr(10).join([f"• {rec}" for rec in recommendations])}

RESOURCES AVAILABLE:
• Professional Consultation - psychsync.ai/schedule
• Self-Help Resources - psychsync.ai/resources
• Support Groups - Connect with others
• 24/7 Crisis Support - Call 988 or text HELLO to 741741

IMPORTANT:
This screening is not a diagnosis.
Results should be reviewed with a licensed mental health professional.

Your mental health matters. We're here to support you.

Best regards,
The PsychSync Team

support@psychsync.ai
Confidential & HIPAA-compliant
            """
        }

    # ========================================================================
    # CLINICIAN NOTIFICATIONS
    # ========================================================================

    @staticmethod
    def clinician_alert_email(
        clinician_name: str,
        alert_details: Dict[str, any]
    ) -> Dict[str, str]:
        """
        Alert email sent to on-call clinician

        Args:
            clinician_name: Name of the clinician
            alert_details: Dictionary with alert information

        Returns:
            Dictionary with subject, html_body, and text_body
        """
        risk_flags_html = "".join([
            f'<span style="display: inline-block; padding: 4px 12px; background: #FEE2E2; color: #991B1B; border-radius: 12px; margin: 4px;">{flag.replace(/_/g, ' ')}</span>'
            for flag in alert_details.get('risk_flags', [])
        ])

        return {
            "subject": f"🚨 URGENT: Crisis Alert - Response Required",
            "html_body": f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crisis Alert - Response Required</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .critical {{ background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); border: 3px solid #DC2626; padding: 30px; border-radius: 12px; margin-bottom: 24px; }}
        .alert-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        .alert-table th {{ background: #F3F4F6; padding: 12px; text-align: left; font-weight: 600; }}
        .alert-table td {{ padding: 12px; border-bottom: 1px solid #E5E7EB; }}
        .button {{ display: inline-block; padding: 16px 32px; background: #DC2626; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 8px 4px; transition: background 0.3s; }}
        .button:hover {{ background: #B91C1C; }}
        .button-blue {{ background: #2563EB; }}
        .button-blue:hover {{ background: #1D4ED8; }}
        .button-green {{ background: #059669; }}
        .button-green:hover {{ background: #047857; }}
        .warning-box {{ background: #FEF2F2; border-left: 4px solid #DC2626; padding: 20px; margin: 20px 0; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="critical">
            <h1 style="color: #DC2626; margin-top: 0; font-size: 28px;">🚨 CRISIS ALERT - IMMEDIATE ACTION REQUIRED</h1>
            <p style="font-size: 18px; font-weight: 500; color: #991B1B; margin: 16px 0;">
                A patient has triggered a <strong>{alert_details.get('severity', 'HIGH').upper()}</strong> risk alert.
                Response required within <strong>{alert_details.get('response_time', '10 minutes')}</strong>.
            </p>
        </div>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">Alert Details:</h3>
        <table class="alert-table">
            <tbody>
                <tr>
                    <th style="width: 30%;">Alert ID:</th>
                    <td style="width: 70%;"><code style="background: #F3F4F6; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{alert_details.get('alert_id', 'N/A')}</code></td>
                </tr>
                <tr>
                    <th>Patient ID:</th>
                    <td><code style="background: #F3F4F6; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{alert_details.get('user_id', 'N/A')}</code></td>
                </tr>
                <tr>
                    <th>Screening Type:</th>
                    <td><strong>{alert_details.get('screening_type', 'N/A')}</strong></td>
                </tr>
                <tr>
                    <th>Score:</th>
                    <td style="font-size: 18px; font-weight: bold; color: #DC2626;">{alert_details.get('score', 'N/A')}</td>
                </tr>
                <tr>
                    <th>Risk Level:</th>
                    <td style="font-size: 18px; font-weight: bold; color: #DC2626;">{alert_details.get('risk_level', 'N/A').upper()}</td>
                </tr>
                <tr>
                    <th>Risk Flags:</th>
                    <td>{risk_flags_html}</td>
                </tr>
                <tr>
                    <th>Time:</th>
                    <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </tbody>
        </table>

        <h3 style="color: #1F2937; font-size: 20px; margin: 24px 0 12px 0;">🚨 IMMEDIATE ACTIONS REQUIRED:</h3>
        <ol style="color: #374151; line-height: 1.8; padding-left: 20px;">
            <li style="margin-bottom: 8px;"><strong>Acknowledge alert in dashboard</strong> (confirms receipt and assigns to you)</li>
            <li style="margin-bottom: 8px;"><strong>Review patient screening results</strong> in detail</li>
            <li style="margin-bottom: 8px;"><strong>Contact patient within required timeframe</strong> per protocol</li>
            <li style="margin-bottom: 8px;"><strong>Complete safety assessment</strong> using standardized protocol</li>
            <li style="margin-bottom: 8px;"><strong>Document all actions taken</strong> in clinical notes</li>
            <li><strong>Create follow-up plan</strong> if appropriate</li>
        </ol>

        <div style="margin: 32px 0;">
            <a href="https://dashboard.psychsync.ai/clinical/alerts/{alert_details.get('alert_id')}" class="button" style="display: inline-block;">
                Open Alert in Dashboard
            </a>
            <a href="tel:{alert_details.get('patient_phone', '')}" class="button button-blue" style="display: inline-block;">
                Call Patient
            </a>
        </div>

        <div class="warning-box">
            <p style="margin: 0; color: #991B1B; font-weight: 500;">
                ⚠️ <strong>REMINDER:</strong> Response time requirements and crisis protocols must be followed per
                organizational policy and HIPAA regulations. All interactions must be documented appropriately.
            </p>
        </div>

        <div style="background: #EFF6FF; padding: 20px; border-radius: 8px; margin: 24px 0;">
            <h4 style="margin: 0 0 12px 0; color: #1E40AF;">Need Support?</h4>
            <p style="margin: 0; color: #1E3A8A;">
                <strong>Clinical Director:</strong> Available 24/7 for consultation<br>
                📞 Emergency Line: <strong>1-800-PSYCH-HELP</strong><br>
                📧 <a href="mailto:oncall@psychsync.ai" style="color: #2563EB;">oncall@psychsync.ai</a>
            </p>
        </div>
    </div>
</body>
</html>
            """,
            "text_body": f"""
🚨 CRISIS ALERT - IMMEDIATE ACTION REQUIRED

Dr. {clinician_name},

A patient has triggered a {alert_details.get('severity', 'HIGH')} risk alert.
Response required within {alert_details.get('response_time', '10 minutes')}.

ALERT DETAILS:
Alert ID: {alert_details.get('alert_id')}
Patient ID: {alert_details.get('user_id')}
Screening: {alert_details.get('screening_type')}
Score: {alert_details.get('score', 'N/A')}
Risk Level: {alert_details.get('risk_level', 'N/A').upper()}
Risk Flags: {', '.join(alert_details.get('risk_flags', []))}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

IMMEDIATE ACTIONS (IN ORDER):
1. Acknowledge alert in clinical dashboard
2. Review patient screening results thoroughly
3. Contact patient within required timeframe
4. Complete safety assessment using protocol
5. Document all actions in clinical notes
6. Create follow-up plan if appropriate

DASHBOARD: dashboard.psychsync.ai/clinical/alerts/{alert_details.get('alert_id')}
CALL PATIENT: {alert_details.get('patient_phone', 'N/A')}

⚠️ CRITICAL: Response time requirements and crisis protocols must be followed.

Questions? Contact Clinical Director:
Emergency: 1-800-PSYCH-HELP
Email: oncall@psychsync.ai
            """
        }

    @staticmethod
    def clinician_alert_sms(alert_severity: str, alert_id: str) -> str:
        """
        SMS page to on-call clinician

        Args:
            alert_severity: Severity level
            alert_id: Alert ID

        Returns:
            SMS message text
        """
        return (
            f"🚨 {alert_severity.upper()} CRISIS ALERT - Patient needs immediate contact. "
            f"Alert ID: {alert_id[:8]}. "
            f"Check dashboard now. Response time protocol active. "
            f"dashboard.psychsync.ai"
        )


# ============================================================================
# NOTIFICATION SERVICE
# ============================================================================

class CrisisNotificationService:
    """
    Service for sending crisis notifications via multiple channels

    Features:
    - Multi-channel delivery (email, SMS, push)
    - Priority-based routing
    - Delivery confirmation
    - Audit logging
    - HIPAA-compliant
    """

    @staticmethod
    async def send_crisis_notification(
        user_email: str,
        user_phone: Optional[str],
        user_name: str,
        risk_level: str,
        screening_type: str,
        score: int,
        alert_details: Dict[str, any]
    ):
        """
        Send multi-channel crisis notification to patient

        Args:
            user_email: Patient's email address
            user_phone: Patient's phone number (optional)
            user_name: Patient's name
            risk_level: Risk level (critical, high, moderate, low)
            screening_type: Type of screening completed
            score: Assessment score
            alert_details: Additional alert details
        """
        templates = CrisisNotificationTemplates()

        # Determine notification level and send accordingly
        if risk_level == "critical":
            # CRITICAL - All channels, immediate delivery
            email_template = templates.critical_alert_email(user_name, screening_type, score)
            await CrisisNotificationService._send_email(
                to=user_email,
                subject=email_template["subject"],
                html_body=email_template["html_body"],
                text_body=email_template["text_body"],
                priority="urgent"
            )

            if user_phone:
                sms_text = templates.critical_alert_sms(user_name, screening_type)
                await CrisisNotificationService._send_sms(
                    to=user_phone,
                    message=sms_text,
                    priority="urgent"
                )

            # Push notification
            await CrisisNotificationService._send_push_notification(
                user_id=alert_details['user_id'],
                title="🚨 Immediate Support Available",
                body="Crisis resources available now. Tap for help.",
                priority="high",
                data={'type': 'crisis_alert', 'alert_id': alert_details['alert_id']}
            )

        elif risk_level == "high":
            # HIGH - Email + SMS, urgent priority
            email_template = templates.high_risk_email(
                user_name, screening_type, score, "moderate-severe"
            )
            await CrisisNotificationService._send_email(
                to=user_email,
                subject=email_template["subject"],
                html_body=email_template["html_body"],
                text_body=email_template["text_body"],
                priority="urgent"
            )

            if user_phone:
                sms_text = templates.high_risk_sms(user_name, screening_type)
                await CrisisNotificationService._send_sms(
                    to=user_phone,
                    message=sms_text,
                    priority="urgent"
                )

        else:  # MODERATE or LOW
            # STANDARD - Email only, normal priority
            recommendations = alert_details.get('recommendations', [
                "Consider speaking with a mental health professional",
                "Monitor your symptoms and seek help if they worsen",
                "Practice self-care and stress management"
            ])
            email_template = templates.moderate_risk_email(
                user_name, screening_type, score, recommendations
            )
            await CrisisNotificationService._send_email(
                to=user_email,
                subject=email_template["subject"],
                html_body=email_template["html_body"],
                text_body=email_template["text_body"],
                priority="normal"
            )

    @staticmethod
    async def notify_clinician(
        clinician_email: str,
        clinician_phone: str,
        clinician_name: str,
        alert_details: Dict[str, any]
    ):
        """
        Notify on-call clinician of crisis alert

        Args:
            clinician_email: Clinician's email address
            clinician_phone: Clinician's phone number
            clinician_name: Clinician's name
            alert_details: Alert information dictionary
        """
        templates = CrisisNotificationTemplates()

        # Email notification
        email_template = templates.clinician_alert_email(clinician_name, alert_details)
        await CrisisNotificationService._send_email(
            to=clinician_email,
            subject=email_template["subject"],
            html_body=email_template["html_body"],
            text_body=email_template["text_body"],
            priority="urgent"
        )

        # SMS page
        sms_text = templates.clinician_alert_sms(
            alert_details['severity'],
            alert_details['alert_id']
        )
        await CrisisNotificationService._send_sms(
            to=clinician_phone,
            message=sms_text,
            priority="urgent"
        )

        # Push notification to clinician app
        await CrisisNotificationService._send_push_notification(
            user_id=alert_details['clinician_id'],
            title=f"🚨 Crisis Alert - {alert_details['severity'].upper()}",
            body="Patient needs immediate contact. Tap to view alert.",
            priority="high",
            data={'type': 'clinician_alert', 'alert_id': alert_details['alert_id']}
        )

    # ========================================================================
    # PRIVATE METHODS - Implement with actual services
    # ========================================================================

    @staticmethod
    async def _send_email(to: str, subject: str, html_body: str, text_body: str, priority: str = "normal"):
        """
        Send email via SendGrid, AWS SES, or similar

        TODO: Implement with actual email service
        - SendGrid (recommended for HIPAA compliance)
        - AWS SES (alternative)
        - Mailgun (alternative)

        Required:
        - HIPAA BAA in place
        - Encryption in transit (TLS)
        - Encryption at rest
        - Audit logging
        - Delivery confirmation
        """
        import logging
        logger = logging.getLogger(__name__)

        # Placeholder implementation
        logger.info(f"Sending email to {to} with priority {priority}")
        logger.info(f"Subject: {subject}")

        # TODO: Implement actual email sending
        # Example with SendGrid:
        # import sendgrid
        # from sendgrid.helpers.mail import Mail, Email, To, Content
        #
        # message = Mail(
        #     from_email='noreply@psychsync.ai',
        #     to_emails=to,
        #     subject=subject,
        #     html_content=html_body,
        #     plain_text_content=text_body
        # )
        #
        # sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        # response = sg.send(message)
        #
        # if response.status_code != 200:
        #     raise Exception(f"Email failed: {response.body}")

        pass

    @staticmethod
    async def _send_sms(to: str, message: str, priority: str = "normal"):
        """
        Send SMS via Twilio, AWS SNS, or similar

        TODO: Implement with actual SMS service
        - Twilio (recommended for reliability)
        - AWS SNS (alternative)
        - MessageBird (alternative)

        Required:
        - HIPAA compliance
        - Delivery status tracking
        - Opt-out management
        - Audit logging
        """
        import logging
        logger = logging.getLogger(__name__)

        # Placeholder implementation
        logger.info(f"Sending SMS to {to} with priority {priority}")
        logger.info(f"Message: {message[:100]}...")

        # TODO: Implement actual SMS sending
        # Example with Twilio:
        # import os
        # from twilio.rest import Client
        #
        # client = Client(
        #     os.environ.get('TWILIO_ACCOUNT_SID'),
        #     os.environ.get('TWILIO_AUTH_TOKEN')
        # )
        #
        # message = client.messages.create(
        #     body=message,
        #     from_=os.environ.get('TWILIO_PHONE_NUMBER'),
        #     to=to
        # )
        #
        # if message.status not in ['queued', 'sent', 'delivered']:
        #     raise Exception(f"SMS failed: {message.error}")

        pass

    @staticmethod
    async def _send_push_notification(
        user_id: str,
        title: str,
        body: str,
        priority: str,
        data: Dict[str, any]
    ):
        """
        Send push notification via Firebase, OneSignal, or similar

        TODO: Implement with actual push service
        - Firebase Cloud Messaging (FCM)
        - OneSignal (cross-platform)
        - Amazon SNS (mobile push)

        Required:
        - User consent
        - Delivery confirmation
        - Badge handling
        - Sound/vibration options
        """
        import logging
        logger = logging.getLogger(__name__)

        # Placeholder implementation
        logger.info(f"Sending push notification to user {user_id}")
        logger.info(f"Title: {title}")
        logger.info(f"Priority: {priority}")

        # TODO: Implement actual push notification sending
        # Example with Firebase:
        # from firebase_admin import messaging
        #
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=title,
        #         body=body,
        #     ),
        #     data=data,
        #     token=user_device_token,
        #     android=messaging.AndroidConfig(
        #         priority='high' if priority == 'high' else 'normal',
        #         notification=messaging.AndroidNotification(
        #             channel_id='crisis_alerts'
        #         )
        #     ),
        #     apns=messaging.APNSConfig(
        #         payload=messaging.APNSPayload(
        #             aps=messaging.Aps(
        #                 alert=messaging.ApsAlert(
        #                     title=title,
        #                     body=body,
        #                 ),
        #                 sound='default',
        #                 badge=1
        #             )
        #         )
        #     )
        # )
        #
        # response = messaging.send(message)
        # logger.info(f"Push notification sent: {response}")

        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_phone_number(phone: str) -> str:
    """Format phone number for SMS delivery"""
    digits = ''.join(filter(str.isdigit, phone))
    if digits.startswith('1'):
        return f"+{digits}"
    return f"+1{digits}"


def validate_email_address(email: str) -> bool:
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
