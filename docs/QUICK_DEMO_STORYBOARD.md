# 🎬 Quick Demo Storyboard (2-Minute Version)

**Purpose**: Fast, shareable demo for team onboarding
**Duration**: 2 minutes
**Format**: Screen recording with voiceover

---

## ⏱️ Timeline Breakdown

| Time | Scene | Visual | Audio |
|------|-------|--------|-------|
| 0:00-0:15 | Intro | PsychSync dashboard | "Hi! Quick demo: Memory leak testing in 2 minutes." |
| 0:15-0:30 | Open Tool | Navigate to test file | "Open frontend/scripts/quick-memory-test.html" |
| 0:30-0:45 | Show Interface | Test tool overview | "Clean interface with metrics, progress, and controls" |
| 0:45-0:55 | Start Test | Click Quick Test button | "Click Quick Test - runs for 2 minutes" |
| 0:55-1:15 | Show Progress | Speed up footage | "Simulates user actions while tracking memory" |
| 1:15-1:30 | Show Results | Green success box | "Results: Growth of only 7.6 MB - PASS!" |
| 1:30-1:45 | Explain | Show metrics cards | "Easy: Under 50MB = PASS, 50-100MB = WARN, over 100MB = FAIL" |
| 1:45-2:00 | CTA | Resources list | "That's it! See docs for more. Happy testing!" |

---

## 📝 Voiceover Script

### (0:00-0:15) Intro
```
"Hi everyone! Quick demo today: How to run memory leak tests for PsychSync
in just 2 minutes. Let's dive in!"
```

### (0:15-0:30) Open Tool
```
"First, open the test tool at frontend/scripts/quick-memory-test.html
It opens right in your browser - no installation needed."
```

### (0:30-0:45) Show Interface
```
"You'll see a clean interface showing:
- Status and progress
- Real-time memory metrics
- Test controls
- And a detailed log"
```

### (0:45-0:55) Start Test
```
"Just click the 'Quick Test (2 min)' button to start.
The test will automatically simulate user actions while monitoring memory."
```

### (0:55-1:15) Show Progress
```
"Watch as it runs - clicking, scrolling, navigating through your app.
Memory is tracked every 2 seconds, so we catch any leaks immediately."
```

### (1:15-1:30) Show Results
```
"And done! In just 2 minutes, we have our results:
- Memory grew only 7.6 MB
- That's well within healthy limits
- Green status means PASS - safe to deploy!"
```

### (1:30-1:45) Explain Criteria
```
"Reading results is easy:
- Under 50 MB growth? ✅ Deploy!
- 50 to 100 MB? ⚠️ Review first
- Over 100 MB? ❌ Fix before deploy"
```

### (1:45-2:00) Wrap Up
```
"That's it! Fast, easy, automated.

Check out docs/QA_LOAD_TESTING_GUIDE.md for details.
Happy testing!"
```

---

## 🎨 Screen Shots Needed

Capture these screens for the video:

1. **Test Interface** (full page, clean)
2. **Clicking Quick Test** (button hover/click)
3. **Progress** (partially filled progress bar)
4. **Results** (green success box showing)
5. **Metrics** (all three cards showing values)

---

## 💡 Production Tips

### Screen Recording Software Options

**Mac**:
- QuickTime Player (built-in)
- CleanShot X (paid, excellent)
- Kap (free, open source)

**Windows**:
- Xbox Game Bar (Win+G)
- OBS Studio (free)
- Loom (free/paid)

**Browser-Based**:
- Loom Chrome extension
- Vidyard Chrome extension
- Awesome Screenshot extension

### Recording Settings

```yaml
Resolution: 1920x1080
Frame Rate: 30 fps
Format: MP4 (H.264)
Audio: Built-in microphone
```

### Editing Software

**Free**:
- iMovie (Mac)
- Shotcut (Cross-platform)
- OpenShot (Cross-platform)
- DaVinci Resolve (Professional, free)

