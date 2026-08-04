/**
 * Caching Config Dashboard - Memoized Sub-Component
 */

import React, { useMemo } from 'react';
import { CacheSummary, CacheEntry } from './types';

interface CachingConfigDashboardProps {
  cacheSummary: CacheSummary | null;
  cacheEntries: CacheEntry[];
  loading?: boolean;
}

function getGradeColor(grade: string): string {
  const gradeNum = grade.replace(/[^A-Z]/g, '');
  if (gradeNum === 'A' || gradeNum === 'A+') return 'text-green-600';
  if (gradeNum === 'B') return 'text-blue-600';
  if (gradeNum === 'C') return 'text-yellow-600';
  return 'text-red-600';
}

function getGradeBgColor(grade: string): string {
  const gradeNum = grade.replace(/[^A-Z]/g, '');
  if (gradeNum === 'A' || gradeNum === 'A+') return 'border-green-500';
  if (gradeNum === 'B') return 'border-blue-500';
  if (gradeNum === 'C') return 'border-yellow-500';
  return 'border-red-500';
}

export const CachingConfigDashboard = React.memo<CachingConfigDashboardProps>(({
  cacheSummary,
  cacheEntries,
  loading = false,
}) => {
  const lowHitRateEntries = useMemo(
    () => cacheEntries.filter(e => e.hit_rate < 50),
    [cacheEntries]
  );

  if (loading) {
    return <div className="animate-pulse"><div className="h-64 bg-gray-200 rounded-lg" /></div>;
  }

  if (!cacheSummary) {
    return <div className="text-center py-12 text-gray-500">No cache data available</div>;
  }

  return (
    <div className="space-y-6">
      {/* Cache Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cache Performance Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-4xl font-bold text-gray-900">{cacheSummary.total_entries}</p>
            <p className="text-sm text-gray-600 mt-1">Total Entries</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-green-600">{cacheSummary.overall_hit_rate.toFixed(1)}%</p>
            <p className="text-sm text-gray-600 mt-1">Hit Rate</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">{cacheSummary.total_hits.toLocaleString()}</p>
            <p className="text-sm text-gray-600 mt-1">Total Hits</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-orange-600">{cacheSummary.memory_usage_mb.toFixed(1)}MB</p>
            <p className="text-sm text-gray-600 mt-1">Memory Usage</p>
          </div>
        </div>
      </div>

      {/* Low Hit Rate Entries */}
      {lowHitRateEntries.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              Low Hit Rate Entries ({lowHitRateEntries.length})
            </h3>
          </div>
          <div className="divide-y max-h-96 overflow-y-auto">
            {lowHitRateEntries.map((entry) => (
              <div key={entry.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{entry.key}</p>
                    <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Hit Rate</p>
                        <p className={`font-bold ${entry.hit_rate < 30 ? 'text-red-600' : 'text-yellow-600'}`}>
                          {entry.hit_rate.toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Hits/Misses</p>
                        <p className="font-medium">{entry.hit_count}/{entry.miss_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Size</p>
                        <p className="font-medium">{(entry.size_bytes / 1024).toFixed(1)}KB</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Cache Entries */}
      {cacheEntries.length > lowHitRateEntries.length && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">All Cache Entries</h3>
          </div>
          <div className="divide-y max-h-64 overflow-y-auto">
            {cacheEntries.slice(0, 20).map((entry) => (
              <div key={entry.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 truncate flex-1">{entry.key}</span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    entry.hit_rate >= 70 ? 'bg-green-100 text-green-800' :
                    entry.hit_rate >= 50 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {entry.hit_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

CachingConfigDashboard.displayName = 'CachingConfigDashboard';
export default CachingConfigDashboard;
