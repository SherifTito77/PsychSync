/**
 * 🎨 Visual Button State Test Runner
 *
 * Provides interactive visual testing for all button states and interactions.
 * Can be used in development and QA environments.
 */

import React, { useState } from 'react';
import Button, { BUTTON_VARIANTS, BUTTON_SIZES } from '../../components/common/Button';

interface StateTest {
  id: string;
  name: string;
  description: string;
  action?: () => void;
}

const ButtonStateVisualTester: React.FC = () => {
  const [currentVariant, setCurrentVariant] = useState(BUTTON_VARIANTS[0]);
  const [currentSize, setCurrentSize] = useState(BUTTON_SIZES[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);
  const [interactionLog, setInteractionLog] = useState<string[]>([]);

  const logInteraction = (message: string) => {
    setInteractionLog(prev => [`[${new Date().toLocaleTimeString()}] ${message}`, ...prev].slice(0, 10));
  };

  const simulateLoading = () => {
    setIsLoading(true);
    logInteraction('Loading started');
    setTimeout(() => {
      setIsLoading(false);
      logInteraction('Loading completed');
    }, 2000);
  };

  const handleClick = () => {
    if (!isLoading && !isDisabled) {
      logInteraction('Button clicked');
    }
  };

  const handleMouseEnter = () => {
    logInteraction('Mouse entered button (hover state)');
  };

  const handleMouseLeave = () => {
    logInteraction('Mouse left button');
  };

  const handleFocus = () => {
    logInteraction('Button focused (focus state)');
  };

  const handleBlur = () => {
    logInteraction('Button lost focus (blur state)');
  };

  const stateTests: StateTest[] = [
    {
      id: 'default',
      name: 'Default State',
      description: 'Normal button appearance'
    },
    {
      id: 'hover',
      name: 'Hover State',
      description: 'Mouse hover over button'
    },
    {
      id: 'focus',
      name: 'Focus State',
      description: 'Tab to focus button'
    },
    {
      id: 'active',
      name: 'Active State',
      description: 'Click and hold button'
    },
    {
      id: 'loading',
      name: 'Loading State',
      description: 'Button with loading spinner'
    },
    {
      id: 'disabled',
      name: 'Disabled State',
      description: 'Disabled button interaction'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🎨 Button State Visual Testing Suite
          </h1>
          <p className="text-gray-600 mb-6">
            Interactive testing environment for all button states and UI interactions
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">🎛️ Controls</h2>

              {/* Variant Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Variant
                </label>
                <select
                  value={currentVariant}
                  onChange={(e) => setCurrentVariant(e.target.value as any)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  {BUTTON_VARIANTS.map(variant => (
                    <option key={variant} value={variant}>
                      {variant.charAt(0).toUpperCase() + variant.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Size Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Size
                </label>
                <select
                  value={currentSize}
                  onChange={(e) => setCurrentSize(e.target.value as any)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  {BUTTON_SIZES.map(size => (
                    <option key={size} value={size}>
                      {size.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* State Toggles */}
              <div className="space-y-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isDisabled}
                    onChange={(e) => setIsDisabled(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">Disabled</span>
                </label>

                <Button
                  onClick={simulateLoading}
                  disabled={isLoading}
                  variant="outline"
                  size="small"
                  className="w-full"
                >
                  {isLoading ? 'Loading...' : 'Test Loading State'}
                </Button>
              </div>
            </div>

            {/* State Reference */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h3 className="text-lg font-semibold mb-3">📋 State Tests</h3>
              <div className="space-y-2">
                {stateTests.map(test => (
                  <div key={test.id} className="p-3 bg-gray-50 rounded border">
                    <div className="font-medium text-sm">{test.name}</div>
                    <div className="text-xs text-gray-600">{test.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Testing Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-xl font-semibold mb-6">🧪 Interactive Button Testing</h2>

              {/* Test Buttons Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Standard Test Button */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Standard Button
                  </h3>
                  <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center min-h-[100px]">
                    <Button
                      variant={currentVariant}
                      size={currentSize}
                      disabled={isDisabled}
                      loading={isLoading}
                      onClick={handleClick}
                      onMouseEnter={handleMouseEnter}
                      onMouseLeave={handleMouseLeave}
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                    >
                      Test Button
                    </Button>
                  </div>
                </div>

                {/* Button with Icon */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Button with Icon
                  </h3>
                  <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center min-h-[100px]">
                    <Button
                      variant={currentVariant}
                      size={currentSize}
                      disabled={isDisabled}
                      loading={isLoading}
                      icon={<span>🚀</span>}
                      onClick={handleClick}
                      onMouseEnter={handleMouseEnter}
                      onMouseLeave={handleMouseLeave}
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                    >
                      Icon Button
                    </Button>
                  </div>
                </div>

                {/* Long Text Button */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Long Text Button
                  </h3>
                  <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center min-h-[100px]">
                    <Button
                      variant={currentVariant}
                      size={currentSize}
                      disabled={isDisabled}
                      loading={isLoading}
                      onClick={handleClick}
                      onMouseEnter={handleMouseEnter}
                      onMouseLeave={handleMouseLeave}
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                    >
                      This is a very long button text for testing
                    </Button>
                  </div>
                </div>

                {/* Minimal Button */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Minimal Button
                  </h3>
                  <div className="p-4 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center min-h-[100px]">
                    <Button
                      variant={currentVariant}
                      size={currentSize}
                      disabled={isDisabled}
                      loading={isLoading}
                      onClick={handleClick}
                      onMouseEnter={handleMouseEnter}
                      onMouseLeave={handleMouseLeave}
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                    >
                      Go
                    </Button>
                  </div>
                </div>
              </div>

              {/* Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">🎯 Testing Instructions</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• <strong>Hover:</strong> Move mouse over buttons to test hover states</li>
                  <li>• <strong>Focus:</strong> Tab to buttons or click to test focus states</li>
                  <li>• <strong>Click:</strong> Click buttons to test active states</li>
                  <li>• <strong>Disabled:</strong> Toggle disabled state to test interactions</li>
                  <li>• <strong>Loading:</strong> Click "Test Loading State" to test loading state</li>
                  <li>• <strong>Keyboard:</strong> Use Tab, Shift+Tab, Enter, Space keys</li>
                </ul>
              </div>
            </div>

            {/* Interaction Log */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">📝 Interaction Log</h3>
              <div className="bg-gray-50 rounded border p-4 h-32 overflow-y-auto">
                {interactionLog.length === 0 ? (
                  <p className="text-gray-500 text-sm">No interactions yet...</p>
                ) : (
                  <div className="space-y-1">
                    {interactionLog.map((log, index) => (
                      <div key={index} className="text-xs font-mono text-gray-700">
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <button
                onClick={() => setInteractionLog([])}
                className="mt-3 text-sm text-blue-600 hover:text-blue-800"
              >
                Clear Log
              </button>
            </div>
          </div>
        </div>

        {/* Comprehensive State Display */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-6">🎭 Complete State Showcase</h2>
          <div className="space-y-8">
            {/* All Variants */}
            <div>
              <h3 className="text-lg font-medium mb-4">All Variants ({currentSize})</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                {BUTTON_VARIANTS.map(variant => (
                  <div key={variant} className="text-center">
                    <div className="text-xs text-gray-600 mb-2">{variant}</div>
                    <Button
                      variant={variant}
                      size={currentSize}
                      onClick={() => logInteraction(`Clicked ${variant} variant`)}
                    >
                      {variant}
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* All Sizes */}
            <div>
              <h3 className="text-lg font-medium mb-4">All Sizes ({currentVariant})</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {BUTTON_SIZES.map(size => (
                  <div key={size} className="text-center">
                    <div className="text-xs text-gray-600 mb-2">{size.toUpperCase()}</div>
                    <Button
                      variant={currentVariant}
                      size={size}
                      onClick={() => logInteraction(`Clicked ${size} size`)}
                    >
                      {size}
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* State Matrix */}
            <div>
              <h3 className="text-lg font-medium mb-4">State Matrix</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {BUTTON_VARIANTS.slice(0, 6).map(variant => (
                  <div key={variant} className="space-y-3">
                    <div className="text-sm font-medium text-gray-700">{variant}</div>

                    {/* Normal */}
                    <Button variant={variant} size="sm">
                      Normal
                    </Button>

                    {/* Hover (visual only) */}
                    <div className="relative">
                      <Button variant={variant} size="sm" className="opacity-75">
                        Hover (simulated)
                      </Button>
                    </div>

                    {/* Disabled */}
                    <Button variant={variant} size="sm" disabled>
                      Disabled
                    </Button>

                    {/* Loading */}
                    <Button variant={variant} size="sm" loading>
                      Loading
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ButtonStateVisualTester;