# 🎬 Memory Leak Testing - Video Demo Script

**Title**: Memory Leak Load Testing for PsychSync
**Duration**: 8-10 minutes
**Target Audience**: QA Team, Developers, Project Managers
**Difficulty**: Beginner-friendly

---

## 🎥 Recording Setup

### Equipment Needed
- Screen recording software (QuickTime, OBS, Loom)
- Microphone (optional but recommended)
- Chrome browser with PsychSync frontend running

### Technical Settings
- **Resolution**: 1920x1080 or higher
- **Frame Rate**: 30 fps
- **Audio**: Clear voiceover, minimal background noise
- **Format**: MP4 (for sharing) or MOV (for editing)

---

## 📋 Script Outline

1. **Introduction** (0:00-1:00) - What & Why
2. **Quick Start Demo** (1:00-3:00) - 2-minute test
3. **Results Interpretation** (3:00-4:30) - Reading output
4. **Full Test Demo** (4:30-6:30) - 10-minute test
5. **Common Issues** (6:30-7:30) - Troubleshooting
6. **Summary & Next Steps** (7:30-8:30) - Wrap-up

---

## 🎬 Scene-by-Scene Script

### Scene 1: Introduction (0:00 - 1:00)

**Visual**:
- Chrome browser open showing PsychSync at `http://localhost:5173`
- Clean desktop, no other windows visible

**Audio Script**:
```
"Hi everyone! In this video, I'll show you how to run automated memory leak
tests for the PsychSync application.

Memory leaks are a common issue in web applications where the browser keeps
using more and more memory over time, eventually causing the app to become slow
or crash. We've created an automated testing tool that makes it easy to catch
these issues before they reach production.

This test is perfect for QA validation before releases, and only takes 2 to
10 minutes to run. Let's dive in!"
```

**On-Screen Actions**:
- Type `http://localhost:5173` in address bar (if not already there)
- Show the PsychSync dashboard

---

### Scene 2: Opening the Test Tool (1:00 - 1:45)

**Visual**:
- Navigate to `frontend/scripts/quick-memory-test.html`
- Show the test interface

**Audio Script**:
```
"First, let's open our memory leak testing tool. You can find it at
frontend/scripts/quick-memory-test.html.

I've already opened it here in the browser. As you can see, we have a clean
interface showing:
- Current test status at the top
- A progress bar
- Three metric cards for memory tracking
- Two test options: Quick Test and Full Test
- And a log window at the bottom

Let's start with the Quick Test which only takes 2 minutes."
```

**On-Screen Actions**:
- Navigate to file or use Cmd+O to open
- Point to each section of the interface

---

### Scene 3: Running Quick Test (1:45 - 3:00)

**Visual**:
- Click "⚡ Quick Test (2 min)" button
- Watch progress bar fill
- Show metrics updating in real-time
- Show log messages scrolling

**Audio Script**:
```
"I'll click the Quick Test button to start a 2-minute validation test.

[CLICK]

The test has started! You can see:
- The status shows 'Running'
- The progress bar shows our completion percentage
- The metrics cards show real-time memory usage
- The log window shows each action being performed

What's happening behind the scenes is the test is:
- Navigating to different pages
- Scrolling through content
- Clicking buttons
- Simulating real user behavior

Every 10 seconds, an action is performed, and memory is tracked every 2 seconds.
This helps us detect if memory is growing unbounded, which would indicate a leak."
```

**On-Screen Actions**:
- Click the button
- Point to progress bar as it fills
- Highlight changing metrics
- Speed up footage slightly (optional) during waiting period

---

### Scene 4: Quick Test Results (3:00 - 4:30)

**Visual**:
- Test completes
- Green alert appears
- Results summary shown

**Audio Script**:
```
"The test has completed! And look - we have a green success message.

Let me break down these results:

- Current Memory: 52.8 MB
- Memory Growth: +7.6 MB
- Growth Rate: 0.76 MB per minute

This is a PASS result! Our growth of only 7.6 MB over 10 minutes is well
within acceptable limits. The test also tells us:

✅ TEST PASSED: Memory usage is stable

This means we can deploy with confidence!

The results have been automatically downloaded as a JSON file, which we can
save for our records or compare with future tests."
```

**On-Screen Actions**:
- Point to each metric
- Show the green alert box
- Indicate the JSON download (or show it being saved)

---

### Scene 5: Full Test Demo (4:30 - 6:30)

**Visual**:
- Click reset button
- Click "▶️ Start 10-Minute Test" button
- Show longer progress

