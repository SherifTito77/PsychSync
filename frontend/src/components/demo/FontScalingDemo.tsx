/**
 * Font Scaling Demo Component - Interactive visualization of 50%-200% zoom behavior
 * Shows real-time font scaling effects with accessibility compliance indicators
 */

import React, { useState, useEffect } from 'react';
import { FontScalingValidator } from '../accessibility/FontScalingValidator';

interface FontSizeDemo {
  level: number;
  name: string;
  description: string;
  useCase: string;
}

const FONT_SIZES: FontSizeDemo[] = [
  {
    level: 50,
    name: 'Very Small',
    description: '50% of default size - Minimum practical for reading',
    useCase: 'Users with excellent vision, compact displays'
  },
  {
    level: 75,
    name: 'Small',
    description: '75% of default size - Reduced but still readable',
    useCase: 'Users fitting more content on screen, temporary reduction'
  },
  {
    level: 100,
    name: 'Normal',
    description: '100% of default size - Standard comfortable reading',
    useCase: 'Default setting for most users'
  },
  {
    level: 125,
    name: 'Large',
    description: '125% of default size - Enhanced readability',
    useCase: 'Users with mild vision difficulties, reading comfort'
  },
  {
    level: 150,
    name: 'Extra Large',
    description: '150% of default size - Significantly enhanced readability',
    useCase: 'Users with moderate vision difficulties, accessibility needs'
  },
  {
    level: 175,
    name: 'Very Large',
    description: '175% of default size - Maximum practical size',
    useCase: 'Users with significant vision difficulties'
  },
  {
    level: 200,
    name: 'Maximum WCAG',
    description: '200% of default size - WCAG 2.1 AA requirement',
    useCase: 'WCAG compliance requirement for accessibility'
  }
];

const DEMO_CONTENT = {
  headings: [
    { level: 1, text: 'Main Page Heading - H1' },
    { level: 2, text: 'Section Title - H2' },
    { level: 3, text: 'Subsection Title - H3' },
    { level: 4, text: 'Component Title - H4' },
    { level: 5, text: 'Minor Title - H5' },
    { level: 6, text: 'Smallest Title - H6' }
  ],
  paragraphs: [
    'This is standard body text that demonstrates how paragraph content scales across different font sizes. The quick brown fox jumps over the lazy dog. This pangram helps test how different character combinations render at various sizes.',
    'Typography plays a crucial role in accessibility. When users increase font size to 200%, content should reflow properly without requiring horizontal scrolling. This ensures that users with visual impairments can access all content effectively.',
    'Line height and spacing become increasingly important at larger font sizes. Proper spacing prevents text from feeling cramped and maintains readability across all zoom levels.'
  ],
  // SECURITY: Removed dangerouslySetInnerHTML - using React components instead
  mixedContent: [
    { text: 'This paragraph contains ', bold: 'bold text', postfix: ', ', italic: 'italic text', postfix2: ', and ', link: { text: 'inline links', href: '#' }, postfix3: ' that should all scale proportionally.' },
    { text: 'Numbers and symbols (123, @#$%, &*%) must remain clear and readable at all sizes.' },
    { text: 'Mixed content testing: Regular ', bold: 'bold', postfix1: ' ', italic: 'italic', postfix2: ' ', boldItalic: { bold: 'bold italic', italic: 'italic' }, postfix3: ' and ', link: { text: 'links', href: '#' }, postfix4: '.' }
  ]
};

export const FontScalingDemo: React.FC = () => {
  const [currentFontSize, setCurrentFontSize] = useState(100);
  const [isAnimating, setIsAnimating] = useState(false);
  const [validationResults, setValidationResults] = useState<any>(null);
  const [showValidation, setShowValidation] = useState(false);

  // Apply font size change
  const applyFontSize = (level: number) => {
    setIsAnimating(true);
    setCurrentFontSize(level);
    document.documentElement.style.fontSize = `${level}%`;

    setTimeout(() => {
      setIsAnimating(false);
    }, 300);
  };

  // Reset to default
  const resetFontSize = () => {
    applyFontSize(100);
  };

  // Handle validation complete
  const handleValidationComplete = (results: any[]) => {
    setValidationResults(results);
    setShowValidation(true);
  };

  // Calculate responsive sizing for demo
  const getResponsiveSize = (baseSize: number) => {
    return (baseSize * currentFontSize / 100).toFixed(2);
  };

  // Render heading with appropriate tag
  const renderHeading = (level: number, text: string) => {
    const Tag = `h${level}` as keyof JSX.IntrinsicElements;
    return <Tag>{text}</Tag>;
  };

  return (
    <div className="font-scaling-demo">
      <style>{`
        .font-scaling-demo {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          transition: all 0.3s ease;
        }

        .demo-header {
          text-align: center;
          margin-bottom: 30px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 30px;
          border-radius: 16px;
        }

        .demo-title {
          font-size: 32px;
          margin-bottom: 12px;
          font-weight: 700;
        }

        .demo-subtitle {
          font-size: 18px;
          margin-bottom: 20px;
          opacity: 0.9;
        }

        .current-size-display {
          display: inline-block;
          padding: 12px 24px;
          border-radius: 30px;
          font-weight: 600;
          font-size: 20px;

          /* Firefox fallback - solid background */
          background: rgba(255, 255, 255, 0.85);

          /* Modern browsers - backdrop blur */
          @supports (-webkit-backdrop-filter: blur(10px)) or (backdrop-filter: blur(10px)) {
            background: rgba(255, 255, 255, 0.4);
            -webkit-backdrop-filter: blur(10px);
            backdrop-filter: blur(10px);
          }
        }

        .size-selector {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 40px;
        }

        .size-option {
          background: white;
          border: 3px solid #e0e0e0;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }

        .size-option:hover {
          border-color: #667eea;
          transform: translateY(-2px);
          box-shadow: 0 8px 16px rgba(102, 126, 234, 0.1);
        }

        .size-option.active {
          border-color: #667eea;
          background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
          transform: scale(1.02);
        }

        .size-option.active::before {
          content: '✓';
          position: absolute;
          top: 12px;
          right: 12px;
          background: #667eea;
          color: white;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
        }

        .size-level {
          font-size: 24px;
          font-weight: 700;
          color: #667eea;
          margin-bottom: 8px;
        }

        .size-name {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
          color: #333;
        }

        .size-description {
          font-size: 14px;
          color: #666;
          margin-bottom: 12px;
          line-height: 1.4;
        }

        .size-use-case {
          font-size: 12px;
          color: #888;
          font-style: italic;
        }

        .demo-controls {
          display: flex;
          justify-content: center;
          gap: 16px;
          margin-bottom: 40px;
          flex-wrap: wrap;
        }

        .control-button {
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          min-height: 48px;
          min-width: 48px;
        }

        .control-button.primary {
          background: #667eea;
          color: white;
        }

        .control-button.primary:hover {
          background: #5a6fd8;
        }

        .control-button.secondary {
          background: #f8f9fa;
          color: #333;
          border: 2px solid #dee2e6;
        }

        .control-button.secondary:hover {
          background: #e9ecef;
        }

        .control-button.danger {
          background: #e74c3c;
          color: white;
        }

        .control-button.danger:hover {
          background: #c0392b;
        }

        .content-showcase {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
          margin-bottom: 40px;
        }

        .content-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .section-title {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 20px;
          color: #333;
          border-bottom: 2px solid #667eea;
          padding-bottom: 8px;
        }

        .headings-showcase h1,
        .headings-showcase h2,
        .headings-showcase h3,
        .headings-showcase h4,
        .headings-showcase h5,
        .headings-showcase h6 {
          margin-bottom: 16px;
          line-height: 1.2;
        }

        .headings-showcase h1 {
          font-size: 2rem;
          border-left: 4px solid #667eea;
          padding-left: 12px;
        }

        .headings-showcase h2 {
          font-size: 1.5rem;
          border-left: 4px solid #764ba2;
          padding-left: 12px;
        }

        .headings-showcase h3 {
          font-size: 1.25rem;
        }

        .headings-showcase h4 {
          font-size: 1.125rem;
        }

        .headings-showcase h5 {
          font-size: 1rem;
        }

        .headings-showcase h6 {
          font-size: 0.875rem;
          color: #666;
        }

        .paragraphs-showcase p {
          margin-bottom: 16px;
          line-height: 1.5;
          color: #444;
        }

        .paragraphs-showcase .highlight {
          background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
          padding: 16px;
          border-left: 4px solid #667eea;
          border-radius: 0 8px 8px 0;
        }

        .demo-link {
          color: #667eea;
          text-decoration: none;
          border-bottom: 1px solid transparent;
          transition: border-color 0.2s ease;
        }

        .demo-link:hover {
          border-bottom-color: #667eea;
        }

        .interactive-elements {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          margin-bottom: 40px;
        }

        .elements-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
        }

        .element-group {
          padding: 16px;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
        }

        .element-label {
          font-size: 14px;
          font-weight: 600;
          color: #666;
          margin-bottom: 12px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .button-group {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .demo-button {
          padding: 10px 16px;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
          min-height: 44px;
          min-width: 44px;
        }

        .demo-button:hover {
          background: #f8f9fa;
        }

        .demo-button.primary {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }

        .demo-button.primary:hover {
          background: #5a6fd8;
        }

        .demo-input {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
          min-height: 44px;
          box-sizing: border-box;
        }

        .demo-textarea {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
          min-height: 88px;
          resize: vertical;
          box-sizing: border-box;
        }

        .validation-panel {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .validation-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .validation-title {
          font-size: 20px;
          font-weight: 700;
          color: #333;
        }

        .toggle-button {
          padding: 8px 16px;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }

        .toggle-button:hover {
          background: #5a6fd8;
        }

        .animating {
          opacity: 0.7;
          transform: scale(0.98);
        }

        @media (max-width: 768px) {
          .font-scaling-demo {
            padding: 16px;
          }

          .content-showcase {
            grid-template-columns: 1fr;
            gap: 16px;
          }

          .demo-controls {
            flex-direction: column;
          }

          .control-button {
            width: 100%;
          }

          .elements-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 480px) {
          .size-selector {
            grid-template-columns: 1fr;
          }

          .demo-title {
            font-size: 24px;
          }

          .demo-subtitle {
            font-size: 16px;
          }
        }
      `}</style>

      <div className={`font-scaling-demo ${isAnimating ? 'animating' : ''}`}>
        <div className="demo-header">
          <h1 className="demo-title">🔤 Font Scaling Demo</h1>
          <p className="demo-subtitle">
            Interactive demonstration of WCAG 2.1 AA compliant font scaling from 50% to 200%
          </p>
          <div className="current-size-display">
            Current Zoom: {currentFontSize}%
          </div>
        </div>

        <div className="size-selector">
          {FONT_SIZES.map(({ level, name, description, useCase }) => (
            <div
              key={level}
              className={`size-option ${currentFontSize === level ? 'active' : ''}`}
              onClick={() => applyFontSize(level)}
            >
              <div className="size-level">{level}%</div>
              <div className="size-name">{name}</div>
              <div className="size-description">{description}</div>
              <div className="size-use-case">{useCase}</div>
            </div>
          ))}
        </div>

        <div className="demo-controls">
          <button
            className="control-button primary"
            onClick={() => setShowValidation(!showValidation)}
          >
            {showValidation ? 'Hide' : 'Show'} Accessibility Validator
          </button>

          <button
            className="control-button secondary"
            onClick={resetFontSize}
          >
            Reset to 100%
          </button>

          <button
            className="control-button secondary"
            onClick={() => {
              const levels = [50, 75, 100, 125, 150, 175, 200];
              let index = 0;

              const interval = setInterval(() => {
                if (index >= levels.length) {
                  clearInterval(interval);
                  resetFontSize();
                  return;
                }
                applyFontSize(levels[index]);
                index++;
              }, 1000);
            }}
          >
            Auto Demo (7s)
          </button>
        </div>

        <div className="content-showcase">
          <div className="content-section headings-showcase">
            <h3 className="section-title">📝 Typography Scaling</h3>
            {DEMO_CONTENT.headings.map(({ level, text }) => (
              <div key={level}>
                {renderHeading(level, text)}
              </div>
            ))}
          </div>

          <div className="content-section paragraphs-showcase">
            <h3 className="section-title">📄 Text Content Scaling</h3>
            {DEMO_CONTENT.paragraphs.map((paragraph, index) => (
              <p key={index} className={index === 1 ? 'highlight' : ''}>
                {paragraph}
              </p>
            ))}

            <h4 className="section-title" style={{ fontSize: '16px', marginTop: '24px' }}>
              Mixed Content Testing
            </h4>
            {DEMO_CONTENT.mixedContent.map((content, index) => (
              <p key={index}>
                {typeof content === 'string' ? (
                  content
                ) : (
                  <>
                    {content.text}
                    {content.bold && <strong>{content.bold}</strong>}
                    {content.postfix}
                    {content.italic && <em>{content.italic}</em>}
                    {content.postfix2}
                    {content.boldItalic && (
                      <strong><em>{content.boldItalic.bold}</em></strong>
                    )}
                    {content.postfix3 || content.postfix}
                    {content.link && <a href={content.link.href} className="demo-link">{content.link.text}</a>}
                    {content.postfix3}
                  </>
                )}
              </p>
            ))}
          </div>
        </div>

        <div className="interactive-elements">
          <h3 className="section-title">🖱️ Interactive Elements</h3>
          <div className="elements-grid">
            <div className="element-group">
              <div className="element-label">Buttons</div>
              <div className="button-group">
                <button className="demo-button">Default</button>
                <button className="demo-button primary">Primary</button>
                <button className="demo-button">Long Button Text</button>
              </div>
            </div>

            <div className="element-group">
              <div className="element-label">Form Inputs</div>
              <input
                type="text"
                className="demo-input"
                placeholder="Text input scales properly"
                defaultValue="Sample text"
              />
            </div>

            <div className="element-group">
              <div className="element-label">Text Area</div>
              <textarea
                className="demo-textarea"
                placeholder="Multi-line text input"
                defaultValue="This textarea scales properly at all font sizes while maintaining readability and accessibility."
              />
            </div>

            <div className="element-group">
              <div className="element-label">Links</div>
              <div>
                <a href="#" className="demo-link" style={{ marginRight: '16px' }}>
                  Primary Link
                </a>
                <a href="#" className="demo-link">
                  Secondary Link
                </a>
              </div>
            </div>
          </div>
        </div>

        {showValidation && (
          <div className="validation-panel">
            <div className="validation-header">
              <h3 className="validation-title">♿ Accessibility Validation</h3>
              <button
                className="toggle-button"
                onClick={() => setShowValidation(false)}
              >
                Close
              </button>
            </div>

            <FontScalingValidator
              onValidationComplete={handleValidationComplete}
              autoRun={true}
              testLevels={[100, 150, 200]}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default FontScalingDemo;
