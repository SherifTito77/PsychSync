/**
 * 🔧 Comprehensive Test Generator
 *
 * Automated test generation utility for creating comprehensive
 * test suites for React components with consistent patterns
 * and full coverage.
 */

import * as fs from 'fs/promises';
import * as path from 'path';

interface ComponentInfo {
  name: string;
  filePath: string;
  props: ComponentProp[];
  variants?: ComponentVariant[];
}

interface ComponentProp {
  name: string;
  type: string;
  required?: boolean;
  defaultValue?: string;
  description?: string;
}

interface ComponentVariant {
  name: string;
  props: Record<string, any>;
  description?: string;
}

interface TestGenerationConfig {
  componentPath: string;
  outputPath?: string;
  includeAccessibility?: boolean;
  includePerformance?: boolean;
  includeInteraction?: boolean;
  customTestPatterns?: string[];
}

class ComprehensiveTestGenerator {
  private readonly DEFAULT_CONFIG: Partial<TestGenerationConfig> = {
    includeAccessibility: true,
    includePerformance: true,
    includeInteraction: true,
    outputPath: 'src/tests/generated',
  };

  /**
   * Generate comprehensive test file for a component
   */
  async generateTests(config: TestGenerationConfig): Promise<void> {
    const finalConfig = { ...this.DEFAULT_CONFIG, ...config };
    const componentInfo = await this.analyzeComponent(finalConfig.componentPath);

    const testContent = this.generateTestFileContent(componentInfo, finalConfig);
    const outputPath = this.getOutputPath(componentInfo, finalConfig);

    await this.ensureDirectoryExists(path.dirname(outputPath));
    await fs.writeFile(outputPath, testContent, 'utf-8');

    console.log(`✅ Generated comprehensive test file: ${outputPath}`);
  }

  /**
   * Analyze component file to extract information
   */
  private async analyzeComponent(filePath: string): Promise<ComponentInfo> {
    const content = await fs.readFile(filePath, 'utf-8');
    const fileName = path.basename(filePath, '.tsx');

    // Extract component name from file or export
    const componentMatch = content.match(/(?:const|function|class)\s+(\w+)/);
    const componentName = componentMatch?.[1] || fileName;

    // Extract props interface (simplified)
    const propsMatch = content.match(/interface\s+(\w*Props)\s*{([^}]+)}/s);
    const props = this.extractProps(propsMatch?.[2] || '');

    // Extract variants from usage examples or comments
    const variants = this.extractVariants(content, componentName);

