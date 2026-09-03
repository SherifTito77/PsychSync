# Legal Review Preparation Checklist

**Purpose:** Prepare all necessary documentation for healthcare legal counsel review

**⚖️ CRITICAL:** Operating a clinical mental health platform requires thorough legal review to avoid liability and ensure compliance.

---

## 📋 Pre-Review Preparation

### **Step 1: Gather Core Documents**

**Business Documents:**
- [ ] Articles of Incorporation
- [ ] Operating Agreement
- [ ] Business licenses
- [ ] Tax ID (EIN)
- [ ] Privacy Policy (draft)
- [ ] Terms of Service (draft)
- [ ] BAA templates (from vendors)

**Clinical Documents:**
- [ ] Screening tool documentation (PHQ-9, GAD-7, C-SSRS)
- [ ] Scoring algorithms (evidence-based validation)
- [ ] Crisis intervention protocols
- [ ] Clinician training materials
- [ ] User consent forms
- [ ] Clinical disclaimer templates

**Technical Documents:**
- [ ] System architecture documentation
- [ ] Data flow diagrams (how PHI is stored/transmitted)
- [ ] Security documentation (encryption, access controls)
- [ ] HIPAA security policies
- [ ] Incident response procedures
- [ ] Business associate agreements (BAAs)

---

### **Step 2: Identify Legal Issues**

**Primary Legal Concerns:**

#### **1. Duty to Warn / Duty to Protect**
- **Issue:** When someone screens positive for suicide risk, what is our legal obligation?
- **Considerations:** Tarasoff duty, state laws vary
- **Questions for Counsel:**
  - Are we considered "mental health professionals" under state law?
  - What triggers duty to warn? (C-SSRS positive? PHQ-9 item 9?)
  - To whom do we owe a duty? (User, identified victims, both?)
  - What if we can't locate the user?

#### **2. Malpractice Liability**
- **Issue:** If someone dies by suicide after using our platform, are we liable?
- **Considerations:** Platform is screening, not diagnosis; crisis response team; proper disclaimers
- **Questions for Counsel:**
  - Does our screening constitute "mental health services"?
  - Are our disclaimers sufficient?
  - Should we require users to waive liability?
  - What liability insurance is needed?

#### **3. HIPAA Compliance**
- **Issue:** We're collecting and storing protected health information (PHI)
- **Considerations:** PHI encryption, access controls, audit trails, BAA with all vendors
- **Questions for Counsel:**
  - Are we a HIPAA covered entity or business associate?
  - Do we need to register with HHS?
  - What are our breach notification obligations?
  - Are our consent forms HIPAA-compliant?

#### **4. State Licensure**
- **Issue:** Are we practicing mental health across state lines?
- **Considerations:** Clinicians licensed in their state; users in all states
- **Questions for Counsel:**
  - Does our platform constitute "practicing" in each state?
  - Do clinicians need licenses in all states where users are located?
  - Are there telehealth regulations we must follow?

#### **5. Medical Device Regulation**
- **Issue:** Could our screening tools be considered "medical devices"?
- **Considerations:** FDA regulation of SaMD (Software as a Medical Device)
- **Questions for Counsel:**
  - Are PHQ-9, GAD-7, C-SSRS considered medical devices?
  - Do we need FDA clearance or registration?
  - What if we add "diagnostic" features later?

#### **6. Data Privacy (Beyond HIPAA)**
- **Issue:** State privacy laws (CCPA, etc.) and international laws (GDPR)
- **Considerations:** Users in California, EU, etc.
- **Questions for Counsel:**
  - Does CCPA apply to us?
  - What about GDPR for EU users?
  - Do we need GDPR data transfer agreements?

#### **7. Emergency Exception to Confidentiality**
- **Issue:** When can we break confidentiality to save a life?
- **Considerations:** Imminent harm vs. past ideation; contacting emergency services
- **Questions for Counsel:**
  - What constitutes "imminent harm"?
  - Can we contact family/friends?
  - Can we call 911 without user consent?
  - What documentation is required?

---

### **Step 3: Create Specific Legal Questions**

#### **For Healthcare Counsel:**

