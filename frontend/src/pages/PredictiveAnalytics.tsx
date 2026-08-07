import React, { useState, useEffect } from 'react';

import {
  Insights,
  ModelTraining,
  Assessment,
  TrendingUp,
  Settings,
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  CheckCircle,
  Error,
  Warning
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Tooltip,
  IconButton
} from '@mui/material';
import { XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart as RechartsBarChart, Bar } from 'recharts';

import api from '../services/api';

// Types for prediction data
interface ModelInfo {
  model_id: string;
  model_type: string;
  prediction_type: string;
  target_type: string;
  target_name: string;
  performance: {
    accuracy?: number;
    r2?: number;
    mse?: number;
    mae?: number;
    f1?: number;
    cv_scores?: number[];
    feature_importance?: Record<string, number>;
  };
  hyperparameters: Record<string, any>;
  training_date: string;
  cross_val_score?: number;
}

interface PredictionResult {
  prediction: number | string;
  confidence: number;
  prediction_interval?: [number, number];
  probabilities?: Record<string, number>;
  feature_contributions?: Record<string, number>;
  model_id: string;
  prediction_type: string;
  timestamp: string;
}

interface TrainingConfig {
  prediction_type: string;
  target_variable: string;
  team_ids?: string[];
  model_types?: string[];
  test_size: number;
  cv_folds: number;
  hyperparameter_tuning: boolean;
  feature_selection: boolean;
  min_data_quality: number;
}

const PredictiveAnalytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [predictionDialogOpen, setPredictionDialogOpen] = useState(false);
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({
    prediction_type: 'team_performance',
    target_variable: 'team_performance_score',
    test_size: 0.2,
    cv_folds: 5,
    hyperparameter_tuning: true,
    feature_selection: true,
    min_data_quality: 0.7
  });
  const [predictionConfig, setPredictionConfig] = useState({
    team_ids: [] as string[],
    include_confidence: true,
    include_feature_importance: true
  });
  const [dataQuality, setDataQuality] = useState<any>(null);
  const [clinicalScreenings, setClinicalScreenings] = useState<any>(null);
  const [trainingInProgress, setTrainingInProgress] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);

  // Load models on component mount
  useEffect(() => {
    loadModels();
    assessDataQuality();
    loadClinicalScreenings();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await api.get('/predictions/models');
      const data = response.data;

      // Defensive check for response structure
      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setModels(data.models);
          // Automatically select the first model if none selected
          if (data.models.length > 0 && !selectedModel) {
            setSelectedModel(data.models[0].model_id);
          }
        } else {
          setError(data.error_message || 'Failed to load models');
        }
      } else {
        // Handle cases where the response is not in the expected format
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err) {
      setError('Failed to connect to prediction service');
    } finally {
      setLoading(false);
    }
  };

  const assessDataQuality = async () => {
    try {
      const response = await api.get('/predictions/data/quality');
      const data = response.data;

      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setDataQuality(data.data_quality);
        } else {
          setError(data.error_message || 'Failed to assess data quality');
        }
      } else {
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err) {
      setError('Failed to assess data quality');
      console.error('Failed to assess data quality:', err);
    }
  };

  const loadClinicalScreenings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/predictions/clinical-screenings');
      const data = response.data;

      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setClinicalScreenings(data);
        } else {
          setError(data.error_message || 'Failed to load clinical screenings');
        }
      } else {
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err) {
      setError('Failed to load clinical screenings');
      console.error('Failed to load clinical screenings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModel = async () => {
    try {
      setTrainingInProgress(true);
      setTrainingProgress(0);
      setError(null);
      setSuccess(null);

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setTrainingProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response = await api.post('/predictions/train', trainingConfig);

      clearInterval(progressInterval);
      setTrainingProgress(100);

      const data = response.data;

      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setSuccess(`Model training completed successfully! Best model: ${data.model_comparison?.best_model_name}`);
          await loadModels();
        } else {
          setError(data.error_message || 'Model training failed');
        }
      } else {
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err) {
      setError('Failed to train model');
    } finally {
      setTrainingInProgress(false);
      setTrainingProgress(0);
    }
  };

  const handleMakePredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await api.post('/predictions/predict', {
        prediction_type: 'team_performance',
        entity_ids: predictionConfig.team_ids,
        model_id: selectedModel || undefined,
        include_confidence: predictionConfig.include_confidence,
        include_feature_importance: predictionConfig.include_feature_importance
      });

      const data = response.data;

      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setPredictions(data.predictions);
          setPredictionDialogOpen(false);
          setSuccess(`Generated ${data.predictions.length} predictions successfully`);
        } else {
          setError(data.error_message || 'Prediction failed');
        }
      } else {
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const errorMsg = detail?.message ||
                     (typeof detail === 'string' ? detail : null) ||
                     'Failed to make predictions';
      setError(errorMsg);
      console.error('Prediction error:', err.response?.data || err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!window.confirm('Are you sure you want to delete this model?')) {
      return;
    }

    try {
      const response = await api.delete(`/predictions/models/${modelId}`);
      const data = response.data;

      if (typeof data?.success !== 'undefined') {
        if (data.success) {
          setSuccess('Model deleted successfully');
          await loadModels();
        } else {
          setError(data.error_message || 'Failed to delete model');
        }
      } else {
        setError('Received an unexpected response from the server.');
        console.error('Unexpected response format:', data);
      }
    } catch (err) {
      setError('Failed to delete model');
    }
  };

  const getPerformanceColor = (score?: number) => {
    if (!score) {return 'default';}
    if (score >= 0.8) {return 'success';}
    if (score >= 0.6) {return 'warning';}
    return 'error';
  };

  const getPerformanceIcon = (score?: number) => {
    if (!score) {return <Error />;}
    if (score >= 0.8) {return <CheckCircle color="success" />;}
    if (score >= 0.6) {return <Warning color="warning" />;}
    return <Error color="error" />;
  };

  const renderModelPerformanceChart = (model: ModelInfo) => {
    const performanceData = Object.entries(model.performance)
      .filter(([key, value]) => typeof value === 'number' && key !== 'cv_scores')
      .map(([key, value]) => ({
        metric: key.replace(/_/g, ' ').toUpperCase(),
        value: Number((value as number).toFixed(3))
      }));

    return (
      <ResponsiveContainer width="100%" height={200}>
        <RechartsBarChart data={performanceData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="metric" />
          <YAxis />
          <RechartsTooltip />
          <Bar dataKey="value" fill="#8884d8" />
        </RechartsBarChart>
      </ResponsiveContainer>
    );
  };

  const renderFeatureImportanceChart = (featureImportance: Record<string, number>) => {
    const data = Object.entries(featureImportance)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([feature, importance]) => ({
        feature: feature.length > 15 ? `${feature.substring(0, 15)  }...` : feature,
        importance: Number(importance.toFixed(3))
      }));

    return (
      <ResponsiveContainer width="100%" height={200}>
        <RechartsBarChart data={data} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="feature" type="category" width={100} />
          <RechartsTooltip />
          <Bar dataKey="importance" fill="#82ca9d" />
        </RechartsBarChart>
      </ResponsiveContainer>
    );
  };

  const renderPredictionResults = () => {
    if (predictions.length === 0) {
      return (
        <Alert severity="info">
          No predictions available. Make predictions to see results here.
        </Alert>
      );
    }

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Entity ID</TableCell>
              <TableCell>Prediction</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Prediction Interval</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Timestamp</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {predictions.map((prediction, index) => (
              <TableRow key={index}>
                <TableCell>{`Team ${index + 1}`}</TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {typeof prediction.prediction === 'number'
                      ? prediction.prediction.toFixed(2)
                      : (prediction.prediction ?? 'N/A')}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={prediction.confidence !== null ? `${(prediction.confidence * 100).toFixed(1)}%` : 'N/A'}
                    color={prediction.confidence !== null && prediction.confidence > 0.8 ? 'success' : prediction.confidence !== null && prediction.confidence > 0.6 ? 'warning' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {prediction.prediction_interval && prediction.prediction_interval.length >= 2 ? (
                    <Typography variant="caption">
                      [{prediction.prediction_interval[0].toFixed(2)}, {prediction.prediction_interval[1].toFixed(2)}]
                    </Typography>
                  ) : '-'}
                </TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {prediction.model_id.substring(0, 20)}...
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {prediction.timestamp ? new Date(prediction.timestamp).toLocaleString() : 'N/A'}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Insights sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Predictive Analytics
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Data Quality Overview */}
      {dataQuality ? (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Quality Assessment
            </Typography>
            {dataQuality.total_rows !== undefined ? (
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {dataQuality.overall_score !== undefined && dataQuality.overall_score !== null
                        ? `${(dataQuality.overall_score * 100).toFixed(1)}%`
                        : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Overall Quality
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {dataQuality.total_rows !== undefined && dataQuality.total_rows !== null
                        ? dataQuality.total_rows.toLocaleString()
                        : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Data Points
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {dataQuality.total_features !== undefined && dataQuality.total_features !== null
                        ? dataQuality.total_features
                        : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Features
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, md: 3 }}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {dataQuality.completeness !== undefined && dataQuality.completeness !== null
                        ? `${(dataQuality.completeness * 100).toFixed(1)}%`
                        : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Completeness
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                No data quality assessment available. Please ensure you have completed assessments.
              </Alert>
            )}
            {dataQuality.total_rows !== undefined && dataQuality.overall_score !== undefined && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={dataQuality.overall_score * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      ) : !loading && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No data quality information available. Try refreshing the page or check your assessment data.
        </Alert>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Models" icon={<ModelTraining />} />
        <Tab label="Predictions" icon={<TrendingUp />} />
        <Tab label="Training" icon={<Settings />} />
      </Tabs>

      {/* Models Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Trained Models</Typography>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={loadModels}
              disabled={loading}
            >
              Refresh
            </Button>
          </Grid>

          {models.map((model) => (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={model.model_id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        {model.model_type.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip
                        label={model.prediction_type.replace('_', ' ')}
                        size="small"
                        color="primary"
                        sx={{ mb: 1 }}
                      />
                    </Box>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteModel(model.model_id)}
                    >
                      <Delete />
                    </IconButton>
                  </Box>

                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Target: {model.target_name}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getPerformanceIcon(model.performance.accuracy || model.performance.r2)}
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {model.performance.accuracy
                        ? `Accuracy: ${(model.performance.accuracy * 100).toFixed(1)}%`
                        : model.performance.r2
                        ? `R²: ${model.performance.r2.toFixed(3)}`
                        : 'No performance metrics'
                      }
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Performance Chart */}
                  {renderModelPerformanceChart(model)}

                  {model.performance.feature_importance && Object.keys(model.performance.feature_importance).length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Top Features
                      </Typography>
                      {renderFeatureImportanceChart(model.performance.feature_importance)}
                    </>
                  )}

                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="caption" color="textSecondary">
                      Trained: {model.training_date ? new Date(model.training_date).toLocaleDateString() : 'Unknown'}
                    </Typography>
                    <Button
                      size="small"
                      onClick={() => setSelectedModel(model.model_id)}
                      variant={selectedModel === model.model_id ? "contained" : "outlined"}
                    >
                      {selectedModel === model.model_id ? "Selected" : "Select"}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}

          {models.length === 0 && !loading && (
            <Grid size={{ xs: 12 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 6 }}>
                  <ModelTraining sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="textSecondary" gutterBottom>
                    No trained models found
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                    Train your first predictive model to get started
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<PlayArrow />}
                    onClick={() => setActiveTab(2)}
                  >
                    Train Model
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Predictions Tab */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Prediction Results</Typography>
            {!selectedModel ? (
              <Tooltip title="Please select a model from the Models tab first">
                <span>
                  <Button
                    variant="contained"
                    startIcon={<TrendingUp />}
                    disabled
                  >
                    Make Predictions
                  </Button>
                </span>
              </Tooltip>
            ) : (
              <Button
                variant="contained"
                startIcon={<TrendingUp />}
                onClick={() => setPredictionDialogOpen(true)}
              >
                Make Predictions
              </Button>
            )}
          </Grid>

          <Grid size={{ xs: 12 }}>
            {renderPredictionResults()}
          </Grid>
        </Grid>
      )}

      {/* Training Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Training Configuration
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                  Configure and train new predictive models using your assessment data
                </Typography>

                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Prediction Type</InputLabel>
                      <Select
                        value={trainingConfig.prediction_type}
                        onChange={(e) => setTrainingConfig({...trainingConfig, prediction_type: e.target.value})}
                      >
                        <MenuItem value="team_performance">Team Performance</MenuItem>
                        <MenuItem value="user_outcome">User Outcome</MenuItem>
                        <MenuItem value="assessment_completion">Assessment Completion</MenuItem>
                      </Select>
                    </FormControl>

                    <TextField
                      fullWidth
                      label="Target Variable"
                      value={trainingConfig.target_variable}
                      onChange={(e) => setTrainingConfig({...trainingConfig, target_variable: e.target.value})}
                      sx={{ mb: 2 }}
                      helperText="The variable you want to predict"
                    />

                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>Model Types</InputLabel>
                      <Select
                        multiple
                        value={trainingConfig.model_types || []}
                        onChange={(e) => setTrainingConfig({...trainingConfig, model_types: e.target.value as string[]})}
                        renderValue={(selected) => (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {(selected).map((value) => (
                              <Chip key={value} label={value} size="small" />
                            ))}
                          </Box>
                        )}
                      >
                        <MenuItem value="random_forest">Random Forest</MenuItem>
                        <MenuItem value="gradient_boosting">Gradient Boosting</MenuItem>
                        <MenuItem value="svm">Support Vector Machine</MenuItem>
                        <MenuItem value="neural_network">Neural Network</MenuItem>
                        <MenuItem value="linear_regression">Linear Regression</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Test Size"
                      value={trainingConfig.test_size}
                      onChange={(e) => setTrainingConfig({...trainingConfig, test_size: parseFloat(e.target.value)})}
                      inputProps={{ min: 0.1, max: 0.5, step: 0.1 }}
                      sx={{ mb: 2 }}
                      helperText="Proportion of data for testing (0.1-0.5)"
                    />

                    <TextField
                      fullWidth
                      type="number"
                      label="Cross-Validation Folds"
                      value={trainingConfig.cv_folds}
                      onChange={(e) => setTrainingConfig({...trainingConfig, cv_folds: parseInt(e.target.value)})}
                      inputProps={{ min: 2, max: 10, step: 1 }}
                      sx={{ mb: 2 }}
                      helperText="Number of CV folds for model evaluation"
                    />

                    <Box sx={{ mb: 2 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={trainingConfig.hyperparameter_tuning}
                            onChange={(e) => setTrainingConfig({...trainingConfig, hyperparameter_tuning: e.target.checked})}
                          />
                        }
                        label="Hyperparameter Tuning"
                      />
                      <FormControlLabel
                        control={
                          <Switch
                            checked={trainingConfig.feature_selection}
                            onChange={(e) => setTrainingConfig({...trainingConfig, feature_selection: e.target.checked})}
                          />
                        }
                        label="Feature Selection"
                      />
                    </Box>
                  </Grid>
                </Grid>

                {trainingInProgress && (
                  <Box sx={{ mt: 3, mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      Training Progress: {trainingProgress}%
                    </Typography>
                    <LinearProgress variant="determinate" value={trainingProgress} />
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    startIcon={trainingInProgress ? <Stop /> : <PlayArrow />}
                    onClick={handleTrainModel}
                    disabled={trainingInProgress}
                    size="large"
                  >
                    {trainingInProgress ? 'Training...' : 'Start Training'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Prediction Dialog */}
      <Dialog
        open={predictionDialogOpen}
        onClose={() => setPredictionDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        disableRestoreFocus // Prevents focus conflict with triggering button
      >
        <DialogTitle>Make Predictions</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select teams to predict performance for using the selected model.
          </Typography>

          <TextField
            fullWidth
            autoFocus
            label="Team IDs (comma-separated)"
            placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000"
            value={predictionConfig.team_ids.join(',')}
            onChange={(e) => setPredictionConfig({
              ...predictionConfig,
              team_ids: e.target.value.split(',').map(id => id.trim()).filter(id => id !== '')
            })}
            sx={{ mb: 2, mt: 1 }} // Added margin top to ensure visibility
            helperText="Enter team IDs (UUIDs) separated by commas"
          />

          <FormControlLabel
            control={
              <Switch
                checked={predictionConfig.include_confidence}
                onChange={(e) => setPredictionConfig({...predictionConfig, include_confidence: e.target.checked})}
              />
            }
            label="Include confidence intervals"
          />

          <FormControlLabel
            control={
              <Switch
                checked={predictionConfig.include_feature_importance}
                onChange={(e) => setPredictionConfig({...predictionConfig, include_feature_importance: e.target.checked})}
              />
            }
            label="Include feature contributions"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPredictionDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleMakePredictions}
            variant="contained"
            disabled={predictionConfig.team_ids.length === 0 || loading}
          >
            Predict
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clinical Screenings Card */}
      {clinicalScreenings?.screenings && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Assessment sx={{ mr: 2, fontSize: 28 }} />
              <Typography variant="h6">Clinical Assessments</Typography>
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              GAD7, PHQ9, and other mental health screening results
            </Typography>
            {clinicalScreenings.summary && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Total assessments: {clinicalScreenings.summary.total}
              </Alert>
            )}
            {clinicalScreenings.summary?.by_type && (
              <TableContainer component={Paper} sx={{ mb: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Assessment Type</TableCell>
                      <TableCell>Count</TableCell>
                      <TableCell>Avg Score</TableCell>
                      <TableCell>Max Score</TableCell>
                      <TableCell>Min Score</TableCell>
                      <TableCell>Crisis Alerts</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(clinicalScreenings.summary.by_type).map(([type, stats]) => (
                      <TableRow key={type}>
                        <TableCell>{type}</TableCell>
                        <TableCell>{stats.count}</TableCell>
                        <TableCell>{stats.avg_score ? stats.avg_score.toFixed(1) : 'N/A'}</TableCell>
                        <TableCell>{stats.max_score ? stats.max_score.toFixed(1) : 'N/A'}</TableCell>
                        <TableCell>{stats.min_score ? stats.min_score.toFixed(1) : 'N/A'}</TableCell>
                        <TableCell>{stats.crisis_count || 0}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={loadClinicalScreenings}
                disabled={loading}
              >
                Refresh
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PredictiveAnalytics;
