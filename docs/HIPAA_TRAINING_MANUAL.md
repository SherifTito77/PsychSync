# HIPAA Training Manual

**Purpose:** Comprehensive HIPAA training for all PsychSync staff

**⚠️ MANDATORY:** All staff must complete HIPAA training BEFORE accessing any user health information

---

## 📚 Training Overview

### **Who Must Complete This Training?**
✅ All employees
✅ All contractors
✅ All crisis clinicians
✅ All IT staff with system access
✅ All executives and management

### **When Must Training Be Completed?**
- **New Hires:** Within first week of employment
- **Annual Refresher:** Every 12 months
- **Policy Changes:** Within 30 days of policy update

### **Training Format:**
- ⏱️ **Duration:** 2 hours (initial), 1 hour (annual refresher)
- 📝 **Format:** Interactive modules + quiz
- ✅ **Passing Score:** 80% or higher
- 📜 **Certificate:** Issued upon completion

---

## 🎯 Module 1: HIPAA Basics (15 minutes)

### **What is HIPAA?**

**Health Insurance Portability and Accountability Act of 1996**

**Two Main Rules:**
1. **Privacy Rule** - Protects PHI
2. **Security Rule** - Protects ePHI (electronic PHI)

---

### **What is PHI?**

**Protected Health Information (PHI)** = Any health information that can be linked to a specific person

**Examples:**
- Screening responses (PHQ-9, GAD-7, C-SSRS)
- Mental health diagnoses
- Treatment information
- Contact information (when combined with health data)
- Dates of service/birth
- Any unique identifiers (email, user ID, IP address)

**18 Identifiers:**
1. Names
2. Geographic subdivisions (smaller than state)
3. All elements of dates (except year) for dates directly related to an individual
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers
14. Web Universal Resource Locators (URLs)
15. Internet Protocol (IP) address numbers
16. Biometric identifiers (fingerprints, voiceprints)
17. Full face photographic images
18. Any other unique identifying number, characteristic, or code

---

### **What is ePHI?**

**Electronic Protected Health Information** = PHI in electronic form

**At PsychSync, ePHI includes:**
- Database records of screenings
- User profile information
- Clinical notes
- Alert logs
- Audit trails
- Email communications (if containing PHI)

---

### **Who Must Comply with HIPAA?**

**Covered Entities:**
- Healthcare providers
- Health plans
- Healthcare clearinghouses

**Business Associates:**
- Vendors who handle PHI on behalf of covered entities
- **PsychSync is a Business Associate** (we handle PHI for healthcare providers)

---

## 🎯 Module 2: Privacy Rule (30 minutes)

### **Permitted Uses & Disclosures**

**You CAN use/disclose PHI WITHOUT authorization:**

1. **For Treatment** ✅
   - Example: Crisis clinician reviewing screening to provide intervention

2. **For Payment** ✅
   - Example: Billing insurance (not applicable to PsychSync currently)

3. **For Healthcare Operations** ✅
   - Example: Quality improvement, training, fraud detection

4. **Required by Law** ✅
   - Example: Court order, subpoena

5. **Public Health Activities** ✅
   - Example: Reporting contagious diseases (not applicable)

6. **Victims of Abuse/Neglect** ✅
   - Example: Reporting suspected elder abuse

7. **Health Oversight Activities** ✅
   - Example: Government audits

8. **Coroners/Medical Examiners** ✅
   - Example: Deceased user information

9. **Research** ✅
   - Example: De-identified data only

10. **To Avert a Serious Threat to Health or Safety** ✅
    - **CRITICAL FOR CRISIS INTERVENTION**
    - Example: Contacting 911 for imminent suicide risk

---

### **Uses/Disclosures REQUIRING Authorization**

**You MUST obtain written authorization for:**

❌ Marketing (except for refill reminders, appointment reminders)
❌ Sale of PHI
❌ Psychotherapy notes (special protection)
❌ Most research using identifiable data
❌ Employment purposes
❌ Insurance eligibility (outside of healthcare)

---

### **Minimum Necessary Standard**

**Rule:** When using/disclosing PHI, use only the **minimum necessary** to accomplish the purpose.

**Examples:**

❌ **WRONG:** Sending entire clinical record to billing department
✅ **RIGHT:** Sending only diagnosis codes to billing department

❌ **WRONG:** Sharing full screening with all staff
✅ **RIGHT:** Only crisis clinicians see screening results

**For Crisis Intervention:**
- Clinicians get ALL screening information (needed for intervention)
- IT staff get NO clinical information (only technical data)
- Support staff get NO PHI

---

### **Patient Rights Under HIPAA**

**1. Right to Access**
- Users can request copies of their records
- Must provide within 30 days
- Can charge reasonable cost-based fee

**2. Right to Amend**
- Users can request corrections to their records
- We can deny if record is accurate

**3. Right to Accounting of Disclosures**
- Users can request list of who we shared their PHI with
- Last 6 years of disclosures

**4. Right to Request Restrictions**
- Users can ask us to limit how we use/disclose their PHI
- We don't have to agree (except for psychotherapy notes)

**5. Right to Request Confidential Communications**
- Users can ask us to communicate in a specific way (e.g., personal email instead of work)

**6. Right to a Paper Copy of Privacy Notice**
- Must provide on first service delivery
- Must post on website

**7. Right to File a Complaint**
- Users can complain to us or to HHS
- Cannot retaliate against users who complain

---

## 🎯 Module 3: Security Rule (30 minutes)

### **Three Types of Security Safeguards**

#### **1. Administrative Safeguards** (Policies & Procedures)

**Required:**
✅ **Security Management Process** - Identify and analyze security risks
✅ **Assigned Security Official** - One person responsible for security
✅ **Workforce Training** - All staff must be trained (that's this training!)
✅ **Information Access Management** - Who can access what
✅ **Contingency Planning** - Backup, disaster recovery, emergency mode
✅ **Evaluation** - Periodic security assessments

**At PsychSync:**
- Security Officer: CTO or designated InfoSec
- Access Control: Role-based access (RBAC)
- Backups: Daily encrypted backups
- Disaster Recovery: Can restore operations within 24 hours

---

#### **2. Physical Safeguards** (Physical Protection)

**Required:**
✅ **Facility Access Controls** - Limit physical access to PHI
✅ **Workstation Use** - Rules for computer use
✅ **Workstation Security** - Lock screens when away
✅ **Device and Media Controls** - Encrypt laptops, track PHI disposal

**At PsychSync:**
- Office: Badge access required
- Computers: Auto-lock after 5 minutes
- Laptops: Full disk encryption (FileVault/BitLocker)
- Mobile: No PHI on personal phones
- Disposal: Shred hard copies; wipe electronic media

---

#### **3. Technical Safeguards** (Technical Protection)

**Required:**

**A. Access Control** ✅
- Unique user IDs for everyone
- Emergency access procedure (break glass in case of emergency)
- Automatic logoff (timeout)
- Encryption and decryption

**At PsychSync:**
- Each user has unique login
- MFA required for remote access
- Auto-logout after 15 minutes inactive
- All PHI encrypted at rest and in transit

**B. Audit Controls** ✅
- Hardware, software, and procedural mechanisms that record and examine activity
- MUST track: Who accessed what, when, and why

**At PsychSync:**
- Comprehensive audit logging
- Log all PHI access
- Review logs weekly
- Alert on suspicious activity

**C. Integrity** ✅
- Protect PHI from improper alteration or destruction
- Must detect integrity violations

**At PsychSync:**
- Database integrity checks
- Backup verification
- Change logs for clinical data
- Read-only access for most users

**D. Transmission Security** ✅
- Protect PHI during transmission
- Guard against unauthorized access

**At PsychSync:**
- TLS 1.3 for all web traffic
- Encrypted database connections
- Secure email (TLS or encryption)
- VPN for remote access

---

### **Encryption Requirements**

**Encryption is NOT specifically required by HIPAA Security Rule, BUT:**
- If you DON'T encrypt, you must document why it's not appropriate
- **Reality:** Encryption is Addressable Implementation Spec → You basically MUST encrypt

**At PsychSync, we encrypt:**
✅ Data at rest (databases, backups)
✅ Data in transit (web, email, API)
✅ Data on mobile devices
✅ Data on portable media (USB drives)

**Encryption Standards:**
- AES-256 for data at rest
- TLS 1.3 for data in transit
- PGP/GPG for email (if needed)

---

## 🎯 Module 4: Crisis Intervention & HIPAA (20 minutes)

### **The Emergency Exception**

**HIPAA allows disclosure to prevent or lessen a serious and imminent threat to health or safety.**

**At PsychSync, this applies when:**
- User screens positive for suicide risk
- User indicates intent to harm self or others
- User is in immediate danger

**What You CAN Do:**
✅ Contact emergency services (911)
✅ Contact user's emergency contact
✅ Contact family/friends if appropriate
✅ Disclose limited PHI to facilitate intervention
✅ Use professional judgment

**What You MUST Do:**
⚠️ Document the disclosure in audit log
⚠️ Only disclose minimum necessary information
⚠️ Believe in good faith that disclosure is necessary
⚠️ Only disclose to people who can help

---

### **Scenario: User Screens Positive for Suicide Risk**

**Step 1:** Automated system detects crisis
**Step 2:** Clinician receives alert with PHI
**Step 3:** Clinician calls user
**Step 4:** If user doesn't answer, call emergency contact
**Step 5:** If imminent danger, call 911
**Step 6:** Document everything

**HIPAA Compliance:**
✅ Access to PHI is permitted (for treatment)
✅ Disclosure to emergency services is permitted (emergency exception)
✅ Documentation in audit log (required)
✅ Minimum necessary (only disclose risk level, location)

---

### **What NOT to Do**

❌ **Don't ignore the crisis** - Duty to warn may apply
❌ **Don't disclose more than necessary** - Just risk level and location
❌ **Don't post on social media** - EVER
❌ **Don't discuss with colleagues** - Only those who need to know
❌ **Don't access records unnecessarily** - Only for active cases

---

## 🎯 Module 5: Breach Notification (15 minutes)

### **What is a Breach?**

**Breach = Unauthorized acquisition, access, use, or disclosure of PHI**

**Examples:**
- Laptop with unencrypted PHI stolen
- PHI emailed to wrong person
- Database hacked
- Paper records left in public area
- Employee snoops in records they shouldn't access

---

### **Breach Notification Requirements**

**If breach affects 500+ individuals:**
- Notify HHS **without unreasonable delay** (and within 60 days)
- Notify prominent media outlets in affected area
- Notify individuals **without unreasonable delay** (and within 60 days)

**If breach affects < 500 individuals:**
- Notify individuals **without unreasonable delay** (and within 60 days)
- Notify HHS annually (all small breaches combined)

**What Must Notification Include?**
- Description of breach
- Types of PHI exposed
- Steps individuals should take to protect themselves
- What we're doing to investigate/mitigate
- Contact information for questions

---

### **What to Do If You Discover a Breach**

**IMMEDIATELY:**
1. **Stop the breach** (if possible)
2. **Report to Security Officer** (security@psychsync.ai)
3. **Preserve evidence** (don't delete anything)
4. **Don't discuss it** (except with authorized personnel)

**Then:**
1. Security Officer investigates
2. Determine if notification is required
3. If so, notify within required timeframes
4. Document everything

---

## 🎯 Module 6: Real-World Scenarios (20 minutes)

### **Scenario 1: Clinician Access**

**Situation:** A crisis clinician is at home and needs to access a user's screening to provide intervention.

**Is this HIPAA compliant?**
✅ **YES** - This is permitted for treatment purposes

**Requirements:**
- Clinician has legitimate need to access
- Using secure connection (VPN)
- Access is logged (audit trail)
- Only minimum necessary information accessed

---

### **Scenario 2: IT Support**

**Situation:** An IT staff member needs to troubleshoot a database issue and views user records.

**Is this HIPAA compliant?**
❌ **NO** - Unless IT access is de-identified or role-based access allows it

**Correct approach:**
- IT staff should NEVER view PHI unless absolutely necessary
- Use de-identified data for testing/troubleshooting
- If PHI must be accessed, document reason and get approval

---

### **Scenario 3: Family Contact**

**Situation:** A user's mother calls and says "My son is using your platform and I'm worried about him. Can you tell me if he's okay?"

**Is this HIPAA compliant?**
❌ **NO** - Cannot disclose PHI to family without user's permission

**Correct response:**
- "I understand your concern, but we cannot disclose any information about users without their permission. If you're worried about his safety, please contact emergency services or go check on him."

**Exception:**
- If user has signed authorization allowing disclosure to family
- If emergency exception applies (imminent danger)

---

### **Scenario 4: Law Enforcement Request**

**Situation:** Police show up with a subpoena demanding user records.

**Is this HIPAA compliant?**
✅ **MAYBE** - Can disclose if required by law

**Correct approach:**
- Verify the subpoena is valid
- Contact legal counsel before responding
- Only provide what's specifically requested
- Document the disclosure
- Notify user (if allowed)

---

### **Scenario 5: Social Media**

**Situation:** An employee sees a funny screening response and shares it on Twitter (anonymized).

**Is this HIPAA compliant?**
❌ **NO** - Even anonymized, this violates HIPAA

**Why it's wrong:**
- Derogatory sharing of PHI
- Could potentially be re-identified
- Violates privacy and trust

**Penalty:**
- Immediate termination
- Potential civil/criminal penalties
- HIPAA violation fines

---

### **Scenario 6: Forgot Password**

**Situation:** A user emails saying "I forgot my password, can you reset it?"

**Is this HIPAA compliant?**
⚠️ **MAYBE** - Depends on verification process

**Correct approach:**
- Verify identity before resetting
- Don't disclose PHI in email
- Send reset link to verified email
- Log the action

---

## 🎯 Module 7: Best Practices (10 minutes)

### **DO ✅**

✅ **DO** Treat all PHI as confidential
✅ **DO** Use strong, unique passwords
✅ **DO** Lock your computer when away
✅ **DO** Report suspicious activity immediately
✅ **DO** Access only the records you need
✅ **DO** Use secure communication methods
✅ **DO** Complete mandatory training annually
✅ **DO** Follow the minimum necessary standard
✅ **DO** Document everything
✅ **DO** Ask if you're unsure

---

### **DON'T ❌**

❌ **DON'T** Share passwords
❌ **DON'T** Access records out of curiosity
❌ **DON'T** Discuss PHI in public areas
❌ **DON'T** Email PHI unencrypted
❌ **DON'T** Store PHI on personal devices
❌ **DON'T** Leave PHI visible on screens
❌ **DON'T** Throw PHI in regular trash (shred it)
❌ **DON'T** Share PHI on social media (EVER)
❌ **DON'T** Ignore security warnings
❌ **DON'T** Assume you know what you're doing (ask!)

---

## 📝 Final Quiz

### **Question 1:**
**What is the minimum necessary standard?**
A) You must access all records to be thorough
B) You should access only the PHI needed to do your job
C) You can access any records you want as long as you're careful
D) Only doctors need to follow minimum necessary

