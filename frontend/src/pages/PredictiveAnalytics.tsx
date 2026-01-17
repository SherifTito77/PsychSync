import React, { useState, useEffect } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Insights,
  ModelTraining,
  Assessment,
  TrendingUp,
  BarChart,
  Settings,
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  Info,
  ExpandMore,
  CheckCircle,
  Error,
  Warning
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart as RechartsBarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

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
  team_ids?: number[];
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
  const [trainingDialogOpen, setTrainingDialogOpen] = useState(false);
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
    team_ids: [] as number[],
    include_confidence: true,
    include_feature_importance: true
  });
  const [dataQuality, setDataQuality] = useState<any>(null);
  const [trainingInProgress, setTrainingInProgress] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);

  // Load models on component mount
  useEffect(() => {
    loadModels();
    assessDataQuality();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/predictions/models');
      const data = await response.json();

      if (data.success) {
        setModels(data.models);
      } else {
        setError(data.error_message || 'Failed to load models');
      }
    } catch (err) {
      setError('Failed to connect to prediction service');
    } finally {
      setLoading(false);
    }
  };

  const assessDataQuality = async () => {
    try {
      const response = await fetch('/api/v1/predictions/data/quality');
      const data = await response.json();

      if (data.success) {
        setDataQuality(data.data_quality);
      }
    } catch (err) {
      console.error('Failed to assess data quality:', err);
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

      const response = await fetch('/api/v1/predictions/train', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trainingConfig),
      });

      clearInterval(progressInterval);
      setTrainingProgress(100);

      const data = await response.json();

      if (data.success) {
        setSuccess(`Model training completed successfully! Best model: ${data.model_comparison?.best_model_name}`);
        setTrainingDialogOpen(false);
        await loadModels();
      } else {
        setError(data.error_message || 'Model training failed');
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

      const response = await fetch('/api/v1/predictions/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prediction_type: 'team_performance',
          entity_ids: predictionConfig.team_ids,
          model_id: selectedModel || undefined,
          include_confidence: predictionConfig.include_confidence,
          include_feature_importance: predictionConfig.include_feature_importance
        }),
      });

      const data = await response.json();

      if (data.success) {
        setPredictions(data.predictions);
        setPredictionDialogOpen(false);
        setSuccess(`Generated ${data.predictions.length} predictions successfully`);
      } else {
        setError(data.error_message || 'Prediction failed');
      }
    } catch (err) {
      setError('Failed to make predictions');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!window.confirm('Are you sure you want to delete this model?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/predictions/models/${modelId}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        setSuccess('Model deleted successfully');
        await loadModels();
      } else {
        setError(data.error_message || 'Failed to delete model');
      }
    } catch (err) {
      setError('Failed to delete model');
    }
  };

  const getPerformanceColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getPerformanceIcon = (score?: number) => {
    if (!score) return <Error />;
    if (score >= 0.8) return <CheckCircle color="success" />;
    if (score >= 0.6) return <Warning color="warning" />;
    return <Error color="error" />;
  };

  const renderModelPerformanceChart = (model: ModelInfo) => {
    const performanceData = Object.entries(model.performance)
      .filter(([key, value]) => typeof value === 'number' && key !== 'cv_scores')
      .map(([key, value]) => ({
        metric: key.replace(/_/g, ' ').toUpperCase(),
        value: Number(value.toFixed(3))
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
        feature: feature.length > 15 ? feature.substring(0, 15) + '...' : feature,
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
                      : prediction.prediction}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={`${(prediction.confidence * 100).toFixed(1)}%`}
                    color={prediction.confidence > 0.8 ? 'success' : prediction.confidence > 0.6 ? 'warning' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {prediction.prediction_interval ? (
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
                    {new Date(prediction.timestamp).toLocaleString()}
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
      {dataQuality && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Quality Assessment
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {(dataQuality.overall_score * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Overall Quality
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {dataQuality.total_rows.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Data Points
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {dataQuality.total_features}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Features
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {(dataQuality.completeness * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completeness
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                variant="determinate"
                value={dataQuality.overall_score * 100}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label="Models" icon={<ModelTraining />} />
        <Tab label="Predictions" icon={<TrendingUp />} />
        <Tab label="Training" icon={<Settings />} />
      </Tabs>

      {/* Models Tab */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
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
            <Grid item xs={12} md={6} lg={4} key={model.model_id}>
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
                      Trained: {new Date(model.training_date).toLocaleDateString()}
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
            <Grid item xs={12}>
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
                    onClick={() => setTrainingDialogOpen(true)}
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
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Prediction Results</Typography>
            <Button
              variant="contained"
              startIcon={<TrendingUp />}
              onClick={() => setPredictionDialogOpen(true)}
              disabled={!selectedModel}
            >
              Make Predictions
            </Button>
          </Grid>

          <Grid item xs={12}>
            {renderPredictionResults()}
          </Grid>
        </Grid>
      )}

      {/* Training Tab */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Training Configuration
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                  Configure and train new predictive models using your assessment data
                </Typography>

                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
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
                            {(selected as string[]).map((value) => (
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

                  <Grid item xs={12} md={6}>
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
      <Dialog open={predictionDialogOpen} onClose={() => setPredictionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Make Predictions</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select teams to predict performance for using the selected model.
          </Typography>

          <TextField
            fullWidth
            label="Team IDs (comma-separated)"
            placeholder="e.g., 1,2,3,4"
            value={predictionConfig.team_ids.join(',')}
            onChange={(e) => setPredictionConfig({
              ...predictionConfig,
              team_ids: e.target.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
            })}
            sx={{ mb: 2 }}
            helperText="Enter team IDs separated by commas"
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
    </Box>
  );
};

export default PredictiveAnalytics;
