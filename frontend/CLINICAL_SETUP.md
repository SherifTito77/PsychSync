# Clinical Assessment System Setup Guide

## 📋 Overview
The clinical assessment system provides HIPAA-compliant mental health screening tools for your PsychSync SaaS platform.

## 🚀 Quick Setup

### 1. Verify Installation
```bash
# Navigate to frontend directory
cd frontend

# Check if all files are created
ls src/pages/Clinical*
ls src/components/clinical/
ls src/routes/ClinicalRoutes.tsx
ls src/styles/clinical.css
```

### 2. Test the Clinical System
```bash
# Start development server
npm run dev

# Navigate to clinical assessments
# http://localhost:5173/clinical-assessments
```

## 🌐 Available Routes

### Main Assessment Pages
- `/clinical-assessments` - Mental health screening homepage
- `/clinical` - Alias for assessments page

### Assessment Flow
- `/clinical/consent` - Informed consent form
- `/clinical/assessment/phq9/take` - PHQ-9 depression screening
- `/clinical/assessment/gad7/take` - GAD-7 anxiety screening
- `/clinical/assessment/{tool}/complete` - Results and recommendations

### Emergency Resources
- `/clinical/emergency` - 24/7 crisis support

### Admin Dashboard
- `/clinical/dashboard` - Clinical staff management interface

## 🏥 Assessment Tools Available

### PHQ-9 (Depression)
- **9 questions** about depressive symptoms
- **Scoring**: 0-27 (Minimal to Severe)
- **Crisis detection**: Question 9 (suicidal thoughts)

### GAD-7 (Anxiety)
- **7 questions** about anxiety symptoms
- **Scoring**: 0-21 (Minimal to Severe)
- **Quick assessment**: 3-5 minutes

## 🔧 Backend Integration

### Required API Endpoints
```typescript
POST /api/v1/clinical/consent
POST /api/v1/clinical/screenings
POST /api/v1/clinical/alerts
GET /api/v1/clinical/alerts
POST /api/v1/clinical/emergency-access
```

### Database Models (Already Created)
- `ClinicalScreening` - Assessment data
- `ClinicalAlert` - Crisis notifications
- `ClinicalReferral` - Referral tracking
- `ClinicalAuditLog` - HIPAA compliance
- `ClinicalConsent` - Consent management

## 🎨 Customization

### Add New Assessment Tools
1. Update `ClinicalAssessment.tsx` with new questions
2. Add scoring logic to the assessment function
3. Create new route in `App.tsx`

### Modify Emergency Resources
1. Edit `ClinicalEmergency.tsx`
2. Update `EmergencyQuickActions.tsx`
3. Add crisis hotline numbers as needed

### Customize Styling
1. Edit `src/styles/clinical.css`
2. Modify component-specific styles
3. Ensure accessibility compliance

## 🔒 Security Features

### HIPAA Compliance
- ✅ Informed consent tracking
- ✅ Audit logging of all access
- ✅ Data encryption in transit
- ✅ Role-based access control

### Safety Measures
- ✅ Crisis detection algorithms
- ✅ Emergency resource integration
- ✅ Automatic alert escalation
- ✅ 24/7 support availability

## 📱 Mobile Features

### Responsive Design
- ✅ Mobile-first layout
- ✅ Touch-friendly interface
- ✅ Large, readable fonts
- ✅ Emergency quick-access buttons

### Offline Support
- ✅ PWA capabilities
- ✅ Offline crisis resources
- ✅ Local data persistence
- ✅ Background sync

## 🧪 Testing

### Run Tests
```bash
# Run clinical integration tests
npm test clinical-integration.test.tsx

# Run all tests
npm test

# Run with coverage
npm run test:coverage
```

### Manual Testing Checklist
- [ ] Assessment flow works end-to-end
- [ ] Consent forms are complete and clear
- [ ] Crisis detection triggers appropriately
- [ ] Emergency resources are accessible
- [ ] Mobile responsiveness works
- [ ] Accessibility features function
- [ ] API integration works correctly

## 📊 Analytics & Monitoring

### Key Metrics to Track
- Assessment completion rates
- Crisis alert frequency
- Emergency resource usage
- User satisfaction scores
- Clinical outcomes

### Dashboard Analytics
- Real-time alert monitoring
- Assessment trend analysis
- Referral tracking
- Compliance reporting

## 🔧 Troubleshooting

### Common Issues

#### Assessment Not Loading
```typescript
// Check authentication
const token = localStorage.getItem('access_token');
if (!token) {
  // Redirect to login
}
```

#### Crisis Alert Not Triggering
```typescript
// Check PHQ-9 question 9 response
const response9 = responses[9];
if (response9 && response9 !== 'Not at all') {
  setShowCrisisWarning(true);
}
```

#### API Connection Issues
```typescript
// Check API endpoints in network tab
// Verify authentication headers
// Check backend CORS settings
```

## 📞 Emergency Contacts

### Crisis Hotlines
- **988 Suicide & Crisis Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911
- **National Domestic Violence Hotline**: 1-800-799-7233

### Clinical Support
- **EAP (Employee Assistance)**: Check with your employer
- **Insurance Provider**: Contact for mental health coverage
- **Primary Care Physician**: Referral to mental health specialist

## 📚 Documentation

### Additional Resources
- [Clinical Documentation](./docs/clinical/)
- [HIPAA Compliance Guide](./docs/hipaa-compliance.md)
- [Emergency Procedures](./docs/emergency-procedures.md)
- [API Reference](./docs/clinical-api.md)

### Training Materials
- [Staff Training Guide](./docs/clinical-training.md)
- [User Manual](./docs/user-guide.md)
- [Safety Protocols](./docs/safety-protocols.md)

## 🔄 Updates & Maintenance

### Regular Maintenance Tasks
- Review emergency contact information
- Update consent forms as needed
- Monitor system performance
- Check for security updates
- Review user feedback

### Version Updates
- Update assessment tools based on clinical research
- Add new mental health resources
- Improve user interface based on feedback
- Ensure ongoing regulatory compliance

## 🚨 Emergency Protocol

### Immediate Response
1. **If user reports crisis**: Immediate alert creation
2. **Automatic notifications**: Email/SMS to clinical staff
3. **Emergency resource display**: Prominent, easy access
4. **Follow-up required**: System tracks until resolved

### Staff Response Procedures
1. **Acknowledge alert**: Within 1 hour
2. **Assess severity**: Use clinical protocols
3. **Contact user**: Appropriate follow-up method
4. **Document actions**: Complete audit trail
5. **Monitor until resolved**: Ensure safety

---

## 📞 Support

For technical issues or questions:
- Development Team: [Contact Info]
- Clinical Support: [Contact Info]
- Emergency: [24/7 Crisis Line]

This clinical assessment system is designed to provide safe, effective mental health screening while maintaining the highest standards of privacy and security.