import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, Treemap, Cell, PieChart, Pie
} from 'recharts';
import {
  TrendingUp, TrendingDown, Activity, Heart, Users,
  Calendar, AlertTriangle, FileText, Download, Filter,
  Brain, Pill, Stethoscope, Clock, CheckCircle, XCircle
} from 'lucide-react';

const ClinicalDataVisualization = ({ patientData, populationData, timeRange = '30days' }) => {
  const [selectedView, setSelectedView] = useState('individual');
  const [selectedMetrics, setSelectedMetrics] = useState(['vital_signs', 'medication_adherence']);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [clinicalAlerts, setClinicalAlerts] = useState([]);

  const metricConfig = {
    vital_signs: {
      label: 'Vital Signs',
      color: '#ef4444',
      icon: Heart,
      submetrics: ['blood_pressure', 'heart_rate', 'temperature', 'oxygen_saturation']
    },
    medication_adherence: {
      label: 'Medication Adherence',
      color: '#3b82f6',
      icon: Pill,
      submetrics: ['daily_adherence', 'missed_doses', 'on_time_percentage']
    },
    symptom_tracking: {
      label: 'Symptom Tracking',
      color: '#f59e0b',
      icon: Activity,
      submetrics: ['pain_level', 'fatigue', 'nausea', 'anxiety']
    },
    lab_results: {
      label: 'Lab Results',
      color: '#10b981',
      icon: FileText,
      submetrics: ['glucose', 'cholesterol', 'hba1c', 'kidney_function']
    },
    mental_health: {
      label: 'Mental Health',
      color: '#8b5cf6',
      icon: Brain,
      submetrics: ['mood_score', 'anxiety_level', 'sleep_quality', 'stress_level']
    },
    activity_levels: {
      label: 'Activity Levels',
      color: '#06b6d4',
      icon: Activity,
      submetrics: ['steps', 'exercise_minutes', 'active_calories', 'sedentary_time']
    }
  };

  useEffect(() => {
    generateClinicalAlerts();
  }, [patientData]);

  const generateClinicalAlerts = () => {
    const alerts = [];

    if (patientData) {
      // Blood pressure alerts
      if (patientData.bloodPressure?.systolic > 140) {
        alerts.push({
          id: 1,
          type: 'critical',
          title: 'High Blood Pressure',
          value: `${patientData.bloodPressure.systolic}/${patientData.bloodPressure.diastolic}`,
          threshold: '>140/90',
          recommendation: 'Consider medication adjustment',
          timestamp: new Date()
        });
      }

      // Medication adherence alerts
      if (patientData.medicationAdherence < 70) {
        alerts.push({
          id: 2,
          type: 'warning',
          title: 'Low Medication Adherence',
          value: `${patientData.medicationAdherence}%`,
          threshold: '<80%',
          recommendation: 'Patient counseling needed',
          timestamp: new Date()
        });
      }

      // Symptom severity alerts
      if (patientData.painLevel > 7) {
        alerts.push({
          id: 3,
          type: 'urgent',
          title: 'Severe Pain Reported',
          value: `${patientData.painLevel}/10`,
          threshold: '>7',
          recommendation: 'Immediate follow-up required',
          timestamp: new Date()
        });
      }
    }

    setClinicalAlerts(alerts);
  };

  const generateVitalSignsData = () => {
    if (!patientData?.vitalSignsHistory) return [];

    return patientData.vitalSignsHistory.map((entry, index) => ({
      date: new Date(entry.timestamp).toLocaleDateString(),
      systolic: entry.bloodPressure?.systolic || 120,
      diastolic: entry.bloodPressure?.diastolic || 80,
      heartRate: entry.heartRate || 72,
      temperature: entry.temperature ? (entry.temperature * 9/5) + 32 : 98.6,
      oxygenSat: entry.oxygenSaturation || 98
    }));
  };

  const generateMedicationAdherenceData = () => {
    if (!patientData?.medicationHistory) return [];

    return patientData.medicationHistory.map((entry, index) => ({
      date: new Date(entry.timestamp).toLocaleDateString(),
      adherence: entry.adherencePercentage || 85,
      missedDoses: entry.missedDoses || 0,
      onTimePercentage: entry.onTimePercentage || 75
    }));
  };

  const generatePopulationHealthData = () => {
    if (!populationData) return [];

    return [
      { category: 'Controlled', value: 45, fill: '#10b981' },
      { category: 'At Risk', value: 30, fill: '#f59e0b' },
      { category: 'Uncontrolled', value: 15, fill: '#ef4444' },
      { category: 'Lost to Follow-up', value: 10, fill: '#6b7280' }
    ];
  };

  const generateRiskStratificationData = () => {
    if (!populationData?.riskDistribution) return [];

    return Object.entries(populationData.riskDistribution).map(([risk, count]) => ({
      name: risk.charAt(0).toUpperCase() + risk.slice(1),
      value: count,
      fill: risk === 'low' ? '#10b981' : risk === 'medium' ? '#f59e0b' : '#ef4444'
    }));
  };

  const calculateTrend = (data, metric) => {
    if (data.length < 2) return { direction: 'stable', percentage: 0 };

    const recent = data.slice(-7).reduce((sum, d) => sum + d[metric], 0) / 7;
    const previous = data.slice(-14, -7).reduce((sum, d) => sum + d[metric], 0) / 7;

    const change = ((recent - previous) / previous) * 100;
    return {
      direction: change > 5 ? 'improving' : change < -5 ? 'declining' : 'stable',
      percentage: Math.abs(change).toFixed(1)
    };
  };

  const renderClinicalAlerts = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="space-y-4 mb-8"
    >
      <h3 className="text-lg font-semibold text-gray-900">Clinical Alerts</h3>
      {clinicalAlerts.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <p className="text-green-800">No clinical alerts at this time</p>
          </div>
        </div>
      ) : (
        clinicalAlerts.map((alert, index) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className={`border-l-4 rounded-lg p-4 ${
              alert.type === 'critical' ? 'bg-red-50 border-red-400' :
              alert.type === 'urgent' ? 'bg-orange-50 border-orange-400' :
              'bg-yellow-50 border-yellow-400'
            }`}
          >
            <div className="flex items-start space-x-3">
              <AlertTriangle className={`h-5 w-5 mt-0.5 ${
                alert.type === 'critical' ? 'text-red-600' :
                alert.type === 'urgent' ? 'text-orange-600' : 'text-yellow-600'
              }`} />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">{alert.title}</h4>
                  <span className="text-sm text-gray-500">
                    {alert.value} (Threshold: {alert.threshold})
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{alert.recommendation}</p>
                <p className="text-xs text-gray-500 mt-2">
                  {alert.timestamp.toLocaleString()}
                </p>
              </div>
            </div>
          </motion.div>
        ))
      )}
    </motion.div>
  );

  const renderVitalSignsChart = () => {
    const data = generateVitalSignsData();
    const systolicTrend = calculateTrend(data, 'systolic');

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Vital Signs Trends</h3>
            <div className="flex items-center space-x-2 mt-1">
              {systolicTrend.direction === 'improving' ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : systolicTrend.direction === 'declining' ? (
                <TrendingDown className="h-4 w-4 text-red-600" />
              ) : (
                <Activity className="h-4 w-4 text-gray-600" />
              )}
              <span className={`text-sm font-medium ${
                systolicTrend.direction === 'improving' ? 'text-green-600' :
                systolicTrend.direction === 'declining' ? 'text-red-600' : 'text-gray-600'
              }`}>
                {systolicTrend.direction} ({systolicTrend.percentage}%)
              </span>
            </div>
          </div>
          <select className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
            <option value="bp">Blood Pressure</option>
            <option value="hr">Heart Rate</option>
            <option value="temp">Temperature</option>
            <option value="o2">Oxygen Saturation</option>
          </select>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
            <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Line
              type="monotone"
              dataKey="systolic"
              stroke="#ef4444"
              strokeWidth={2}
              name="Systolic BP"
              dot={{ fill: '#ef4444', r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="diastolic"
              stroke="#f59e0b"
              strokeWidth={2}
              name="Diastolic BP"
              dot={{ fill: '#f59e0b', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    );
  };

  const renderMedicationAdherenceChart = () => {
    const data = generateMedicationAdherenceData();

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Medication Adherence</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Daily Adherence Rate</h4>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="adherence"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Adherence Summary</h4>
            <div className="space-y-3">
              {[
                { label: 'Current Week', value: '82%', color: 'green' },
                { label: 'Previous Week', value: '78%', color: 'yellow' },
                { label: 'Monthly Average', value: '80%', color: 'blue' },
                { label: 'Missed Doses', value: '6', color: 'red' }
              ].map((stat) => (
                <div key={stat.label} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">{stat.label}</span>
                  <span className={`font-medium ${
                    stat.color === 'green' ? 'text-green-600' :
                    stat.color === 'yellow' ? 'text-yellow-600' :
                    stat.color === 'red' ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderPopulationHealth = () => {
    const populationData = generatePopulationHealthData();
    const riskData = generateRiskStratificationData();

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Population Health Overview</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Chronic Disease Control Status</h4>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={populationData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {populationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Risk Stratification</h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8">
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderClinicalMetrics = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8 }}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
    >
      {[
        {
          label: 'Average BP',
          value: patientData?.bloodPressure?.systolic ? `${patientData.bloodPressure.systolic}/${patientData.bloodPressure.diastolic}` : '120/80',
          unit: 'mmHg',
          icon: Heart,
          color: '#ef4444',
          status: 'normal'
        },
        {
          label: 'Medication Adherence',
          value: patientData?.medicationAdherence || 85,
          unit: '%',
          icon: Pill,
          color: '#3b82f6',
          status: 'warning'
        },
        {
          label: 'Last Check-in',
          value: '2',
          unit: 'days ago',
          icon: Calendar,
          color: '#10b981',
          status: 'normal'
        },
        {
          label: 'Risk Level',
          value: 'Medium',
          unit: '',
          icon: AlertTriangle,
          color: '#f59e0b',
          status: 'warning'
        }
      ].map((metric, index) => {
        const Icon = metric.icon;

        return (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.9 + index * 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${metric.color}20` }}>
                <Icon className="h-5 w-5" style={{ color: metric.color }} />
              </div>
              <span className={`w-2 h-2 rounded-full ${
                metric.status === 'normal' ? 'bg-green-500' :
                metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
            </div>

            <div className="text-2xl font-bold text-gray-900">
              {metric.value}
              {metric.unit && <span className="text-sm font-normal text-gray-500 ml-1">{metric.unit}</span>}
            </div>

            <div className="text-sm text-gray-600 mt-1">{metric.label}</div>
          </motion.div>
        );
      })}
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Clinical Data Visualization</h1>
              <p className="text-gray-600">Patient monitoring and population health analytics</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">View:</label>
                <select
                  value={selectedView}
                  onChange={(e) => setSelectedView(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="individual">Individual Patient</option>
                  <option value="population">Population</option>
                  <option value="comparison">Comparison</option>
                </select>
              </div>
              <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Download className="h-4 w-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {selectedView === 'individual' && (
          <>
            {renderClinicalAlerts()}
            {renderClinicalMetrics()}
            {renderVitalSignsChart()}
            {renderMedicationAdherenceChart()}
          </>
        )}

        {selectedView === 'population' && (
          <>
            {renderPopulationHealth()}
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Population Health Analytics</h3>
              <p className="text-gray-600">Comprehensive population health insights coming soon</p>
            </div>
          </>
        )}

        {selectedView === 'comparison' && (
          <div className="text-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Comparative Analysis</h3>
            <p className="text-gray-600">Multi-patient comparison tools coming soon</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClinicalDataVisualization;