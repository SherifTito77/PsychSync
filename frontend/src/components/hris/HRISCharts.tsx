// HRISCharts.tsx - Interactive Chart Components for HRIS Analytics
import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Color palette
const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6'];

// Big Five Personality Radar Chart
export const BigFiveRadarChart: React.FC<{ data: Record<string, number>; name?: string }> = ({ data, name }) => {
  const chartData = [
    { trait: 'Openness', value: data.openness || 0, fullMark: 100 },
    { trait: 'Conscientiousness', value: data.conscientiousness || 0, fullMark: 100 },
    { trait: 'Extraversion', value: data.extraversion || 0, fullMark: 100 },
    { trait: 'Agreeableness', value: data.agreeableness || 0, fullMark: 100 },
    { trait: 'Neuroticism', value: data.neuroticism || 0, fullMark: 100 }
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={chartData}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="trait" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 10 }} />
        <Radar
          name={name || 'Personality'}
          dataKey="value"
          stroke="#6366f1"
          fill="#6366f1"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
};

// Department Distribution Bar Chart
export const DepartmentBarChart: React.FC<{ data: Array<{ name: string; count: number; percentage: number }> }> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} angle={-45} textAnchor="end" height={80} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: number, name: string) => [value, 'Employees']}
        />
        <Legend />
        <Bar dataKey="count" name="Employees" fill="#6366f1" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

// Location Distribution Pie Chart
export const LocationPieChart: React.FC<{ data: Record<string, number> }> = ({ data }) => {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={true}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: number) => [value, 'Employees']}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

// Leadership Potential vs Team Fit Scatter Chart
export const LeadershipVsTeamFitChart: React.FC<{
  data: Array<{ name: string; leadership?: number; teamFit?: number }>;
}> = ({ data }) => {
  const chartData = data
    .filter(emp => emp.leadership !== undefined && emp.teamFit !== undefined)
    .map(emp => ({
      name: emp.name.split(' ')[0], // First name only
      leadership: emp.leadership,
      teamFit: emp.teamFit
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 100]} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Legend />
        <Bar dataKey="leadership" name="Leadership Potential" fill="#6366f1" radius={[4, 4, 0, 0]} />
        <Bar dataKey="teamFit" name="Team Fit Score" fill="#22c55e" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

// Assessment Completion Rate Trend
export const AssessmentTrendChart: React.FC<{
  data: Array<{ month: string; completed: number; total: number }>;
}> = ({ data }) => {
  const chartData = data.map(d => ({
    ...d,
    rate: ((d.completed / d.total) * 100).toFixed(1)
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 100]} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: any) => [value, '%']}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="rate"
          name="Completion Rate %"
          stroke="#6366f1"
          strokeWidth={3}
          dot={{ fill: '#6366f1', r: 5 }}
          activeDot={{ r: 7 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

// Trait Distribution Chart
export const TraitDistributionChart: React.FC<{ data: Record<string, number> }> = ({ data }) => {
  const chartData = Object.entries(data)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis dataKey="name" type="category" tick={{ fill: '#6b7280', fontSize: 12 }} width={90} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Bar dataKey="value" name="Employees" fill="#8b5cf6" radius={[0, 8, 8, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

// Emotional Intelligence Distribution
export const EQDistributionChart: React.FC<{ data: Array<{ name: string; eq?: number }> }> = ({ data }) => {
  const chartData = data
    .filter(emp => emp.eq !== undefined)
    .map(emp => ({
      name: emp.name.split(' ')[0],
      eq: emp.eq
    }))
    .sort((a, b) => b.eq - a.eq);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 100]} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: number) => [value, 'EQ Score']}
        />
        <Bar dataKey="eq" name="Emotional Intelligence" fill="#ec4899" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

// Department Analytics Comparison Chart
export const DepartmentComparisonChart: React.FC<{
  data: Array<{
    name: string;
    avg_leadership_potential?: number;
    avg_team_fit?: number;
    assessment_completion_rate?: number;
  }>;
}> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
        <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} domain={[0, 100]} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Legend />
        <Bar dataKey="avg_leadership_potential" name="Avg Leadership" fill="#6366f1" radius={[4, 4, 0, 0]} />
        <Bar dataKey="avg_team_fit" name="Avg Team Fit" fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="assessment_completion_rate" name="Completion Rate" fill="#f97316" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

// MBTI Distribution Pie Chart
export const MBTIDistributionChart: React.FC<{ data: Record<string, number> }> = ({ data }) => {
  const chartData = Object.entries(data).map(([type, count]) => ({ name: type, value: count }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => percent && percent * 100 > 5 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
          formatter={(value: number) => [value, 'Employees']}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};
