# 📸 Screenshot Automation Guide

## Quick Start

### 1. Install Puppeteer
```bash
npm install puppeteer
```

### 2. Start Your Dev Server
```bash
cd frontend
npm run dev
# Server should run on http://localhost:5173
```

### 3. Capture Screenshots
```bash
node capture-screenshots.js
```

### 4. View Results
```bash
open screenshots/index.html
# or
firefox screenshots/index.html
```

---

## What Gets Captured

The script captures **13 automated screenshots**:

| # | Filename | Description |
|---|----------|-------------|
| 1 | `01-sidebar-collapsed.png` | Full sidebar, all sections collapsed |
| 2 | `02-sidebar-expanded-all.png` | Full sidebar, all sections expanded |
| 3 | `03-early-warning-collapsed.png` | Early Warning section collapsed |
| 4 | `04-early-warning-expanded.png` | Early Warning section expanded |
| 5 | `05-early-warning-hover.png` | Hover state on Early Warning |
| 6 | `06-active-burnout-prevention.png` | Active state: Burnout Prevention |
| 7 | `07-active-behavioral-analytics.png` | Active state: Behavioral Analytics |
| 8 | `08-burnout-prevention-page.png` | Full Burnout Prevention page |
| 9 | `09-team-dashboard-page.png` | Full Team Dashboard page |
| 10 | `10-anomaly-detection-page.png` | Full Anomaly Detection page |
| 11 | `11-visual-separator.png` | Visual separator detail |
| 12 | `12-mobile-sidebar-collapsed.png` | Mobile view collapsed |
| 13 | `13-mobile-early-warning-expanded.png` | Mobile view expanded |

---

## Customization

### Change Base URL
Edit `capture-screenshots.js`:
```javascript
const CONFIG = {
  baseUrl: 'http://localhost:3000', // Your port
  // ...
};
```

### Add New Screenshots
Add to the `SCREENSHOTS` array:
```javascript
{
  name: '14-my-new-screenshot',
  url: '/my-page',
  action: async (page) => {
    // Custom actions
    await page.click('#my-button');
  },
  description: 'My custom screenshot'
}
```

### Change Viewport Sizes
```javascript
const CONFIG = {
  viewport: {
    desktop: { width: 1920, height: 1080 },
    custom: { width: 2560, height: 1440 } // Add custom
  }
};
```

---

## Manual Screenshots (If Script Fails)

If the automated script doesn't work, capture these manually:

### Desktop Screenshots
1. Open `http://localhost:5173/dashboard`
2. Press **Cmd+Shift+4** (Mac) or **PrtScn** (Windows)
3. Capture the following states:

#### **Core Screenshots:**
- [ ] Sidebar collapsed (all sections closed)
- [ ] Sidebar expanded (Early Warning section open)
- [ ] Visual separator ("⚡ Risk Detection")
- [ ] Active state on Burnout Prevention
- [ ] Active state on Behavioral Analytics

#### **Feature Pages:**
- [ ] `/burnout-prevention` - Full page
- [ ] `/behavioral-analytics` - Full page
- [ ] `/anomaly-detection` - Full page
- [ ] `/team-dashboard` - Full page
- [ ] `/employee-safety` - Full page

#### **Mobile Screenshots:**
1. Open Chrome DevTools (**Cmd+Option+I**)
2. Click device toolbar (**Cmd+Shift+M**)
3. Select iPhone 12 Pro or similar
4. Capture:
  - [ ] Mobile sidebar collapsed
  - [ ] Mobile Early Warning expanded

---

## Screenshot Best Practices

### ✅ DO:
- Use high-DPI displays (Retina/4K)
- Capture at 100% zoom (no browser zoom)
- Use consistent viewport sizes
- Include full browser window (shows context)
- Clean browser state (no extensions, clear cache)
- Use consistent time of day (affects colors/themes)

### ❌ DON'T:
- Crop images too tightly
- Use blurry/low-res captures
- Mix viewport sizes
- Include personal data/sensitive info
- Capture during animations/transitions
- Use browser extensions that modify UI

---

## Image Requirements

### For Documentation:
- **Format:** PNG (lossless)
- **Resolution:** 1920x1080 minimum
- **DPI:** 72 (web) or 300 (print)
- **File Size:** < 2MB per image

### For Presentations:
- **Format:** PNG or JPG
- **Resolution:** 2560x1440 (2K)
- **Aspect Ratio:** 16:9
- **Compression:** High quality

### For Web:
- **Format:** WebP (modern browsers)
- **Resolution:** 1920x1080
- **Compression:** Balanced
- **Lazy Load:** Yes

---

## Troubleshooting

### Script fails to connect
**Problem:** Cannot connect to localhost:5173
**Solution:**
```bash
# Check if server is running
curl http://localhost:5173

# Start server if not running
cd frontend && npm run dev
```

### Screenshots are blank
**Problem:** Empty/black screenshots
**Solution:**
- Increase `delays.pageLoad` in config
- Check for JavaScript errors
- Verify page rendering: `await page.waitForSelector('aside')`

### Wrong viewport size
**Problem:** Images are wrong size
**Solution:**
```javascript
// Force viewport before each screenshot
await page.setViewport({ width: 1920, height: 1080 });
await page.goto(url);
```

### Mobile screenshots don't work
**Problem:** Mobile view not capturing
**Solution:**
- Ensure Chrome DevTools device emulation is supported
- Use actual mobile device or emulator
- Test viewport: `{ width: 375, height: 812, isMobile: true }`

---

## Output Structure

```
screenshots/
├── index.html                  # Auto-generated gallery
├── 01-sidebar-collapsed.png
├── 02-sidebar-expanded-all.png
├── 03-early-warning-collapsed.png
├── 04-early-warning-expanded.png
├── 05-early-warning-hover.png
├── 06-active-burnout-prevention.png
├── 07-active-behavioral-analytics.png
├── 08-burnout-prevention-page.png
├── 09-team-dashboard-page.png
├── 10-anomaly-detection-page.png
├── 11-visual-separator.png
├── 12-mobile-sidebar-collapsed.png
└── 13-mobile-early-warning-expanded.png
```

---

## Advanced Usage

### Batch Processing
```bash
# Capture all viewports
for viewport in desktop laptop tablet mobile; do
  VIEWPORT=$viewport node capture-screenshots.js
done
```

### CI/CD Integration
```yaml
# .github/workflows/screenshots.yml
name: Screenshots
on: [push]
jobs:
  capture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm install
      - run: npm run dev &
      - run: sleep 10
      - run: node capture-screenshots.js
      - uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: screenshots/
```

### Docker Environment
```bash
# Run in Docker container
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  node:18 \
  sh -c "npm install && node capture-screenshots.js"
```

---

## Next Steps

After capturing screenshots:

1. **Review Quality**
   - Check for blur/artifacts
   - Verify text is readable
   - Ensure colors are accurate

2. **Organize**
   - Rename if needed
   - Add metadata/tags
   - Create categories

3. **Optimize**
   - Compress if needed (TinyPNG)
   - Convert to WebP for web
   - Create thumbnails

4. **Distribute**
   - Upload to documentation
   - Add to presentations
   - Share with team

---

## Resources

- [Puppeteer Documentation](https://pptr.dev)
- [Screenshot Best Practices](https://www.smashingmagazine.com/2018/10/web-performance-monitoring-puppeteer/)
- [Automated Visual Testing](https://www.cypress.io/blog/2019/12/05/screenshot-comparison-in-cypress/)