**Screening & Diagnosis:**
1. "Does providing PHQ-9, GAD-7, and C-SSRS screenings constitute practicing medicine or psychology?"
2. "What disclaimers must we include to clarify we are NOT diagnosing?"
3. "Are there any screenings we should AVOID due to higher liability?"
4. "What's the difference between 'screening' and 'assessment' legally?"

**Crisis Response:**
5. "When a user screens positive for suicide risk, what is our legal duty?"
6. "If we can't reach the user, what are our obligations?"
7. "Can we contact emergency services (911) without user consent?"
8. "What if we have incomplete location information?"
9. "What documentation is required when we break confidentiality?"

**Clinician Liability:**
10. "Are our crisis clinicians personally liable for interventions?"
11. "What malpractice insurance limits are recommended?"
12. "Does our protocol protect clinicians from liability?"
13. "What if a clinician misses an alert (doesn't respond in time)?"

**User Data:**
14. "Who owns the screening data - the user or PsychSync?"
15. "Can we use de-identified data for research/improvement?"
16. "What are our obligations if law enforcement requests user data?"
17. "How long must we retain clinical records?"
18. "What if a user demands their data be deleted?"

**Regulatory:**
19. "Are we a HIPAA covered entity or business associate?"
20. "Do we need to register with state medical boards?"
21. "Are there any state-by-state requirements we should know about?"
22. "Could our screening tools be considered 'medical devices' by the FDA?"

---

### **Step 4: Prepare Visual Aids**

**Data Flow Diagram:**
Create a simple diagram showing:
1. User takes screening
2. Responses stored in database (encrypted)
3. Score calculated
4. If crisis alert → Clinician notified
5. Clinician contacts user
6. If no response → Escalate to emergency contact
7. If imminent danger → Call 911

**System Architecture:**
Show:
- Database encryption at rest
- TLS encryption in transit
- Access controls (who can see what)
- Audit logging (all PHI access logged)

**Crisis Protocol Flowchart:**
1. Screening submitted
2. Score calculated
3. Risk level determined
4. IF critical → Page clinician immediately
5. Clinician assesses within 5 minutes
6. Safety plan created OR emergency services contacted
7. Documentation completed

---

### **Step 5: Draft Key Policies**

**Privacy Policy (Draft Outline):**
```markdown
# Privacy Policy

## Information We Collect
- Clinical screening responses (PHI)
- Contact information
- Demographic information
- Usage data

## How We Use Your Information
- To provide screening results
- To connect you with resources
- For crisis intervention (if needed)
- To improve our platform (de-identified only)

## How We Protect Your Information
- HIPAA-compliant encryption
- Access controls
- Audit trails
- Secure data centers

## When We Share Your Information
- With crisis clinicians (if you're at risk)
- With emergency services (if imminent danger)
- With your consent (otherwise we don't share)

## Your Rights
- Access your records
- Correct errors
- Request deletion (with clinical hold)
- Opt-out of non-essential data use

## Contact Us
privacy@psychsync.ai
```

**Terms of Service (Draft Outline):**
```markdown
# Terms of Service

## Important Disclaimer
"PsychSync is a screening tool, NOT a diagnostic tool.
It does NOT replace professional mental health evaluation.

If you are in crisis, call 988 or 911 immediately."

## Your Responsibilities
- Answer questions honestly
- Contact a professional if screening indicates risk
- Don't rely on PsychSync for emergency care

## Our Responsibilities
- Provide evidence-based screenings
- Protect your health information
- Connect you with crisis resources if needed
- Maintain HIPAA compliance

## Limitation of Liability
"We are not liable for any harm resulting from:
- Your failure to seek professional care
- Your misuse of the platform
- Technical failures beyond our control

## Waiver
"By using PsychSync, you acknowledge that:
- This is NOT emergency care
- We are NOT your mental health provider
- You should seek professional evaluation if needed"
```