**Answer:** B

---

### **Question 2:**
**A user screens positive for suicide risk. Can you call 911?**
A) No, that violates privacy
B) Only if the user gives permission
C) Yes, under the emergency exception
D) Only if you get a court order

**Answer:** C

---

### **Question 3:**
**How long must you retain audit logs?**
A) 1 year
B) 3 years
C) 6 years
D) Forever

**Answer:** C (6 years from creation)

---

### **Question 4:**
**A user's mother calls asking about their screening. Can you tell her?**
A) Yes, she's family
B) Only if she sounds really worried
C) No, never without user's permission
D) Only if she offers to pay

**Answer:** C

---

### **Question 5:**
**What is ePHI?**
A) Electronic Protected Health Information
B) Emergency Private Health Information
C) Encrypted Personal Health Information
D) External Public Health Information

**Answer:** A

---

### **Question 6:**
**You find a laptop with PHI in a coffee shop. What do you do?**
A) Take it home and keep it safe
B) Report to security officer immediately
C) Try to find the owner yourself
D) Wipe it and sell it

**Answer:** B

---

### **Question 7:**
**How often must you complete HIPAA training?**
A) Once when hired
B) Every 6 months
C) Annually
D) Only if there's a breach

**Answer:** C

---

### **Question 8:**
**Can you discuss PHI in an elevator?**
A) Yes, as long as you whisper
B) No, never
C) Only if the elevator is empty
D) Only with colleagues