**Quick & Simple**:
- Trim footage: QuickTime (Mac) or Photos (Win)
- Add text overlays: Shotcut or iMovie
- Export: H.264, 1080p, 30fps

---

## 📱 Alternative: Screen Recording Workflow

### Using Loom (Easiest)

```bash
1. Install Loom Chrome extension
2. Click Loom icon → "New Screen Recording"
3. Select "Current Tab"
4. Open quick-memory-test.html
4. Click "Start Recording"
5. Perform the demo
6. Click "Stop Recording"
7. Download MP4
8. Upload to sharing platform
```

### Using QuickTime (Mac)

```bash
1. Open QuickTime Player
2. File → New Screen Recording
3. Click red record button
4. Select entire screen or portion
5. Perform demo
6. Stop recording
8. File → Export → 1080p
```

### Using OBS Studio (Advanced)

```bash
1. Download OBS Studio
2. Add Source → Display Capture
3. Add Source → Audio Input Capture
4. Set Output Resolution: 1920x1080
5. Start Recording
6. Perform demo
7. Stop Recording
8. File → Export → MP4
```

---

## 🎬 Creating the Video: Step-by-Step

### Step 1: Prepare Your Environment

```bash
# 1. Start frontend
cd frontend
npm run dev

# 2. Open test file in Chrome
open scripts/quick-memory-test.html

# 3. Open a terminal/log window for reference
open docs/QA_LOAD_TESTING_GUIDE.md
```

### Step 2: Rehearse Once

```
Run through the demo once without recording to:
- Check audio levels
- Practice smooth mouse movements
- Time each section
- Identify any issues
```

### Step 3: Record

```
Start recording and follow the script:
- Speak clearly and confidently
- Move mouse smoothly
- Pause briefly at key moments
- Don't worry about small mistakes
```

### Step 4: Edit

```
1. Trim off beginning/ending
2. Remove major mistakes
3. Add text overlays (optional)
4. Ensure audio is clear
5. Export in appropriate format
```

---

## 📊 Alternative: Create GIF Demo

For ultra-fast sharing, create an animated GIF:

```python
# 1. Record demo using any tool
# 2. Use gifski (Mac) to convert:
brew install gifski
gifski screen-recording.mov --output memory-test-demo.gif

# 3. Or use online tool:
#    https://www.cloudconvert.com/mov-to-gif
#    https://ezgif.com/video-to-gif
```

**GIF Settings**:
- Duration: 30-60 seconds max
- Frame rate: 10-15 fps
- Resolution: 720p (reduces file size)
- Loop: Yes

---

## 🎯 Video Distribution

### Where to Share

**Internal**:
- Company Google Drive/Dropbox
- Slack #qa-automation channel
- Confluence/Notion wiki
- LMS (Learning Management System)

**External** (if applicable):
- YouTube (unlisted)
- Vimeo
- Company knowledge base

### File Organization

```
/docs/
  /videos/
    memory-test-2min-demo.mp4       # Full demo
    memory-test-quick-demo.gif       # Short loop
    memory-test-thumbnails/          # Preview images
        screenshot-1.png
        screenshot-2.png
        ...
```

---

## ✅ Final Checklist

Before publishing:

- [ ] Audio is clear and understandable
- [ ] Screen is readable (not too small)
- [ ] Mouse movements are smooth
- [ ] Text overlays are readable
- [ ] Video is 2-3 minutes max
- [ ] File size is reasonable (< 50 MB)
- [ ] Tested on different devices
- [ ] Closed captions available (optional)

---

## 🚀 Quick Start Summary

**To record this video:**

```bash
1. Open: frontend/scripts/quick-memory-test.html
2. Start screen recording
3. Follow the 2-minute script
4. Stop recording
5. Edit lightly (trim ends)
6. Export as MP4
7. Share with team!
```

**Total time**: ~10 minutes from start to finish!

---

This storyboard makes it super easy to create a professional demo in just 10 minutes! 🎬
