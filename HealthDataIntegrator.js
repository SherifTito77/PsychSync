/**
 * Universal Health Data Integration Layer
 * Connects wellness platform with wearables, health devices, and health apps
 * Normalizes diverse data formats into unified health data model
 */

const fetch = require('node-fetch');
const crypto = require('crypto');

class HealthDataIntegrator {
  constructor() {
    this.adapters = new Map();
    this.dataBuffer = [];
    this.subscribers = [];
    this.dataModel = this.initializeDataModel();
    this.setupAdapters();
  }

  initializeDataModel() {
    return {
      // Activity metrics
      steps: { value: 0, unit: 'count', timestamp: null },
      caloriesBurned: { value: 0, unit: 'kcal', timestamp: null },
      activeMinutes: { value: 0, unit: 'minutes', timestamp: null },
      distance: { value: 0, unit: 'km', timestamp: null },

      // Heart metrics
      heartRate: { value: 0, unit: 'bpm', timestamp: null },
      restingHeartRate: { value: 0, unit: 'bpm', timestamp: null },
      heartRateVariability: { value: 0, unit: 'ms', timestamp: null },
      bloodOxygen: { value: 0, unit: '%', timestamp: null },

      // Sleep metrics
      sleepDuration: { value: 0, unit: 'hours', timestamp: null },
      sleepEfficiency: { value: 0, unit: '%', timestamp: null },
      sleepStages: { deep: 0, light: 0, rem: 0, awake: 0, unit: 'minutes' },
      sleepQuality: { value: 0, unit: 'score', timestamp: null },

      // Stress and recovery
      stressLevel: { value: 0, unit: 'score', timestamp: null },
      recoveryScore: { value: 0, unit: 'score', timestamp: null },
      bodyBattery: { value: 0, unit: '%', timestamp: null },

      // Physical metrics
      weight: { value: 0, unit: 'kg', timestamp: null },
      bodyFat: { value: 0, unit: '%', timestamp: null },
      muscleMass: { value: 0, unit: 'kg', timestamp: null },
      hydration: { value: 0, unit: '%', timestamp: null },

      // Blood metrics (for compatible devices)
      systolicBP: { value: 0, unit: 'mmHg', timestamp: null },
      diastolicBP: { value: 0, unit: 'mmHg', timestamp: null },
      bloodGlucose: { value: 0, unit: 'mg/dL', timestamp: null },

      // Exercise metrics
      workouts: [],
      exerciseMinutes: { value: 0, unit: 'minutes', timestamp: null },
      workoutIntensity: { value: 0, unit: 'score', timestamp: null },

      // Mindfulness metrics
      mindfulnessMinutes: { value: 0, unit: 'minutes', timestamp: null },
      meditationSessions: [],

      // Nutrition (where available)
      waterIntake: { value: 0, unit: 'ml', timestamp: null },
      nutritionLogs: [],

      // Metadata
      lastSync: null,
      dataSources: [],
      qualityScore: 0
    };
  }

  setupAdapters() {
    // Apple Health / HealthKit
    this.adapters.set('apple_health', new AppleHealthAdapter());

    // Google Fit
    this.adapters.set('google_fit', new GoogleFitAdapter());

    // Fitbit
    this.adapters.set('fitbit', new FitbitAdapter());

    // Garmin
    this.adapters.set('garmin', new GarminAdapter());

    // Oura Ring
    this.adapters.set('oura', new OuraAdapter());

    // Whoop
    this.adapters.set('whoop', new WhoopAdapter());

    // Polar
    this.adapters.set('polar', new PolarAdapter());

    // Withings
    this.adapters.set('withings', new WithingsAdapter());

    // Generic Bluetooth LE devices
    this.adapters.set('bluetooth_le', new BluetoothLEAdapter());

    // IoT Health Sensors
    this.adapters.set('iot_sensors', new IoTHealthAdapter());
  }

  async connectDevice(deviceType, credentials) {
    try {
      const adapter = this.adapters.get(deviceType);
      if (!adapter) {
        throw new Error(`Unsupported device type: ${deviceType}`);
      }

      const connection = await adapter.connect(credentials);
      console.log(`✅ Connected to ${deviceType}`);

      // Start data sync
      this.startDataSync(deviceType, connection);

      return {
        success: true,
        deviceType,
        connectionId: connection.id,
        capabilities: adapter.getCapabilities()
      };
    } catch (error) {
      console.error(`❌ Failed to connect to ${deviceType}:`, error.message);
      return {
        success: false,
        deviceType,
        error: error.message
      };
    }
  }