**Informed Consent Form (Draft):**
```markdown
# Informed Consent for Clinical Screening

## What You're Agreeing To

I understand that:
1. I will complete evidence-based mental health screenings
2. My responses are confidential and protected by HIPAA
3. My data will be stored securely
4. If I'm at risk, a crisis clinician will contact me
5. I may be connected with mental health resources
6. This screening is NOT a diagnosis

## Crisis Intervention
I understand that:
- If I indicate I'm at risk of harming myself, a clinician will contact me
- If I'm in immediate danger, emergency services may be contacted
- This is for my safety

## Data Use
I consent to:
- My data being used to provide screening results
- My data being used for crisis intervention if needed
- My data being used to improve the platform (de-identified)

## Voluntary Participation
I understand that:
- My participation is voluntary
- I can withdraw at any time
- Withdrawing does not delete prior records (clinical requirement)

## Signature
[ ] I have read and understand this consent
[ ] I am 18 years or older
[ ] I agree to the terms above

Date: _____________
Signature: _____________
```

---

### **Step 6: Prepare for Initial Consultation**

**Before Meeting Counsel:**
1. Organize all documents in a shared folder
2. Create executive summary (2 pages max)
3. Prepare list of specific questions (categorized)
4. Include diagrams/charts for clarity
5. Be prepared to explain technical architecture

**During Meeting:**
1. Take detailed notes
2. Record meeting (if permitted)
3. Ask follow-up questions
4. Establish timeline for legal review
5. Discuss fee structure

**After Meeting:**
1. Send follow-up email with summary
2. Confirm next steps
3. Implement recommendations promptly
4. Schedule follow-up consultation

---

## ⚖️ Selecting Healthcare Counsel

**Qualifications to Look For:**
✅ Experience with mental health law
✅ Experience with digital health/telehealth
✅ HIPAA expertise
✅ Understanding of technology
✅ Familiarity with startup liability

**Questions to Ask Potential Counsel:**
1. "How many mental health startups have you worked with?"
2. "Are you familiar with crisis intervention liability?"
3. "Do you understand HIPAA requirements for SaaS platforms?"
4. "What's your experience with FDA SaMD regulation?"
5. "Can you help us with state licensure questions?"

**Red Flags:**
❌ No experience with mental health law
❌ Unfamiliar with HIPAA
❌ Doesn't understand technology
❌ Says "this is fine" without thorough review
❌ Cannot provide examples of similar work

---

## 💰 Legal Fees Budget

**Initial Setup:**
- Document review: $5,000-10,000
- Initial consultation: $1,000-2,500
- Policy drafting: $10,000-20,000
- **Total: $15,000-30,000**

**Ongoing:**
- Monthly retainer: $2,000-5,000/month
- Ad hoc counsel: $400-800/hour
- Annual compliance review: $5,000-10,000

**Budget for First Year:**
- Initial setup: $25,000
- Monthly retainer: $3,000 × 12 = $36,000
- Annual review: $7,500
- **Total First Year: ~$68,500**

---

## ✅ Pre-Legal Review Checklist

### **Documents Prepared:**
- [ ] Business documents gathered
- [ ] Clinical documentation organized
- [ ] Technical documentation complete
- [ ] Data flow diagram created
- [ ] Crisis protocol flowchart created
- [ ] Privacy Policy drafted
- [ ] Terms of Service drafted
- [ ] Informed Consent drafted
- [ ] Executive summary written
- [ ] List of questions compiled

### **Counsel Selected:**
- [ ] Healthcare attorney retained
- [ ] Fee structure agreed upon
- [ ] Initial consultation scheduled
- [ ] Document access provided
- [ ] Timeline established

---

## 🎯 Post-Review Action Items

### **Immediate (Week 1):**
- [ ] Implement all required policy changes
- [ ] Update disclaimers based on feedback
- [ ] Modify crisis protocols as recommended
- [ ] Adjust data handling practices

### **Short-Term (Month 1):**
- [ ] Complete additional state registrations
- [ ] Obtain necessary licenses
- [ ] Purchase recommended insurance
- [ ] Train staff on legal requirements

### **Long-Term (Ongoing):**
- [ ] Annual legal review
- [ ] Policy updates as laws change
- [ ] Maintain document everything
- [ ] Continuously monitor regulatory changes

---

**Remember:** Legal review is not optional. It's essential for protecting users, your team, and your business. Budget accordingly and prioritize it.

**Questions?** Contact: legal@psychsync.ai
