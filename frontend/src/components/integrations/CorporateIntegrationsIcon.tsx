/**
 * Corporate Integrations Master Icon
 * The main icon representing the entire Corporate Integrations system
 */

import React from 'react';

/**
 * CorporateIntegrationsIcon - Master icon for the system
 *
 * Visual metaphor: Hub with connecting nodes representing data sources
 * Shape: Central circle with 6 orbiting satellites
 * Color: Gradient blue-to-purple (represents integration + intelligence)
 */
export const CorporateIntegrationsIcon: React.FC<{
  className?: string;
  size?: number;
}> = ({ className = "w-8 h-8", size = 32 }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Central hub - represents the orchestrator */}
    <circle cx="32" cy="32" r="8" fill="url(#gradient)" />

    {/* Inner circle - represents intelligence/AI */}
    <circle cx="32" cy="32" r="4" fill="white" opacity="0.9" />

    {/* Orbiting satellites - represents data sources */}
    {/* Top */}
    <circle cx="32" cy="14" r="5" fill="#3B82F6" opacity="0.8" />
    <line x1="32" y1="24" x2="32" y2="19" stroke="#3B82F6" strokeWidth="2" />

    {/* Top-right */}
    <circle cx="46" cy="20" r="5" fill="#10B981" opacity="0.8" />
    <line x1="38" y1="28" x2="43" y2="23" stroke="#10B981" strokeWidth="2" />

    {/* Bottom-right */}
    <circle cx="46" cy="44" r="5" fill="#8B5CF6" opacity="0.8" />
    <line x1="38" y1="36" x2="43" y2="41" stroke="#8B5CF6" strokeWidth="2" />

    {/* Bottom */}
    <circle cx="32" cy="50" r="5" fill="#F59E0B" opacity="0.8" />
    <line x1="32" y1="40" x2="32" y2="45" stroke="#F59E0B" strokeWidth="2" />

    {/* Bottom-left */}
    <circle cx="18" cy="44" r="5" fill="#EF4444" opacity="0.8" />
    <line x1="26" y1="36" x2="21" y2="41" stroke="#EF4444" strokeWidth="2" />

    {/* Top-left */}
    <circle cx="18" cy="20" r="5" fill="#EC4899" opacity="0.8" />
    <line x1="26" y1="28" x2="21" y2="23" stroke="#EC4899" strokeWidth="2" />

    {/* Gradient definition */}
    <defs>
      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3B82F6" />  {/* Blue */}
        <stop offset="100%" stopColor="#8B5CF6" /> {/* Purple */}
      </linearGradient>
    </defs>
  </svg>
);

/**
 * Simplified version - smaller, cleaner
 */
export const CorporateIntegrationsIconSimple: React.FC<{
  className?: string;
  size?: number;
}> = ({ className = "w-6 h-6", size = 24 }) => (
  <svg
    className={className}
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Central hub */}
    <circle cx="12" cy="12" r="4" fill="url(#gradient-simple)" />
    <circle cx="12" cy="12" r="2" fill="white" opacity="0.9" />

    {/* Satellites */}
    <circle cx="12" cy="5" r="2.5" fill="#3B82F6" opacity="0.8" />
    <circle cx="17" cy="8" r="2.5" fill="#10B981" opacity="0.8" />
    <circle cx="17" cy="16" r="2.5" fill="#8B5CF6" opacity="0.8" />
    <circle cx="12" cy="19" r="2.5" fill="#F59E0B" opacity="0.8" />
    <circle cx="7" cy="16" r="2.5" fill="#EF4444" opacity="0.8" />
    <circle cx="7" cy="8" r="2.5" fill="#EC4899" opacity="0.8" />

    {/* Connection lines */}
    <line x1="12" y1="8" x2="12" y2="5" stroke="#CBD5E1" strokeWidth="1" />
    <line x1="15" y1="10" x2="17" y2="8" stroke="#CBD5E1" strokeWidth="1" />
    <line x1="15" y1="14" x2="17" y2="16" stroke="#CBD5E1" strokeWidth="1" />
    <line x1="12" y1="16" x2="12" y2="19" stroke="#CBD5E1" strokeWidth="1" />
    <line x1="9" y1="14" x2="7" y2="16" stroke="#CBD5E1" strokeWidth="1" />
    <line x1="9" y1="10" x2="7" y2="8" stroke="#CBD5E1" strokeWidth="1" />

    <defs>
      <linearGradient id="gradient-simple" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3B82F6" />
        <stop offset="100%" stopColor="#8B5CF6" />
      </linearGradient>
    </defs>
  </svg>
);

/**
 * Logo version - for headers and branding
 */
export const CorporateIntegrationsLogo: React.FC<{
  className?: string;
  showText?: boolean;
}> = ({ className = "h-8", showText = true }) => (
  <div className={`flex items-center gap-2 ${className}`}>
    <CorporateIntegrationsIconSimple className="w-8 h-8" />
    {showText && (
      <div className="flex flex-col">
        <span className="text-lg font-bold text-gray-900 leading-tight">
          Corporate Integrations
        </span>
        <span className="text-xs text-gray-500 leading-tight">
          Behavioral Intelligence Platform
        </span>
      </div>
    )}
  </div>
);

/**
 * Badge icon - for notifications and counts
 */
export const CorporateIntegrationsBadge: React.FC<{
  count?: number;
  className?: string;
}> = ({ count = 0, className = "" }) => (
  <div className={`relative ${className}`}>
    <CorporateIntegrationsIconSimple className="w-6 h-6" />
    {count > 0 && (
      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
        {count > 9 ? '9+' : count}
      </span>
    )}
  </div>
);

export default CorporateIntegrationsIcon;
