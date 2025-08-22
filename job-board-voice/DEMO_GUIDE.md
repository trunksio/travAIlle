# Demo Guide - Job Board with AI Assistant

## Quick Demo Setup

### 1. Access the Demo Helper
Navigate to: http://localhost:5011/demo.html

This page provides:
- Two pre-crafted sample CVs (English & German)
- One-click copy functionality
- Highlighted areas that need clarification
- Direct links to appropriate job applications

### 2. Sample CVs Overview

#### English CV - Sarah Thompson
- **Current Role**: Senior Business Analyst in Digital Services
- **Experience**: 7 years in digital transformation
- **Target**: Senior Project Manager or Product Owner roles
- **Demo Points**:
  - Shows progression from analyst to leadership
  - Has some technical skills but levels unclear
  - Project management experience but no formal certification
  - AI will ask about specific systems and team sizes

#### German CV - Maximilian Weber
- **Current Role**: Teamleiter Kundenservice (Customer Service Team Lead)
- **Experience**: 8 years with strong leadership focus
- **Target**: HR Development or IT Management roles
- **Demo Points**:
  - Career pivot from customer service to HR/IT
  - Strong soft skills, developing technical skills
  - Six Sigma Green Belt in progress
  - AI will explore IT readiness and HR relevance

## Demo Flow (5-minute version)

### Step 1: Language Selection (30 seconds)
1. Start at http://localhost:5011
2. Show language toggle (🇬🇧 EN / 🇩🇪 DE)
3. Switch to German to show instant translation
4. Note how job titles and descriptions change

### Step 2: Browse Jobs (30 seconds)
1. Point out the 6 available positions
2. Highlight German-specific roles (Berlin/Munich)
3. Select "Senior Project Manager" for English demo

### Step 3: Start Application (1 minute)
1. Click "Apply Now" on chosen position
2. Show the three-column layout:
   - Contact Information (manual)
   - AI-Assisted Fields (auto-filled)
   - Full-width Chat Interface below

### Step 4: AI Interaction (2.5 minutes)
1. Go to demo.html and copy Sarah's CV
2. Paste into chat interface
3. **AI will**:
   - Greet and acknowledge the CV
   - Ask clarifying questions about:
     - Specific systems implemented
     - Team sizes managed
     - Project management certification plans
   - Suggest how skills map to the role

4. **Answer examples**:
   - "I led teams of 4-6 people typically"
   - "We implemented Salesforce and SAP"
   - "Planning to get PMP certification this year"

5. **Watch as**:
   - Form fields auto-populate
   - Progress bar updates
   - Fields show "✓ AI Generated" status

### Step 5: Review & Submit (1 minute)
1. Show completed form fields
2. Highlight professional language used
3. Point out how AI addressed the role requirements
4. Click "Submit Application" to complete

## Key Demo Talking Points

### Multilingual Support
- "Full bilingual support - entire experience in English or German"
- "AI responds naturally in selected language"
- "Professional business language appropriate for internal applications"

### AI Intelligence
- "AI understands context from CV"
- "Asks intelligent follow-up questions"
- "Helps articulate strengths appropriately"
- "Reduces anxiety about internal applications"

### Efficiency Gains
- "Reduces application time from 30-45 minutes to 5-10 minutes"
- "Ensures consistent quality in applications"
- "Helps employees who struggle with self-promotion"

### Areas of Clarification
The sample CVs intentionally include ambiguous areas to demonstrate:
- AI's ability to identify gaps
- Interactive clarification process
- Contextual understanding
- Professional judgment in asking questions

## Quick Troubleshooting

### If AI doesn't respond:
- Check that ANTHROPIC_API_KEY is set in .env
- Verify backend is running: `docker compose ps`
- Check logs: `docker compose logs backend`

### If language doesn't switch:
- Clear browser cache
- Refresh the page after switching
- Check localStorage in browser console

### If form doesn't populate:
- Ensure WebSocket connection is active
- Wait for AI to explicitly state field content
- Check that field names match in response

## Demo Variations

### Technical Audience (IT/Developers)
- Focus on WebSocket real-time updates
- Show API responses in browser dev tools
- Discuss Claude API integration
- Explain field extraction logic

### HR Audience
- Emphasize employee experience improvement
- Discuss reduction in incomplete applications
- Show how it helps non-native speakers
- Highlight internal mobility benefits

### Executive Audience
- Focus on efficiency metrics
- Discuss employee retention through mobility
- Show professional output quality
- Emphasize multilingual capabilities

## Sample Responses for Common Questions

**Q: "What if someone doesn't have a CV ready?"**
A: "They can simply describe their experience in the chat. The AI will ask guided questions to build the application."

**Q: "How does it handle confidential information?"**
A: "All data stays within your infrastructure. The AI only processes what's explicitly shared in the chat."

**Q: "Can it handle other languages?"**
A: "Currently English and German, but the architecture supports adding any language Claude supports."

**Q: "How accurate is the form filling?"**
A: "The AI explicitly confirms content before populating fields, ensuring accuracy and allowing user review."

## Tips for Smooth Demo

1. **Pre-load the page** before demo starts
2. **Have both CVs copied** to clipboard beforehand
3. **Use incognito mode** to show fresh experience
4. **Prepare answers** to clarification questions
5. **Show both languages** if audience is international
6. **Keep responses concise** to maintain pace
7. **Have backup plan** if API is slow

---

Remember: The goal is to show how AI makes internal mobility more accessible and less intimidating for employees!