**Answer:** B

---

### **Question 9:**
**What is the penalty for knowingly violating HIPAA?**
A) Nothing, it's just a guideline
B) Slap on the wrist
C) Civil and criminal penalties, fines up to $1.5M, prison time
D) Just have to take training again

**Answer:** C

---

### **Question 10:**
**Who is responsible for HIPAA compliance at PsychSync?**
A) Just the compliance officer
B) Just the clinicians
C) Just management
D) EVERYONE

**Answer:** D

---

## ✅ Training Completion

**Congratulations!** You've completed the HIPAA training.

**Next Steps:**
1. Sign the HIPAA Acknowledgment Form
2. Return to HR/Manager
3. Receive completion certificate
4. Start protecting PHI!

**Remember:** HIPAA compliance is everyone's responsibility. If you see something, say something.

**Questions?** Contact: compliance@psychsync.ai

---

## 📜 HIPAA Acknowledgment Form

```markdown
I, _____________________, acknowledge that I have completed HIPAA training
and understand:

1. What PHI and ePHI are
2. My obligations under HIPAA Privacy & Security Rules
3. The penalties for non-compliance (up to $1.5M in fines + prison)
4. My responsibility to protect all user health information
5. How to report breaches or suspicious activity

I agree to:
- Follow all HIPAA policies and procedures
- Protect PHI from unauthorized disclosure
- Complete annual HIPAA refresher training
- Report any potential violations immediately

Signature: _____________________
Date: _____________________

Employee ID: _____________________

For HR Use:
Training Completed: ______
Certificate Issued: ______
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-14
**Next Review:** 2027-01-14
**Training Coordinator:** compliance@psychsync.ai
