# PWA Icons

This directory contains the Progressive Web App icons for PsychSync.

## Required Icons

The following icon sizes are needed for complete PWA functionality:

- **icon-16x16.png** - 16x16px - Favicon
- **icon-32x32.png** - 32x32px - Favicon (high DPI)
- **icon-72x72.png** - 72x72px - Android launcher (legacy)
- **icon-96x96.png** - 96x96px - Android launcher
- **icon-128x128.png** - 128x128px - Chrome Web Store
- **icon-152x152.png** - 152x152px - iOS touch icon
- **icon-167x167.png** - 167x167px - iOS touch icon (iPad Pro)
- **icon-180x180.png** - 180x180px - iOS touch icon (iPhone)
- **icon-192x192.png** - 192x192px - PWA icon (standard)
- **icon-384x384.png** - 384x384px - PWA icon (high DPI)
- **icon-512x512.png** - 512x512px - PWA icon (splash screen)
- **badge.png** - 72x72px - Notification badge

## Design Guidelines

- Use the PsychSync logo (brain/mind theme)
- Maintain consistent branding with the web app
- Ensure readability at small sizes
- Use transparent background where appropriate
- Include both color and monochrome versions

## Icon Requirements

### PWA Manifest Icons
- Must be PNG format
- Should have transparent or white background
- Minimum safe area: 80% of icon size (avoid edges)

### iOS Icons
- Must be PNG format without transparency
- Apple recommends no transparency for iOS icons
- Include gloss effect if desired (iOS adds automatically)

### Android Icons
- Can be PNG with transparency
- Adaptive icon support recommended for Android 8.0+

## Placeholder Icons

The placeholder files should be replaced with actual designed icons:

1. Create SVG version of the PsychSync logo
2. Export to all required sizes using design tools
3. Optimize for web use (lossy compression for large icons)
4. Test on actual devices for visual quality

## Tools for Icon Generation

- [PWA Asset Generator](https://www.pwabuilder.com/imageGenerator)
- [Favicon.io](https://favicon.io/)
- [RealFaviconGenerator](https://realfavicongenerator.net/)
- Adobe Illustrator/Sketch/Figma for design

## Testing

Test icons on:
- Chrome DevTools (Application > Manifest)
- iOS Safari (Add to Home Screen)
- Android Chrome (Add to Home Screen)
- Various device sizes and pixel densities
