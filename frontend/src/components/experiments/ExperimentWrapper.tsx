// frontend/src/components/experiments/ExperimentWrapper.tsx
// Wrapper component for A/B testing UI elements
import React, { ReactElement, ReactNode } from 'react';
import { useExperiment } from '../../hooks/useExperiment';

interface ExperimentWrapperProps {
  name: string;
  children: ReactNode;
  loadingComponent?: ReactNode;
  renderAs?: 'div' | 'section' | 'span' | 'button';
  className?: string;
  onVariantAssigned?: (variant: string) => void;
}

interface VariantProps {
  name: string;
  children: ReactNode;
}

/**
 * ExperimentWrapper Component
 *
 * Automatically assigns users to variants and renders the appropriate child.
 *
 * @example
 * <ExperimentWrapper name="cta_button_color">
 *   <Variant name="control">
 *     <button className="bg-blue">Sign Up</button>
 *   </Variant>
 *   <Variant name="variant_a">
 *     <button className="bg-green">Sign Up</button>
 *   </Variant>
 * </ExperimentWrapper>
 */
export const ExperimentWrapper: React.FC<ExperimentWrapperProps> = ({
  name,
  children,
  loadingComponent = null,
  renderAs = 'div',
  className = '',
  onVariantAssigned
}) => {
  const { variant, isLoading } = useExperiment(name);

  // Call callback when variant is assigned
  React.useEffect(() => {
    if (variant && !isLoading && onVariantAssigned) {
      onVariantAssigned(variant);
    }
  }, [variant, isLoading, onVariantAssigned]);

  if (isLoading) {
    return <>{loadingComponent}</>;
  }

  // Find the matching variant to render
  const variantElements = React.Children.toArray(children);
  const matchingVariant = variantElements.find((child: any) => {
    return child?.props?.name === variant;
  });

  const Tag = renderAs as keyof JSX.IntrinsicElements;

  return (
    <Tag
      className={`ab-experiment-${name} ab-variant-${variant} ${className}`}
      data-variant={variant}
      data-experiment={name}
    >
      {matchingVariant || children}
    </Tag>
  );
};

/**
 * Variant Component
 *
 * Marker component for experiment variants.
 * The actual rendering logic is in ExperimentWrapper.
 */
export const Variant: React.FC<VariantProps> = ({ name, children }) => {
  // This component is just a marker – ExperimentWrapper handles the logic
  return <>{children}</>;
};

/**
 * Simple CTA Button Experiment Wrapper
 *
 * Convenience component for experimenting with CTA buttons.
 */
export const CTAButtonExperiment: React.FC<{
  experimentName: string;
  onClick: () => void;
  variants: Record<string, { className: string; text: string }>;
  loadingComponent?: ReactNode;
}> = ({ experimentName, onClick, variants, loadingComponent }) => {
  return (
    <ExperimentWrapper name={experimentName} loadingComponent={loadingComponent}>
      {Object.entries(variants).map(([variantName, config]) => (
        <Variant key={variantName} name={variantName}>
          <button
            onClick={onClick}
            className={config.className}
            data-variant={variantName}
          >
            {config.text}
          </button>
        </Variant>
      ))}
    </ExperimentWrapper>
  );
};

/**
 * Text Content Experiment Wrapper
 *
 * Convenience component for experimenting with text copy.
 */
export const TextExperiment: React.FC<{
  experimentName: string;
  variants: Record<string, string>;
  loadingComponent?: ReactNode;
  renderAs?: 'h1' | 'h2' | 'h3' | 'p' | 'span';
}> = ({ experimentName, variants, loadingComponent, renderAs = 'p' }) => {
  return (
    <ExperimentWrapper name={experimentName} loadingComponent={loadingComponent} renderAs={renderAs}>
      {Object.entries(variants).map(([variantName, text]) => (
        <Variant key={variantName} name={variantName}>
          {text}
        </Variant>
      ))}
    </ExperimentWrapper>
  );
};

/**
 * Layout Experiment Wrapper
 *
 * Convenience component for experimenting with page layouts.
 */
export const LayoutExperiment: React.FC<{
  experimentName: string;
  variants: Record<string, ReactNode>;
  loadingComponent?: ReactNode;
}> = ({ experimentName, variants, loadingComponent }) => {
  return (
    <ExperimentWrapper name={experimentName} loadingComponent={loadingComponent}>
      {Object.entries(variants).map(([variantName, component]) => (
        <Variant key={variantName} name={variantName}>
          {component}
        </Variant>
      ))}
    </ExperimentWrapper>
  );
};

export default ExperimentWrapper;
