// src/components/analytics/KPIDashboard.tsx
// Product KPI Dashboard for business intelligence
import React, { useState, useEffect, memo } from 'react';
import { kpiService } from '../../services/kpiService';
import {
  ProductKPIs,
  formatCurrency,
  formatPercentage,
  formatNumber,
  calculateTrend,
} from '../../types/analytics';

interface KPICardProps {
  title: string;
  value: string | number;
  previousValue?: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: string;
  unit?: string;
  size?: 'small' | 'medium' | 'large';
  goodTrend?: 'up' | 'down'; // Which direction is good for this metric?
}

const KPICard: React.FC<KPICardProps> = memo(({
  title,
  value,
  previousValue,
  change,
  trend,
  icon,
  unit = '',
  size = 'medium',
  goodTrend = 'up',
}) => {
  const trendColor = trend === goodTrend ? 'text-green-600' : trend === 'neutral' ? 'text-gray-500' : 'text-red-600';

  const sizeClasses = {
    small: 'p-4',
    medium: 'p-6',
    large: 'p-8',
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${sizeClasses[size]}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <span className="text-2xl">{icon}</span>}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className={`font-bold text-gray-900 ${size === 'large' ? 'text-4xl' : 'text-2xl'}`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
            {unit && <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>}
          </p>
          {previousValue && (
            <p className="text-sm text-gray-500 mt-1">
              Previous: {typeof previousValue === 'number' ? previousValue.toLocaleString() : previousValue}
            </p>
          )}
        </div>
        {change !== undefined && trend && (
          <div className={`text-sm font-semibold ${trendColor} flex items-center`}>
            {trend === 'up' && <span className="mr-1">↑</span>}
            {trend === 'down' && <span className="mr-1">↓</span>}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  );
});

interface KPISectionProps {
  title: string;
  children: React.ReactNode;
}

const KPISection: React.FC<KPISectionProps> = ({ title, children }) => (
  <div className="mb-8">
    <h2 className="text-xl font-bold text-gray-900 mb-4">{title}</h2>
    {children}
  </div>
);

const KPIDashboard: React.FC = () => {
  const [kpis, setKpis] = useState<ProductKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'30d' | '90d' | '12m'>('30d');

  useEffect(() => {
    loadKPIs();
  }, [selectedPeriod]);

  const loadKPIs = async () => {
    try {
      setLoading(true);
      const data = await kpiService.getCurrentKPIs();
      setKpis(data);
    } catch (err) {
      setError(err.message || 'Failed to load KPIs');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !kpis) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-800">Error loading KPIs: {error || 'Unknown error'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Product KPI Dashboard</h1>
          <p className="text-gray-600 mt-1">Track your product's performance and growth metrics</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="12m">Last 12 months</option>
          </select>
          <button
            onClick={loadKPIs}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Revenue Overview */}
      <KPISection title="💰 Revenue Overview">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="MRR"
            value={formatCurrency(kpis.mrr)}
            icon="💵"
            goodTrend="up"
          />
          <KPICard
            title="ARR"
            value={formatCurrency(kpis.arr)}
            icon="📈"
            goodTrend="up"
          />
          <KPICard
            title="ARPU"
            value={formatCurrency(kpis.arpu)}
            icon="👤"
            goodTrend="up"
          />
          <KPICard
            title="Churn Rate"
            value={kpis.churnRate}
            unit="%"
            icon="📉"
            goodTrend="down"
          />
        </div>
      </KPISection>

      {/* Acquisition & Activation */}
      <KPISection title="🎯 Acquisition & Activation">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Trial Signups"
            value={kpis.trialSignups}
            icon="📝"
            goodTrend="up"
          />
          <KPICard
            title="Trial → Paid"
            value={kpis.trialToPaidRate}
            unit="%"
            icon="⭐"
            goodTrend="up"
          />
          <KPICard
            title="First Assessment"
            value={kpis.firstAssessmentCompletion}
            unit="%"
            icon="✅"
            goodTrend="up"
          />
          <KPICard
            title="Time to First Value"
            value={kpis.timeToFirstValue}
            unit="min"
            icon="⚡"
            goodTrend="down"
          />
        </div>
      </KPISection>

      {/* Engagement */}
      <KPISection title="👥 Engagement Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Monthly Active Users"
            value={formatNumber(kpis.monthlyActiveUsers)}
            icon="🚀"
            goodTrend="up"
          />
          <KPICard
            title="Daily Active Users"
            value={formatNumber(kpis.dailyActiveUsers)}
            icon="📱"
            goodTrend="up"
          />
          <KPICard
            title="Assessments per User"
            value={kpis.assessmentsPerUser}
            icon="📊"
            goodTrend="up"
          />
          <KPICard
            title="Avg Session Duration"
            value={kpis.averageSessionDuration}
            unit="min"
            icon="⏱️"
            goodTrend="up"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <KPICard
            title="30-Day Retention"
            value={kpis.retentionRateDay30}
            unit="%"
            icon="🔄"
            goodTrend="up"
          />
          <KPICard
            title="90-Day Retention"
            value={kpis.retentionRateDay90}
            unit="%"
            icon="🔄"
            goodTrend="up"
          />
        </div>
      </KPISection>

      {/* Unit Economics */}
      <KPISection title="💼 Unit Economics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="LTV"
            value={formatCurrency(kpis.ltv)}
            icon="💎"
            goodTrend="up"
          />
          <KPICard
            title="CAC"
            value={formatCurrency(kpis.cac)}
            icon="🎯"
            goodTrend="down"
          />
          <KPICard
            title="LTV:CAC Ratio"
            value={kpis.ltvCacRatio.toFixed(2)}
            icon="📐"
            goodTrend="up"
          />
          <KPICard
            title="Avg Time to Purchase"
            value={kpis.averageTimeToPurchase}
            unit="days"
            icon="🗓️"
            goodTrend="down"
          />
        </div>
      </KPISection>

      {/* Feature Usage */}
      <KPISection title="🔧 Feature Adoption">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard
            title="Personality Assessments"
            value={kpis.featureUsage.personalityAssessments.usagePercentage}
            unit="%"
            icon="🧠"
            goodTrend="up"
          />
          <KPICard
            title="Team Analytics"
            value={kpis.featureUsage.teamAnalytics.usagePercentage}
            unit="%"
            icon="📊"
            goodTrend="up"
          />
          <KPICard
            title="Clinical Tools"
            value={kpis.featureUsage.clinicalTools.usagePercentage}
            unit="%"
            icon="🏥"
            goodTrend="up"
          />
          <KPICard
            title="Predictive Analytics"
            value={kpis.featureUsage.predictiveAnalytics.usagePercentage}
            unit="%"
            icon="🤖"
            goodTrend="up"
          />
          <KPICard
            title="Benchmarking"
            value={kpis.featureUsage.benchmarking.usagePercentage}
            unit="%"
            icon="📈"
            goodTrend="up"
          />
          <KPICard
            title="Team Collaboration"
            value={kpis.teamCollaborationRate}
            unit="%"
            icon="🤝"
            goodTrend="up"
          />
        </div>
      </KPISection>

      {/* Team Metrics */}
      <KPISection title="👨‍👩‍👧‍👦 Team Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Total Teams"
            value={kpis.totalTeams}
            icon="👥"
            goodTrend="up"
          />
          <KPICard
            title="Active Teams"
            value={kpis.activeTeams}
            icon="✅"
            goodTrend="up"
          />
          <KPICard
            title="Avg Team Size"
            value={kpis.averageTeamSize}
            icon="👤"
            goodTrend="up"
          />
          <KPICard
            title="Team Conversion Rate"
            value={kpis.teamConversionRate}
            unit="%"
            icon="⭐"
            goodTrend="up"
          />
        </div>
      </KPISection>

      {/* Assessment Completion Rates */}
      <KPISection title="📝 Assessment Completion Rates">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard
            title="PHQ-9 (Depression)"
            value={kpis.assessmentCompletionRates.phq9}
            unit="%"
            icon="💙"
            goodTrend="up"
          />
          <KPICard
            title="GAD-7 (Anxiety)"
            value={kpis.assessmentCompletionRates.gad7}
            unit="%"
            icon="💛"
            goodTrend="up"
          />
          <KPICard
            title="Big Five"
            value={kpis.assessmentCompletionRates.bigFive}
            unit="%"
            icon="🌟"
            goodTrend="up"
          />
          <KPICard
            title="MBTI"
            value={kpis.assessmentCompletionRates.mbti}
            unit="%"
            icon="🎭"
            goodTrend="up"
          />
          <KPICard
            title="Enneagram"
            value={kpis.assessmentCompletionRates.enneagram}
            unit="%"
            icon="🔢"
            goodTrend="up"
          />
          <KPICard
            title="Overall"
            value={kpis.assessmentCompletionRates.overall}
            unit="%"
            icon="📊"
            goodTrend="up"
          />
        </div>
      </KPISection>

      {/* Support Metrics */}
      <KPISection title="💬 Support Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <KPICard
            title="Open Tickets"
            value={kpis.supportTickets.openTickets}
            icon="🎫"
            goodTrend="down"
          />
          <KPICard
            title="Avg Response Time"
            value={kpis.supportTickets.averageResponseTime}
            unit="hrs"
            icon="⏱️"
            goodTrend="down"
          />
          <KPICard
            title="Customer Satisfaction"
            value={kpis.supportTickets.customerSatisfaction}
            unit="/5"
            icon="😊"
            goodTrend="up"
          />
          <KPICard
            title="Total Tickets"
            value={kpis.supportTickets.totalTickets}
            icon="📋"
            goodTrend="down"
          />
        </div>
      </KPISection>
    </div>
  );
};

KPIDashboard.displayName = 'KPIDashboard';

export default KPIDashboard;