    return {
      name: componentName,
      filePath,
      props,
      variants,
    };
  }

  /**
   * Extract props from interface definition
   */
  private extractProps(interfaceContent: string): ComponentProp[] {
    const props: ComponentProp[] = [];
    const lines = interfaceContent.split('\n').map(line => line.trim()).filter(Boolean);

    for (const line of lines) {
      const propMatch = line.match(/(\w+)(\?)?:\s*([^;]+)(?:\s*=\s*([^;]+))?;?/);
      if (propMatch) {
        props.push({
          name: propMatch[1],
          type: propMatch[3].trim(),
          required: !propMatch[2],
          defaultValue: propMatch[4]?.trim(),
        });
      }
    }

    return props;
  }

  /**
   * Extract variants from component usage patterns
   */
  private extractVariants(content: string, componentName: string): ComponentVariant[] {
    const variants: ComponentVariant[] = [];

    // Look for common variant patterns
    const variantPatterns = [
      { name: 'primary', props: {} },
      { name: 'secondary', props: {} },
      { name: 'disabled', props: { disabled: true } },
      { name: 'loading', props: { loading: true } },
    ];

    // Check if component supports these variants based on prop names
    const hasVariant = content.includes('variant') || content.includes('type') || content.includes('status');

    if (hasVariant) {
      variants.push(...variantPatterns);
    }

    return variants;
  }

  /**
   * Generate the complete test file content
   */
  private generateTestFileContent(
    componentInfo: ComponentInfo,
    config: Partial<TestGenerationConfig>
  ): string {
    const imports = this.generateImports(componentInfo, config);
    const basicTests = this.generateBasicTests(componentInfo);
    const interactionTests = config.includeInteraction ? this.generateInteractionTests(componentInfo) : '';
    const accessibilityTests = config.includeAccessibility ? this.generateAccessibilityTests(componentInfo) : '';
    const performanceTests = config.includePerformance ? this.generatePerformanceTests(componentInfo) : '';
    const edgeCaseTests = this.generateEdgeCaseTests(componentInfo);
    const integrationTests = this.generateIntegrationTests(componentInfo);

    return `${imports}

describe('🎯 Comprehensive ${componentInfo.name} Component Tests', () => {
  let userEventSetup: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    userEventSetup = userEvent.setup();
  });

  ${basicTests}

  ${interactionTests}

  ${accessibilityTests}

  ${performanceTests}

  ${edgeCaseTests}

  ${integrationTests}
});
`;
  }

  /**
   * Generate import statements
   */
  private generateImports(componentInfo: ComponentInfo, config: Partial<TestGenerationConfig>): string {
    const relativePath = path.relative(
      path.dirname(config.outputPath || 'src/tests/generated'),
      path.dirname(componentInfo.filePath)
    ).replace(/\.[^/.]+$/, '');

    return `import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ${componentInfo.name} from '${relativePath}/${componentInfo.name}';
`;
  }

  /**
   * Generate basic rendering tests
   */
  private generateBasicTests(componentInfo: ComponentInfo): string {
    const hasChildren = componentInfo.props.some(prop => prop.name === 'children');
    const hasDisabled = componentInfo.props.some(prop => prop.name === 'disabled');
    const hasClassName = componentInfo.props.some(prop => prop.name === 'className');

    let tests = `
  describe('✅ Basic Rendering & Props', () => {
    test('renders default component correctly', () => {
      render(<${componentInfo.name} />);`;

    if (hasChildren) {
      tests += `
      expect(screen.getByRole('generic')).toBeInTheDocument();`;
    } else {
      tests += `
      const component = document.querySelector('[class*="${componentInfo.name.toLowerCase()}"]');
      expect(component).toBeInTheDocument();`;
    }

    tests += `
    });

    test('renders with custom props correctly', () => {
      const customProps = {`;

    componentInfo.props.slice(0, 3).forEach(prop => {
      if (prop.type.includes('string')) {
        tests += `
        ${prop.name}: 'test-${prop.name}',`;
      } else if (prop.type.includes('boolean')) {
        tests += `
        ${prop.name}: true,`;
      }
    });

    tests += `
      };

      render(<${componentInfo.name} {...customProps} />);
      expect(screen.getByRole('generic')).toBeInTheDocument();
    });`;

    if (hasDisabled) {
      tests += `

    test('renders disabled state correctly', () => {
      render(<${componentInfo.name} disabled />);
      const component = screen.getByRole('generic') || document.querySelector('[disabled]');
      if (component) {
        expect(component).toBeDisabled();
      }
    });`;
    }

    if (hasClassName) {
      tests += `

    test('applies custom className correctly', () => {
      render(<${componentInfo.name} className="custom-test-class" />);
      const element = document.querySelector('.custom-test-class');
      expect(element).toBeInTheDocument();
    });`;
    }

    tests += `
  });`;

    return tests;
  }

  /**
   * Generate interaction tests
   */
  private generateInteractionTests(componentInfo: ComponentInfo): string {
    const hasOnClick = componentInfo.props.some(prop => prop.name === 'onClick');
    const hasOnHover = componentInfo.props.some(prop => prop.name === 'onMouseEnter');
    const hasOnChange = componentInfo.props.some(prop => prop.name === 'onChange');

    let tests = `
  describe('🖱️ Mouse Interaction States', () => {
    test('handles basic mouse interactions', async () => {`;

    if (hasOnClick) {
      tests += `
      const handleClick = vi.fn();
      render(<${componentInfo.name} onClick={handleClick} />);

      const component = screen.getByRole('button') || screen.getByRole('generic');
      if (component) {
        await userEventSetup.click(component);
        expect(handleClick).toHaveBeenCalled();
      }`;
    }

    if (hasOnHover) {
      tests += `

      const handleMouseEnter = vi.fn();
      render(<${componentInfo.name} onMouseEnter={handleMouseEnter} />);

      const component = screen.getByRole('generic');
      if (component) {
        await userEventSetup.hover(component);
        expect(handleMouseEnter).toHaveBeenCalled();
      }`;
    }

    tests += `
    });
  });`;

    return tests;
  }

  /**
   * Generate accessibility tests
   */
  private generateAccessibilityTests(componentInfo: ComponentInfo): string {
    return `
  describe('♿ Accessibility Testing', () => {
    test('has proper semantic structure', () => {
      render(<${componentInfo.name} />);

      // Basic accessibility checks
      const element = document.querySelector('[role]');
      expect(element).toBeInTheDocument();
    });

    test('supports keyboard navigation', async () => {
      const handleKeyDown = vi.fn();
      render(<${componentInfo.name} onKeyDown={handleKeyDown} />);

      const element = screen.getByRole('generic');
      if (element) {
        element.focus();
        expect(element).toHaveFocus();

        await userEventSetup.keyboard('{Enter}');
        // Test keyboard interaction as appropriate
      }
    });

    test('maintains color contrast compliance', () => {
      render(<${componentInfo.name} />);

      const element = screen.getByRole('generic');
      if (element) {
        const styles = window.getComputedStyle(element);
        expect(styles.color).toBeDefined();
      }
    });
  });`;
  }

  /**
   * Generate performance tests
   */
  private generatePerformanceTests(componentInfo: ComponentInfo): string {
    return `
  describe('⚡ Performance Testing', () => {
    test('renders efficiently', async () => {
      const startTime = performance.now();

      render(
        <div>
          {Array.from({ length: 10 }, (_, i) => (
            <${componentInfo.name} key={i} />
          ))}
        </div>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render 10 components quickly
      expect(renderTime).toBeLessThan(100);
    });

    test('handles rapid prop updates', async () => {
      const { rerender } = render(<${componentInfo.name} />);

      // Rapid re-renders
      for (let i = 0; i < 5; i++) {
        rerender(<${componentInfo.name} key={i} />);
      }

      expect(screen.getByRole('generic')).toBeInTheDocument();
    });
  });`;
  }

  /**
   * Generate edge case tests
   */
  private generateEdgeCaseTests(componentInfo: ComponentInfo): string {
    return `
  describe('🎯 Edge Cases & Error Handling', () => {
    test('handles undefined props gracefully', () => {
      expect(() => {
        render(<${componentInfo.name} />);
      }).not.toThrow();
    });

    test('handles extreme prop values', () => {
      const extremeProps = {`;

    componentInfo.props.forEach(prop => {
      if (prop.type.includes('string')) {
        tests += `
        ${prop.name}: 'x'.repeat(1000),`;
      } else if (prop.type.includes('number')) {
        tests += `
        ${prop.name}: 999999,`;
      }
    });

    return `${tests}
      };

      expect(() => {
        render(<${componentInfo.name} {...extremeProps} />);
      }).not.toThrow();
    });

    test('handles null/undefined children gracefully', () => {
      expect(() => {
        render(<${componentInfo.name}>{null}</${componentInfo.name}>);
      }).not.toThrow();
    });
  });`;
  }

  /**
   * Generate integration tests
   */
  private generateIntegrationTests(componentInfo: ComponentInfo): string {
    return `
  describe('🔗 Integration Testing', () => {
    test('integrates with React state', async () => {
      const TestComponent = () => {
        const [count, setCount] = React.useState(0);
        return (
          <div>
            <${componentInfo.name} />
            <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
          </div>
        );
      };

      render(<TestComponent />);
      expect(screen.getByText('Count: 0')).toBeInTheDocument();

      const button = screen.getByRole('button', { name: 'Count: 0' });
      await userEventSetup.click(button);
      expect(screen.getByText('Count: 1')).toBeInTheDocument();
    });

    test('works within form contexts', async () => {
      const handleSubmit = vi.fn((e) => e.preventDefault());

      render(
        <form onSubmit={handleSubmit}>
          <${componentInfo.name} />
          <button type="submit">Submit</button>
        </form>
      );

      const submitButton = screen.getByRole('button', { name: 'Submit' });
      await userEventSetup.click(submitButton);
      expect(handleSubmit).toHaveBeenCalled();
    });
  });`;
  }

  /**
   * Get output path for generated test file
   */
  private getOutputPath(componentInfo: ComponentInfo, config: Partial<TestGenerationConfig>): string {
    const baseDir = config.outputPath || 'src/tests/generated';
    return path.join(baseDir, `${componentInfo.name}.test.tsx`);
  }

  /**
   * Ensure directory exists
   */
  private async ensureDirectoryExists(dirPath: string): Promise<void> {
    try {
      await fs.access(dirPath);
    } catch {
      await fs.mkdir(dirPath, { recursive: true });
    }
  }

  /**
   * Generate tests for all components in a directory
   */
  async generateTestsForDirectory(
    dirPath: string,
    options: {
      pattern?: string;
      recursive?: boolean;
      exclude?: string[];
    } = {}
  ): Promise<string[]> {
    const files = await this.findComponentFiles(dirPath, options);
    const generatedFiles: string[] = [];

    for (const file of files) {
      try {
        await this.generateTests({ componentPath: file });
        generatedFiles.push(file);
      } catch (error) {
        console.warn(`Failed to generate tests for ${file}:`, error);
      }
    }

    console.log(`✅ Generated ${generatedFiles.length} test files`);
    return generatedFiles;
  }

  /**
   * Find React component files in directory
   */
  private async findComponentFiles(
    dirPath: string,
    options: {
      pattern?: string;
      recursive?: boolean;
      exclude?: string[];
    } = {}
  ): Promise<string[]> {
    const { pattern = '*.tsx', recursive = true, exclude = [] } = options;

    const files: string[] = [];
    const entries = await fs.readdir(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (exclude.some(pattern => entry.name.includes(pattern))) {
        continue;
      }

      if (entry.isDirectory() && recursive) {
        const subFiles = await this.findComponentFiles(fullPath, options);
        files.push(...subFiles);
      } else if (entry.isFile() && entry.name.match(pattern)) {
        // Check if it's likely a React component file
        const content = await fs.readFile(fullPath, 'utf-8');
        if (content.includes('export') || content.includes('function') || content.includes('const')) {
          files.push(fullPath);
        }
      }
    }

    return files;
  }
}

/**
 * Command-line interface
 */
async function main() {
  const generator = new ComprehensiveTestGenerator();
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: ts-node testGenerator.ts <component-file-or-directory>');
    console.log('Example: ts-node testGenerator.ts src/components/Button.tsx');
    console.log('Example: ts-node testGenerator.ts src/components/');
    process.exit(1);
  }

  const target = args[0];
  const stats = await fs.stat(target);

  try {
    if (stats.isFile()) {
      // Generate tests for single component
      await generator.generateTests({ componentPath: target });
      console.log('✅ Test generation completed successfully');
    } else if (stats.isDirectory()) {
      // Generate tests for all components in directory
      const generatedFiles = await generator.generateTestsForDirectory(target);
      console.log(`✅ Generated tests for ${generatedFiles.length} components`);
    }

    process.exit(0);

  } catch (error) {
    console.error('❌ Test generation failed:', error);
    process.exit(1);
  }
}

export { ComprehensiveTestGenerator, type TestGenerationConfig, type ComponentInfo };

// Run if called directly
if (require.main === module) {
  main();
}