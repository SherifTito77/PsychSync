import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Flame, Zap, Snowflake, TrendingUp, TrendingDown } from 'lucide-react';

interface ConcentricZoneData {
  inner_zone: { name: string; risk_score: number; indicator_count: number; zone: string };
  middle_zone: { name: string; risk_score: number; health_score: number; zone: string };
  outer_zone: { name: string; risk_score: number; safety_score: number | null; zone: string };
}

interface ZoneMetricsProps {
  zones: ConcentricZoneData;
}

export const ZoneMetrics: React.FC<ZoneMetricsProps> = ({ zones }) => {
  const getZoneIcon = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return <Flame className="h-5 w-5 text-red-600" />;
      case 'yellow': return <Zap className="h-5 w-5 text-yellow-600" />;
      case 'green': return <Snowflake className="h-5 w-5 text-green-600" />;
      default: return null;
    }
  };

  const getZoneBadgeColor = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return 'bg-red-100 text-red-800';
      case 'yellow': return 'bg-yellow-100 text-yellow-800';
      case 'green': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Inner Zone - Individual Behaviors */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{zones.inner_zone.name}</CardTitle>
            {getZoneIcon(zones.inner_zone.zone)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Risk Score</p>
              <div className="flex items-center space-x-2">
                <p className="text-2xl font-bold">{(zones.inner_zone.risk_score * 100).toFixed(1)}%</p>
                <Badge className={getZoneBadgeColor(zones.inner_zone.zone)}>
                  {zones.inner_zone.zone.toUpperCase()}
                </Badge>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Indicators Detected</p>
              <p className="text-xl font-semibold">{zones.inner_zone.indicator_count}</p>
            </div>
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-600">
                {zones.inner_zone.risk_score >= 0.6
                  ? '⚠️ High number of toxic patterns detected at individual level'
                  : zones.inner_zone.risk_score >= 0.3
                  ? '⚡ Moderate behavioral issues detected'
                  : '✅ Healthy individual behaviors'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Middle Zone - Team Dynamics */}
      <Card className="border-l-4 border-l-purple-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{zones.middle_zone.name}</CardTitle>
            {getZoneIcon(zones.middle_zone.zone)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Risk Score</p>
              <div className="flex items-center space-x-2">
                <p className="text-2xl font-bold">{(zones.middle_zone.risk_score * 100).toFixed(1)}%</p>
                <Badge className={getZoneBadgeColor(zones.middle_zone.zone)}>
                  {zones.middle_zone.zone.toUpperCase()}
                </Badge>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Health Score</p>
              <div className="flex items-center space-x-2">
                <p className="text-xl font-semibold">{(zones.middle_zone.health_score * 100).toFixed(1)}%</p>
                {zones.middle_zone.health_score >= 0.7 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
              </div>
            </div>
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-600">
                {zones.middle_zone.risk_score >= 0.6
                  ? '⚠️ Critical team dynamics issues detected'
                  : zones.middle_zone.risk_score >= 0.3
                  ? '⚡ Team-level concerns emerging'
                  : '✅ Healthy team dynamics'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Outer Zone - Organizational Health */}
      <Card className="border-l-4 border-l-green-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{zones.outer_zone.name}</CardTitle>
            {getZoneIcon(zones.outer_zone.zone)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Risk Score</p>
              <div className="flex items-center space-x-2">
                <p className="text-2xl font-bold">{(zones.outer_zone.risk_score * 100).toFixed(1)}%</p>
                <Badge className={getZoneBadgeColor(zones.outer_zone.zone)}>
                  {zones.outer_zone.zone.toUpperCase()}
                </Badge>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-500">Safety Score</p>
              <p className="text-xl font-semibold">
                {zones.outer_zone.safety_score
                  ? `${(zones.outer_zone.safety_score * 100).toFixed(1)}%`
                  : 'N/A'}
              </p>
            </div>
            <div className="pt-2 border-t">
              <p className="text-xs text-gray-600">
                {zones.outer_zone.risk_score >= 0.6
                  ? '⚠️ Organizational health critical'
                  : zones.outer_zone.risk_score >= 0.3
                  ? '⚡ Organizational concerns detected'
                  : '✅ Healthy organizational culture'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