  async startDataSync(deviceType, connection) {
    const adapter = this.adapters.get(deviceType);

    // Real-time data streaming
    if (adapter.supportsRealTime()) {
      adapter.onDataUpdate((data) => {
        this.processIncomingData(deviceType, data);
      });
    }

    // Periodic sync for historical data
    setInterval(async () => {
      try {
        const historicalData = await adapter.getHistoricalData(connection.lastSync);
        this.processIncomingData(deviceType, historicalData);
        connection.lastSync = new Date();
      } catch (error) {
        console.error(`Sync failed for ${deviceType}:`, error.message);
      }
    }, adapter.getSyncInterval());
  }

  processIncomingData(deviceType, rawData) {
    try {
      // Normalize data to universal format
      const normalizedData = this.normalizeData(deviceType, rawData);

      // Validate data quality
      const validation = this.validateData(normalizedData);
      if (!validation.isValid) {
        console.warn(`Invalid data from ${deviceType}:`, validation.errors);
        return;
      }

      // Add to buffer
      this.dataBuffer.push({
        ...normalizedData,
        source: deviceType,
        timestamp: new Date(),
        id: crypto.randomUUID()
      });

      // Notify subscribers
      this.notifySubscribers(normalizedData);

      // Update aggregated metrics
      this.updateAggregatedMetrics();

      console.log(`📊 Processed data from ${deviceType}`);
    } catch (error) {
      console.error(`Error processing data from ${deviceType}:`, error.message);
    }
  }

  normalizeData(deviceType, rawData) {
    const adapter = this.adapters.get(deviceType);
    return adapter.normalizeData(rawData);
  }

