import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ClinicalResourceCardProps {
  title: string;
  description: string;
  type: 'hotline' | 'website' | 'text' | 'emergency';
  contact?: string;
  website?: string;
  available247?: boolean;
  emergency?: boolean;
}

const ClinicalResourceCard: React.FC<ClinicalResourceCardProps> = ({
  title,
  description,
  type,
  contact,
  website,
  available247 = false,
  emergency = false,
}) => {
  const handleContactClick = () => {
    if (type === 'text' || contact?.includes('Text')) {
      // Handle text-based contact
      window.open('sms:741741&body=HOME', '_blank');
    } else if (contact) {
      // Handle phone call
      const phoneNumber = contact.replace(/[^\d]/g, '');
      window.open(`tel:${phoneNumber}`, '_blank');
    }
  };

  const handleWebsiteClick = () => {
    if (website) {
      window.open(website, '_blank', 'noopener,noreferrer');
    }
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'hotline':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
        );
      case 'text':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'website':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        );
      case 'emergency':
        return (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getCardClass = () => {
    if (emergency) return 'border-red-200 bg-red-50';
    if (type === 'emergency') return 'border-red-300 bg-red-50';
    return 'border-gray-200 hover:shadow-lg transition-shadow';
  };

  return (
    <Card className={`${getCardClass()}`}>
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              emergency ? 'bg-red-100 text-red-600' :
              type === 'emergency' ? 'bg-red-100 text-red-600' :
              'bg-blue-100 text-blue-600'
            }`}>
              {getTypeIcon()}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{title}</h3>
              <div className="flex items-center space-x-2 mt-1">
                {available247 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    24/7
                  </span>
                )}
                {emergency && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                    EMERGENCY
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-gray-600 mb-4">{description}</p>

        {/* Action Buttons */}
        <div className="space-y-2">
          {contact && (
            <Button
              onClick={handleContactClick}
              className={`w-full ${
                emergency || type === 'emergency' ? 'bg-red-600 hover:bg-red-700' : ''
              }`}
              variant={emergency || type === 'emergency' ? 'default' : 'outline'}
            >
              {type === 'text' || contact.includes('Text') ? 'Text Now' : `Call ${contact}`}
            </Button>
          )}
          {website && (
            <Button
              onClick={handleWebsiteClick}
              variant="outline"
              className="w-full"
            >
              Visit Website
            </Button>
          )}
        </div>

        {/* Emergency Note */}
        {emergency && (
          <div className="mt-4 p-3 bg-red-100 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Emergency:</strong> Call immediately if you or someone else is in danger.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ClinicalResourceCard;