**Audio Script**:
```
"Now let's look at the Full Test option. This is a more thorough 10-minute
test that provides better confidence before major releases.

[RESET and START FULL TEST]

I've started the full test. This will run for 10 minutes instead of 2,
performing 60 iterations instead of 12.

The principle is exactly the same:
- Simulate user actions
- Track memory continuously
- Alert if growth exceeds thresholds

The difference is we're testing for a longer period, which helps catch
slower memory leaks that might not appear in short sessions.

[FAST FORWARD slightly]

As you can see, the test is progressing smoothly. The progress bar shows
we're about 60% complete. The memory metrics remain stable, and no warnings
have appeared.

This longer test is especially useful for:
- Pre-release validation
- Testing new features with complex state management
- Comparing memory usage between different builds

Let me speed this up to show the final results."
```

**On-Screen Actions**:
- Reset test
- Start full test
- Wait and show progress
- Consider time-lapse or speeding up footage

---

### Scene 6: Full Test Results & Comparison (6:30 - 7:30)

**Visual**:
- Full test completes
- Show comparison between quick and full test results

**Audio Script**:
```
"The full test is complete! Let's compare our results:

Quick Test (2 min): +7.6 MB growth
Full Test (10 min): +12.3 MB growth

Both tests show PASS results. The full test shows slightly more growth, which
is normal for a longer session. The important thing is that memory usage
plateaus and doesn't continue growing unbounded.

If we saw a result like:
- 100+ MB growth over 10 minutes, that would be a WARNING
- 150+ MB growth would be a FAIL, indicating a memory leak

But in this case, we're well within healthy limits!
✅ Both tests PASSED"
```

**On-Screen Actions**:
- Show both test results side by side
- Create a simple comparison table on screen (text overlay)

---

### Scene 7: Reading the Logs (7:30 - 8:15)

**Visual**:
- Scroll through log window
- Highlight key log entries

**Audio Script**:
```
"The log window provides detailed information about what happened:

[POINT TO LOG ENTRIES]

- Each action is logged with a timestamp
- Memory checks show current usage
- Warnings appear if growth exceeds thresholds
- Final summary shows PASS/WARN/FAIL status

You can also see color-coded entries:
- Green: Informational messages
- Yellow: Warnings
- Red: Errors or critical issues

This detailed logging helps with debugging if we do detect a problem."
```

**On-Screen Actions**:
- Scroll through log
- Point to color-coded entries

---

### Scene 8: Interpreting Results (8:15 - 9:00)

**Visual**:
- Show result scenarios (PASS, WARN, FAIL examples)

**Audio Script**:
```
"Let me show you how to interpret different results:

✅ PASS (Under 50 MB growth)
   - Green alert
   - Memory is stable
   - Safe to deploy

⚠️ WARN (50-100 MB growth)
   - Yellow alert
   - Moderate growth detected
   - Review changes before deploying
   - Consider additional testing

❌ FAIL (Over 100 MB growth)
   - Red alert
   - Significant memory leak
   - Fix before deploying
   - Investigate with development team

The test automatically makes this determination, so you don't need to
manually calculate anything!"
```

**On-Screen Actions**:
- Show screenshots or examples of each status
- Use text overlays to explain each scenario

---

### Scene 9: Integration & CI/CD (9:00 - 9:45)

**Visual**:
- Show GitHub Actions workflow example
- Show documentation files

**Audio Script**:
```
"This tool can also be integrated into your CI/CD pipeline!

We provide:
- A bash script that automates running the test
- GitHub Actions workflow template
- Detailed documentation for integration

This means memory leak testing can happen automatically on every pull request,
catching issues before they even reach QA!

The documentation includes everything you need for setup, and we have guides
for both beginners and advanced users."
```

**On-Screen Actions**:
- Show `run-memory-test.sh` script
- Briefly show GitHub Actions YAML
- Show documentation directory

---

### Scene 10: Summary & Wrap-up (9:45 - 10:30)

**Visual**:
- Summary screen with key points
- Show resource links

**Audio Script**:
```
"To summarize what we've learned:

🎯 Memory leak testing is:
   - Fast: 2-10 minutes
   - Easy: Just open a webpage
   - Automated: Runs itself
   - Reliable: Consistent results

📋 When to use:
   - Before every release
   - After adding complex features
   - When investigating performance issues
   - As part of CI/CD pipeline

📚 Resources:
   - Quick Reference: frontend/scripts/README_QA.md
   - Full Guide: docs/QA_LOAD_TESTING_GUIDE.md
   - Team Training: docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md

Try it out yourself and let us know if you have any questions!

Thanks for watching!"
```