  validateData(data) {
    const errors = [];

    // Check for reasonable ranges
    if (data.heartRate?.value > 220 || data.heartRate?.value < 30) {
      errors.push('Heart rate out of reasonable range');
    }

    if (data.steps?.value < 0) {
      errors.push('Negative step count');
    }

    if (data.sleepDuration?.value > 24) {
      errors.push('Sleep duration exceeds 24 hours');
    }

    // Check timestamp validity
    if (data.timestamp && isNaN(new Date(data.timestamp).getTime())) {
      errors.push('Invalid timestamp');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  updateAggregatedMetrics() {
    // Aggregate data from all sources for unified view
    const recent = this.getRecentData(24); // Last 24 hours

    this.dataModel.lastSync = new Date();
    this.dataModel.dataSources = [...new Set(recent.map(d => d.source))];

    // Calculate quality score based on data completeness
    const completeness = this.calculateDataCompleteness(recent);
    const consistency = this.calculateDataConsistency(recent);
    this.dataModel.qualityScore = Math.round((completeness + consistency) / 2);
  }

  calculateDataCompleteness(data) {
    const expectedMetrics = [
      'steps', 'heartRate', 'sleep', 'activeMinutes'
    ];

    const availableMetrics = expectedMetrics.filter(metric =>
      data.some(d => d[metric] !== undefined)
    );

    return (availableMetrics.length / expectedMetrics.length) * 100;
  }

  calculateDataConsistency(data) {
    // Check for consistent reporting intervals and reasonable variations
    if (data.length < 2) return 100;

    const intervals = [];
    for (let i = 1; i < data.length; i++) {
      const interval = new Date(data[i].timestamp) - new Date(data[i-1].timestamp);
      intervals.push(interval);
    }

    const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
    const variance = intervals.reduce((sum, interval) =>
      sum + Math.pow(interval - avgInterval, 2), 0
    ) / intervals.length;

    // Lower variance = higher consistency
    return Math.max(0, 100 - Math.sqrt(variance) / 1000);
  }

  subscribe(callback) {
    this.subscribers.push(callback);
  }

  notifySubscribers(data) {
    this.subscribers.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Subscriber callback error:', error.message);
      }
    });
  }

  getHealthInsights() {
    const recentData = this.getRecentData(7 * 24); // Last week
    return this.generateInsights(recentData);
  }

  generateInsights(data) {
    const insights = [];

    // Activity insights
    const avgSteps = data.reduce((sum, d) => sum + (d.steps?.value || 0), 0) / data.length;
    if (avgSteps < 5000) {
      insights.push({
        type: 'activity',
        level: 'warning',
        title: 'Low Activity Level',
        message: `Your average daily steps are ${Math.round(avgSteps)}. Consider increasing activity.`,
        recommendation: 'Aim for at least 7,000 steps per day for better health.'
      });
    }

    // Sleep insights
    const avgSleep = data.reduce((sum, d) => sum + (d.sleepDuration?.value || 0), 0) / data.length;
    if (avgSleep < 7) {
      insights.push({
        type: 'sleep',
        level: 'warning',
        title: 'Insufficient Sleep',
        message: `You're averaging ${avgSleep.toFixed(1)} hours of sleep per night.`,
        recommendation: 'Aim for 7-9 hours of sleep for optimal recovery.'
      });
    }

    // Heart rate insights
    const restingHR = data.map(d => d.restingHeartRate?.value).filter(v => v);
    if (restingHR.length > 0) {
      const avgRHR = restingHR.reduce((a, b) => a + b, 0) / restingHR.length;
      if (avgRHR > 80) {
        insights.push({
          type: 'cardio',
          level: 'info',
          title: 'Elevated Resting Heart Rate',
          message: `Your average resting heart rate is ${Math.round(avgRHR)} bpm.`,
          recommendation: 'Consider stress management and regular exercise to lower resting heart rate.'
        });
      }
    }

    return insights;
  }

  getRecentData(hours = 24) {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    return this.dataBuffer.filter(d => new Date(d.timestamp) >= cutoff);
  }

  getCurrentHealthData() {
    return this.dataModel;
  }

  getDeviceConnections() {
    return Array.from(this.adapters.entries()).map(([type, adapter]) => ({
      type,
      name: adapter.getDeviceName(),
      connected: adapter.isConnected(),
      capabilities: adapter.getCapabilities(),
      lastSync: adapter.getLastSync()
    }));
  }

  disconnectDevice(deviceType) {
    const adapter = this.adapters.get(deviceType);
    if (adapter) {
      adapter.disconnect();
      console.log(`🔌 Disconnected from ${deviceType}`);
    }
  }

  exportHealthData(format = 'json') {
    const data = {
      summary: this.getCurrentHealthData(),
      insights: this.getHealthInsights(),
      connections: this.getDeviceConnections(),
      exportDate: new Date().toISOString()
    };

    switch (format.toLowerCase()) {
      case 'json':
        return JSON.stringify(data, null, 2);
      case 'csv':
        return this.convertToCSV(data);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  convertToCSV(data) {
    // Convert health data to CSV format
    const headers = ['timestamp', 'metric', 'value', 'unit', 'source'];
    const rows = [headers.join(',')];

    this.dataBuffer.forEach(entry => {
      Object.entries(entry).forEach(([metric, data]) => {
        if (data && typeof data === 'object' && data.value !== undefined) {
          rows.push([
            entry.timestamp,
            metric,
            data.value,
            data.unit,
            entry.source
          ].join(','));
        }
      });
    });

    return rows.join('\n');
  }
}

// Device Adapters

class AppleHealthAdapter {
  constructor() {
    this.connected = false;
    this.lastSync = null;
  }

  async connect(credentials) {
    // Apple HealthKit integration (iOS only in real implementation)
    this.connected = true;
    return { id: 'apple_health_' + Date.now() };
  }

  supportsRealTime() { return true; }
  getSyncInterval() { return 5 * 60 * 1000; } // 5 minutes
  isConnected() { return this.connected; }
  getDeviceName() { return 'Apple Health'; }
  getCapabilities() { return ['heart_rate', 'steps', 'sleep', 'workouts']; }
  getLastSync() { return this.lastSync; }

  async getHistoricalData(since) {
    // Mock implementation
    return {
      heartRate: { value: 72 + Math.random() * 20, unit: 'bpm' },
      steps: { value: Math.floor(Math.random() * 15000), unit: 'count' },
      sleepDuration: { value: 7 + Math.random() * 2, unit: 'hours' }
    };
  }

  normalizeData(rawData) {
    return rawData;
  }

  onDataUpdate(callback) {
    // Set up real-time data listener
  }

  disconnect() {
    this.connected = false;
  }
}

class FitbitAdapter {
  constructor() {
    this.connected = false;
    this.lastSync = null;
    this.apiKey = null;
  }

  async connect(credentials) {
    this.apiKey = credentials.apiKey;
    this.connected = true;
    return { id: 'fitbit_' + Date.now() };
  }

  supportsRealTime() { return true; }
  getSyncInterval() { return 10 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Fitbit'; }
  getCapabilities() { return ['steps', 'heart_rate', 'sleep', 'calories', 'floors']; }
  getLastSync() { return this.lastSync; }

  async getHistoricalData(since) {
    // Fitbit API integration
    return {
      steps: { value: Math.floor(Math.random() * 12000), unit: 'count' },
      heartRate: { value: 68 + Math.random() * 25, unit: 'bpm' },
      caloriesBurned: { value: Math.floor(Math.random() * 500), unit: 'kcal' },
      sleepEfficiency: { value: 85 + Math.random() * 10, unit: '%' }
    };
  }

  normalizeData(rawData) {
    return rawData;
  }

  onDataUpdate(callback) {
    // Fitbit webhook listener
  }

  disconnect() {
    this.connected = false;
  }
}

class GarminAdapter {
  constructor() {
    this.connected = false;
    this.lastSync = null;
  }

  async connect(credentials) {
    this.connected = true;
    return { id: 'garmin_' + Date.now() };
  }

  supportsRealTime() { return true; }
  getSyncInterval() { return 15 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Garmin'; }
  getCapabilities() { return ['heart_rate', 'gps', 'workouts', 'recovery']; }
  getLastSync() { return this.lastSync; }

  async getHistoricalData(since) {
    return {
      heartRate: { value: 65 + Math.random() * 30, unit: 'bpm' },
      bodyBattery: { value: Math.floor(Math.random() * 100), unit: '%' },
      workouts: [
        { type: 'running', duration: 30, calories: 300 }
      ]
    };
  }

  normalizeData(rawData) {
    return rawData;
  }

  onDataUpdate(callback) {
    // Garmin Connect API listener
  }

  disconnect() {
    this.connected = false;
  }
}

// Additional adapters would follow the same pattern...
class OuraAdapter {
  async connect(credentials) { this.connected = true; return { id: 'oura_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 30 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Oura Ring'; }
  getCapabilities() { return ['sleep', 'readiness', 'activity', 'hrv']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

class WhoopAdapter {
  async connect(credentials) { this.connected = true; return { id: 'whoop_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 5 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Whoop'; }
  getCapabilities() { return ['recovery', 'strain', 'sleep', 'hrv']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

class PolarAdapter {
  async connect(credentials) { this.connected = true; return { id: 'polar_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 10 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Polar'; }
  getCapabilities() { return ['heart_rate', 'workouts', 'sleep']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

class WithingsAdapter {
  async connect(credentials) { this.connected = true; return { id: 'withings_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 20 * 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'Withings'; }
  getCapabilities() { return ['weight', 'body_composition', 'blood_pressure', 'sleep']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

class BluetoothLEAdapter {
  async connect(credentials) { this.connected = true; return { id: 'ble_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 1000; } // Very frequent for real-time sensors
  isConnected() { return this.connected; }
  getDeviceName() { return 'Bluetooth LE Sensor'; }
  getCapabilities() { return ['heart_rate', 'temperature', 'glucose']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

class IoTHealthAdapter {
  async connect(credentials) { this.connected = true; return { id: 'iot_' + Date.now() }; }
  supportsRealTime() { return true; }
  getSyncInterval() { return 60 * 1000; }
  isConnected() { return this.connected; }
  getDeviceName() { return 'IoT Health Sensors'; }
  getCapabilities() { return ['air_quality', 'temperature', 'humidity', 'motion']; }
  getLastSync() { return this.lastSync; }
  async getHistoricalData(since) { return {}; }
  normalizeData(rawData) { return rawData; }
  onDataUpdate(callback) {}
  disconnect() { this.connected = false; }
}

module.exports = HealthDataIntegrator;