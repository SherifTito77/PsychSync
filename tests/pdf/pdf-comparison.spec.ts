import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('PDF Generation and Comparison', () => {
  const testReportsDir = 'test-reports';
  const baselineDir = path.join(testReportsDir, 'pdf-baseline');
  const actualDir = path.join(testReportsDir, 'pdf-actual');
  const diffDir = path.join(testReportsDir, 'pdf-diff');

  test.beforeAll(async () => {
    // Ensure directories exist
    [baselineDir, actualDir, diffDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  });

  test('should generate MBTI assessment report PDF', async ({ page }) => {
    // Login and take assessment
    await page.goto('http://localhost:3000/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password');
    await page.click('[data-testid="login-button"]');

    await page.goto('/assessments/mbti');
    await page.fill('[data-testid="assessment-answers"]', JSON.stringify(getMockMBTIAnswers()));
    await page.click('[data-testid="submit-assessment"]');

    // Generate PDF report
    await page.click('[data-testid="generate-pdf"]');

    // Wait for PDF download
    const download = await page.waitForEvent('download');
    const pdfPath = path.join(actualDir, `mbti-report-${Date.now()}.pdf`);
    await download.saveAs(pdfPath);

    // Verify PDF exists and has content
    expect(fs.existsSync(pdfPath)).toBe(true);
    expect(fs.statSync(pdfPath).size).toBeGreaterThan(1000);

    // Visual comparison with baseline (if exists)
    const baselinePath = path.join(baselineDir, 'mbti-report-baseline.pdf');
    if (fs.existsSync(baselinePath)) {
      await comparePDFs(baselinePath, pdfPath, 'mbti-report-comparison');
    }
  });

  test('should generate team analytics PDF', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    await page.fill('[data-testid="email"]', 'teamlead@example.com');
    await page.fill('[data-testid="password"]', 'password');
    await page.click('[data-testid="login-button"]');

    await page.goto('/team/analytics');
    await page.click('[data-testid="export-pdf"]');

    const download = await page.waitForEvent('download');
    const pdfPath = path.join(actualDir, `team-analytics-${Date.now()}.pdf`);
    await download.saveAs(pdfPath);

    // Verify PDF structure
    const pdfContent = await extractPDFContent(pdfPath);
    expect(pdfContent).toContain('Team Analytics');
    expect(pdfContent).toContain('Personality Distribution');
  });

  test('should validate PDF accessibility', async ({ page }) => {
    await page.goto('/assessments/mbti/report/123');
    await page.click('[data-testid="generate-pdf"]');

    const download = await page.waitForEvent('download');
    const pdfPath = path.join(actualDir, `accessibility-test-${Date.now()}.pdf`);
    await download.saveAs(pdfPath);

    // Check for accessibility features
    const pdfContent = await extractPDFContent(pdfPath);
    expect(pdfContent).toContain('/Title');
    expect(pdfContent).toContain('/Lang');
  });

  test('should compare PDF screenshots for visual regression', async ({ page }) => {
    await page.goto('/reports/mbti/sample');

    // Capture screenshot of PDF viewer
    await page.waitForSelector('[data-testid="pdf-viewer"]');
    const screenshot = await page.locator('[data-testid="pdf-viewer"]').screenshot({
      type: 'jpeg',
      quality: 90
    });

    // Compare with baseline
    expect(screenshot).toMatchSnapshot('mbti-pdf-viewer.jpg');
  });
});

async function comparePDFs(baselinePath: string, actualPath: string, testName: string) {
  // PDF comparison implementation
  const pdf2pic = require('pdf2pic');
  const pixelmatch = require('pixelmatch');
  const { createCanvas } = require('canvas');

  // Convert PDFs to images
  const baselineImage = await pdf2pic.convert(baselinePath);
  const actualImage = await pdf2pic.convert(actualPath);

  // Compare images
  const img1 = await loadImage(baselineImage.path);
  const img2 = await loadImage(actualImage.path);

  const { width, height } = img1;
  const diff = createCanvas(width, height);
  const ctx = diff.getContext('2d');

  const numDiffPixels = pixelmatch(
    img1.data, img2.data, ctx.data, width, height,
    { threshold: 0.1 }
  );

  // Save diff image if differences exist
  if (numDiffPixels > 0) {
    const diffBuffer = diff.toBuffer('image/png');
    fs.writeFileSync(path.join(diffDir, `${testName}-diff.png`), diffBuffer);
  }

  // Assert differences are within acceptable range
  const totalPixels = width * height;
  const diffPercentage = (numDiffPixels / totalPixels) * 100;
  expect(diffPercentage).toBeLessThan(0.1); // Less than 0.1% difference
}

function getMockMBTIAnswers() {
  // Generate mock MBTI answers (90 questions, 1-4 scale)
  return Array.from({ length: 90 }, () => Math.floor(Math.random() * 4) + 1);
}

async function extractPDFContent(filePath: string): Promise<string> {
  const pdf = require('pdf-parse');
  const dataBuffer = fs.readFileSync(filePath);
  const data = await pdf(dataBuffer);
  return data.text;
}