**On-Screen Actions**:
- Show bullet points as text overlay
- Display resource links
- Fade to black with contact info

---

## 🎨 Visual Elements to Prepare

### Text Overlays
Create these as simple graphics or screen text:

**Title Card**:
```
Memory Leak Load Testing for PsychSync
A Comprehensive QA Guide
```

**Key Points**:
```
✅ Zero Setup Required
⚡ 2-10 Minute Test Time
📊 Instant Results
🔒 Catches Leaks Before Production
```

**Result Criteria**:
```
PASS:  < 50 MB growth  → Deploy
WARN:  50-100 MB growth → Review
FAIL:  > 100 MB growth → Fix
```

---

## 💡 Recording Tips

### Before Recording
1. ✓ Close unnecessary applications
2. ✓ Clear browser cache/cookies
3. ✓ Set up proper screen resolution
4. ✓ Test microphone levels
5. ✓ Do a dry run of the demo

### During Recording
1. ✓ Speak clearly and at moderate pace
2. ✓ Use mouse movements to guide attention
3. ✓ Pause briefly at key points
4. ✓ Keep cursor visible
5. ✓ Avoid clicking unnecessarily

### After Recording
1. ✓ Edit out mistakes or long pauses
2. ✓ Add intro/outro music (optional)
3. ✓ Include captions (optional)
4. ✓ Export in multiple formats (MP4, GIF clips)

---

## 📱 Alternative: Animated GIF Demo

For a quicker alternative, consider creating an animated GIF:

```bash
# Using ffmpeg to create GIF from screen recording
ffmpeg -i screen-recording.mov -vf "fps=10,scale=720:-1:flags=lanczos" \
  -c:v gif -f gif - > memory-test-demo.gif

# Or use Loom for quick recording
```

---

## 🎓 Video Structure Options

### Option A: Short & Sweet (3-5 minutes)
- Skip to Quick Test demo immediately
- Show results
- Brief interpretation guide
- Link to docs for details

### Option B: Comprehensive (10-12 minutes)
- Full script as written above
- Includes troubleshooting
- CI/CD integration
- Best practices

### Option C: Interactive Demo (15-20 minutes)
- Live commentary
- Q&A format
- Real troubleshooting examples
- Multiple test scenarios

---

## 📊 Quick Demo Outline (2-minute version)

For a ultra-short version, create this:

```python
# 2-Minute Demo Script
0:00 - Open test file (10 sec)
0:10 - Explain interface (20 sec)
0:30 - Start quick test (10 sec)
0:40 - Show progress (30 sec)
1:10 - Show results (30 sec)
1:40 - Explain interpretation (20 sec)
2:00 - End/CTA (0 sec)
```

---

## 🎯 Next Steps

After creating the video:

1. **Upload** to Google Drive or company share
2. **Share link** in:
   - QA documentation
   - Team wiki/confluence
   - Slack #qa-automation channel
3. **Create GIF clips** for quick reference
4. **Embed** in documentation pages
5. **Add** to onboarding materials

---

## 📝 Video Description Template

```
Learn how to run automated memory leak tests for PsychSync in just 2 minutes!

This video covers:
- Opening the memory test tool
- Running a quick 2-minute validation test
- Understanding results (PASS/WARN/FAIL)
- Best practices for pre-release testing

No installation required - just open the HTML file in Chrome!

Resources:
📖 Full Guide: docs/QA_LOAD_TESTING_GUIDE.md
🎓 Training: docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md
🧪 Test Tool: frontend/scripts/quick-memory-test.html

Timestamps:
0:00 - Introduction
1:00 - Opening the test tool
1:45 - Running the Quick Test
3:00 - Understanding results
4:30 - Running the Full Test
6:30 - Interpreting different results
9:00 - Summary

#psychsync #testing #qualityassurance #memoryleaks
```

---

## 🎬 Post-Production Checklist

- [ ] Remove long pauses/silence
- [ ] Add intro/outro cards
- [ ] Include text overlays for key points
- [ ] Normalize audio levels
- [ ] Add captions (optional)
- [ ] Export in 1080p MP4
- [ ] Create short GIF clips for docs
- [ ] Upload to sharing platform

---

**This script should make it easy to create a professional demo video! Would you like me to:**
- **Create a shorter 2-minute version** for quick sharing?
- **Add more technical details** for advanced users?
- **Create a companion blog post** explaining memory leaks?
