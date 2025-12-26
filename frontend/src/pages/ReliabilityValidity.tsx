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
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Assessment,
  Analytics,
  TrendingUp,
  BarChart,
  Settings,
  PlayArrow,
  Refresh,
  Info,
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  Visibility,
  Download,
  Upload,
  Science,
  Psychology,
  DataObject
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  ComposedChart,
  Area,
  AreaChart
} from 'recharts';

// Types for reliability and validity data
interface ReliabilityResult {
  cronbach_alpha: {
    coefficient: number;
    confidence_interval?: [number, number];
    interpretation: string;
    item_statistics?: Record<string, {
      item_total_correlation: number;
      alpha_if_deleted: number;
      item_mean: number;
      item_std: number;
    }>;
    recommendations: string[];
  };
  mcdonald_omega: {
    coefficient: number;
    interpretation: string;
  };
  sample_size: number;
  assessment_id: number;
  analysis_date: string;
}

interface FactorAnalysisResult {
  extraction_method: string;
  rotation_method: string;
  eigenvalues: number[];
  factor_loadings: Record<string, number[]>;
  communalities: number[];
  uniqueness: number[];
  variance_explained: number[];
  cumulative_variance: number[];
  n_factors_suggested: number;
  factor_interpretation: Record<string, string[]>;
  assessment_id: number;
  analysis_date: string;
}

interface ItemAnalysisResult {
  [itemId: string]: {
    item_id: string;
    difficulty: number;
    discrimination: number;
    item_total_correlation: number;
    item_reliability: number;
    skewness: number;
    kurtosis: number;
    option_frequencies?: Record<string, number>;
    distractor_analysis?: Record<string, {
      frequency: number;
      discrimination: number;
      is_effective: boolean;
    }>;
  };
}

interface ValidityResult {
  validity_type: string;
  coefficient: number;
  significance_level: number;
  confidence_interval?: [number, number];
  interpretation: string;
  sample_size: number;
  criterion_description?: string;
  recommendations: string[];
}

interface ComprehensiveAnalysisResult {
  reliability_results?: ReliabilityResult;
  validity_results: ValidityResult[];
  factor_analysis_results?: FactorAnalysisResult;
  item_analysis_results?: ItemAnalysisResult;
  overall_quality_score: number;
  recommendations: string[];
  analysis_time_seconds: number;
}

const ReliabilityValidity: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<number>('');
  const [analysisResults, setAnalysisResults] = useState<ComprehensiveAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [analysisConfig, setAnalysisConfig] = useState({
    include_reliability: true,
    include_validity: true,
    include_factor_analysis: true,
    include_item_analysis: true
  });
  const [dashboardData, setDashboardData] = useState<any>(null);

  useEffect(() => {
    loadAssessments();
  }, []);

  const loadAssessments = async () => {
    try {
      // This would typically fetch from your assessments API
      // For now, using placeholder data
      const placeholderAssessments = [
        { id: 1, title: "Big Five Personality Test", item_count: 44, responses: 1250 },
        { id: 2, title: "Emotional Intelligence Assessment", item_count: 30, responses: 890 },
        { id: 3, title: "Leadership Competency Survey", item_count: 25, responses: 567 },
        { id: 4, title: "Team Collaboration Scale", item_count: 18, responses: 423 }
      ];
      setAssessments(placeholderAssessments);
    } catch (err) {
      setError('Failed to load assessments');
    }
  };

  const loadDashboardData = async (assessmentId: number) => {
    try {
      const response = await fetch(`/api/v1/reliability-validity/dashboard/${assessmentId}`);
      const data = await response.json();

      if (data.success) {
        setDashboardData(data.dashboard);
      } else {
        setError(data.error_message || 'Failed to load dashboard data');
      }
    } catch (err) {
      setError('Failed to connect to reliability service');
    }
  };

  const conductComprehensiveAnalysis = async () => {
    if (!selectedAssessment) {
      setError('Please select an assessment first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/reliability-validity/comprehensive/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assessment_id: selectedAssessment,
          ...analysisConfig
        }),
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResults(data);
        setSuccess(`Analysis completed successfully! Overall quality score: ${(data.overall_quality_score * 100).toFixed(1)}%`);
      } else {
        setError(data.error_message || 'Analysis failed');
      }
    } catch (err) {
      setError('Failed to conduct analysis');
    } finally {
      setLoading(false);
    }
  };

  const getReliabilityColor = (coefficient: number) => {
    if (coefficient >= 0.90) return 'success';
    if (coefficient >= 0.80) return 'primary';
    if (coefficient >= 0.70) return 'warning';
    return 'error';
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.80) return 'success';
    if (score >= 0.60) return 'warning';
    return 'error';
  };

  const renderScreePlot = (eigenvalues: number[]) => {
    const data = eigenvalues.map((value, index) => ({
      factor: index + 1,
      eigenvalue: value,
      cumulative: eigenvalues.slice(0, index + 1).reduce((a, b) => a + b, 0)
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="factor" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <RechartsTooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="eigenvalue" fill="#8884d8" name="Eigenvalue" />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumulative"
            stroke="#82ca9d"
            strokeWidth={2}
            name="Cumulative Variance"
          />
        </ComposedChart>
      </ResponsiveContainer>
    );
  };

  const renderFactorLoadingsHeatmap = (factorLoadings: Record<string, number[]>) => {
    const data = Object.entries(factorLoadings).map(([item, loadings]) => ({
      item,
      ...loadings.reduce((acc, loading, index) => ({
        ...acc,
        [`factor_${index + 1}`]: loading
      }), {})
    }));

    return (
      <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Item</TableCell>
              {Array.from({ length: Math.max(...Object.values(factorLoadings).map(l => l.length)) }, (_, i) => (
                <TableCell key={i} align="center">Factor {i + 1}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.item}</TableCell>
                {Array.from({ length: Math.max(...Object.values(factorLoadings).map(l => l.length)) }, (_, i) => {
                  const loading = row[`factor_${i + 1}`] || 0;
                  const absLoading = Math.abs(loading);
                  return (
                    <TableCell
                      key={i}
                      align="center"
                      sx={{
                        backgroundColor: absLoading > 0.7 ? '#ffeb3b' :
                                       absLoading > 0.5 ? '#ff9800' :
                                       absLoading > 0.3 ? '#4caf50' : 'transparent',
                        fontWeight: absLoading > 0.4 ? 'bold' : 'normal'
                      }}
                    >
                      {loading.toFixed(2)}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderItemAnalysisTable = (itemResults: ItemAnalysisResult) => {
    const data = Object.values(itemResults).map(item => ({
      itemId: item.item_id,
      difficulty: item.difficulty,
      discrimination: item.discrimination,
      itemTotalCorrelation: item.item_total_correlation,
      itemReliability: item.item_reliability,
      skewness: item.skewness,
      kurtosis: item.kurtosis
    }));

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Item ID</TableCell>
              <TableCell align="center">Difficulty</TableCell>
              <TableCell align="center">Discrimination</TableCell>
              <TableCell align="center">Item-Total r</TableCell>
              <TableCell align="center">Reliability</TableCell>
              <TableCell align="center">Skewness</TableCell>
              <TableCell align="center">Kurtosis</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.itemId}</TableCell>
                <TableCell align="center">{item.difficulty.toFixed(3)}</TableCell>
                <TableCell align="center">
                  <Chip
                    label={item.discrimination.toFixed(3)}
                    color={Math.abs(item.discrimination) >= 0.4 ? 'success' :
                           Math.abs(item.discrimination) >= 0.3 ? 'warning' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={item.itemTotalCorrelation.toFixed(3)}
                    color={Math.abs(item.itemTotalCorrelation) >= 0.4 ? 'success' :
                           Math.abs(item.itemTotalCorrelation) >= 0.3 ? 'warning' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">{item.itemReliability.toFixed(3)}</TableCell>
                <TableCell align="center">{item.skewness.toFixed(3)}</TableCell>
                <TableCell align="center">{item.kurtosis.toFixed(3)}</TableCell>
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
        <Science sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Reliability & Validity Analysis
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

      {/* Assessment Selection and Configuration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Assessment Analysis Setup
          </Typography>

          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Select Assessment</InputLabel>
                <Select
                  value={selectedAssessment}
                  onChange={(e) => {
                    setSelectedAssessment(Number(e.target.value));
                    loadDashboardData(Number(e.target.value));
                  }}
                >
                  {assessments.map((assessment) => (
                    <MenuItem key={assessment.id} value={assessment.id}>
                      {assessment.title} ({assessment.responses} responses)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={conductComprehensiveAnalysis}
                  disabled={!selectedAssessment || loading}
                  size="large"
                >
                  {loading ? 'Analyzing...' : 'Start Analysis'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => loadAssessments()}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </Box>
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={analysisConfig.include_reliability}
                    onChange={(e) => setAnalysisConfig({
                      ...analysisConfig,
                      include_reliability: e.target.checked
                    })}
                  />
                }
                label="Reliability Analysis"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={analysisConfig.include_factor_analysis}
                    onChange={(e) => setAnalysisConfig({
                      ...analysisConfig,
                      include_factor_analysis: e.target.checked
                    })}
                  />
                }
                label="Factor Analysis"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={analysisConfig.include_item_analysis}
                    onChange={(e) => setAnalysisConfig({
                      ...analysisConfig,
                      include_item_analysis: e.target.checked
                    })}
                  />
                }
                label="Item Analysis"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={analysisConfig.include_validity}
                    onChange={(e) => setAnalysisConfig({
                      ...analysisConfig,
                      include_validity: e.target.checked
                    })}
                  />
                }
                label="Validity Analysis"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Dashboard Overview */}
      {dashboardData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Overview
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {dashboardData.total_respondents.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Respondents
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {dashboardData.total_items}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Items
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Chip
                    label={`α = ${dashboardData.cronbach_alpha.toFixed(3)}`}
                    color={getReliabilityColor(dashboardData.cronbach_alpha)}
                    sx={{ fontSize: '1rem', p: 2 }}
                  />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Cronbach's Alpha
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={3}>
                <Box textAlign="center">
                  <Chip
                    label={dashboardData.reliability_status}
                    color={getQualityColor(
                      dashboardData.reliability_status === 'excellent' ? 0.9 :
                      dashboardData.reliability_status === 'good' ? 0.8 :
                      dashboardData.reliability_status === 'acceptable' ? 0.7 : 0.6
                    )}
                    sx={{ fontSize: '1rem', p: 2 }}
                  />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Reliability Status
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results Tabs */}
      {analysisResults && (
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Overview" icon={<Analytics />} />
          <Tab label="Reliability" icon={<Assessment />} />
          <Tab label="Factor Analysis" icon={<BarChart />} />
          <Tab label="Item Analysis" icon={<DataObject />} />
          <Tab label="Recommendations" icon={<TrendingUp />} />
        </Tabs>
      )}

      {/* Overview Tab */}
      {analysisResults && activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Overall Quality Assessment
                </Typography>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="body1" gutterBottom>
                    Overall Quality Score: {(analysisResults.overall_quality_score * 100).toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={analysisResults.overall_quality_score * 100}
                    sx={{ height: 10, borderRadius: 5 }}
                    color={getQualityColor(analysisResults.overall_quality_score)}
                  />
                </Box>

                <Grid container spacing={3}>
                  {analysisResults.reliability_results && (
                    <Grid item xs={12} md={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom>
                            Reliability (Cronbach's Alpha)
                          </Typography>
                          <Typography variant="h4" color="primary">
                            {analysisResults.reliability_results.cronbach_alpha.coefficient.toFixed(3)}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {analysisResults.reliability_results.cronbach_alpha.interpretation}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}

                  {analysisResults.factor_analysis_results && (
                    <Grid item xs={12} md={6}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom>
                            Factor Analysis
                          </Typography>
                          <Typography variant="h4" color="primary">
                            {analysisResults.factor_analysis_results.n_factors_suggested}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Factors suggested by eigenvalue criterion
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Analysis Summary
                  </Typography>
                  <Typography variant="body2">
                    Analysis completed in {analysisResults.analysis_time_seconds.toFixed(2)} seconds
                  </Typography>
                  {analysisResults.validity_results.length > 0 && (
                    <Typography variant="body2">
                      {analysisResults.validity_results.length} validity analyses conducted
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Reliability Tab */}
      {analysisResults?.reliability_results && activeTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Internal Consistency Reliability
                </Typography>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Cronbach's Alpha
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography variant="h4" color="primary" sx={{ mr: 2 }}>
                      {analysisResults.reliability_results.cronbach_alpha.coefficient.toFixed(3)}
                    </Typography>
                    <Chip
                      label={getReliabilityColor(analysisResults.reliability_results.cronbach_alpha.coefficient)}
                      color={getReliabilityColor(analysisResults.reliability_results.cronbach_alpha.coefficient)}
                      size="small"
                    />
                  </Box>
                  {analysisResults.reliability_results.cronbach_alpha.confidence_interval && (
                    <Typography variant="body2" color="textSecondary">
                      95% CI: [{analysisResults.reliability_results.cronbach_alpha.confidence_interval[0].toFixed(3)},
                      {analysisResults.reliability_results.cronbach_alpha.confidence_interval[1].toFixed(3)}]
                    </Typography>
                  )}
                </Box>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    McDonald's Omega
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {analysisResults.reliability_results.mcdonald_omega.coefficient.toFixed(3)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {analysisResults.reliability_results.mcdonald_omega.interpretation}
                  </Typography>
                </Box>

                <Typography variant="body2">
                  Sample Size: {analysisResults.reliability_results.sample_size}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Item-Total Correlations
                </Typography>

                {analysisResults.reliability_results.cronbach_alpha.item_statistics && (
                  <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Item</TableCell>
                          <TableCell align="center">Item-Total r</TableCell>
                          <TableCell align="center">α if Deleted</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(analysisResults.reliability_results.cronbach_alpha.item_statistics)
                          .slice(0, 10)
                          .map(([itemId, stats], index) => (
                            <TableRow key={index}>
                              <TableCell>{itemId}</TableCell>
                              <TableCell align="center">
                                <Chip
                                  label={stats.item_total_correlation.toFixed(3)}
                                  color={Math.abs(stats.item_total_correlation) >= 0.4 ? 'success' :
                                         Math.abs(stats.item_total_correlation) >= 0.3 ? 'warning' : 'error'}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell align="center">
                                {stats.alpha_if_deleted.toFixed(3)}
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Factor Analysis Tab */}
      {analysisResults?.factor_analysis_results && activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Factor Analysis Results
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Extraction: {analysisResults.factor_analysis_results.extraction_method.replace('_', ' ')} |
                  Rotation: {analysisResults.factor_analysis_results.rotation_method}
                </Typography>

                {/* Scree Plot */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Scree Plot
                  </Typography>
                  {renderScreePlot(analysisResults.factor_analysis_results.eigenvalues)}
                </Box>

                {/* Factor Loadings */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Factor Loadings Matrix
                  </Typography>
                  {renderFactorLoadingsHeatmap(analysisResults.factor_analysis_results.factor_loadings)}
                </Box>

                {/* Variance Explained */}
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Variance Explained by Factors
                    </Typography>
                    {analysisResults.factor_analysis_results.variance_explained.map((variance, index) => (
                      <Box key={index} sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          Factor {index + 1}: {(variance * 100).toFixed(1)}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={variance * 100}
                          sx={{ height: 4, borderRadius: 2 }}
                        />
                      </Box>
                    ))}
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Cumulative Variance Explained
                    </Typography>
                    {analysisResults.factor_analysis_results.cumulative_variance.map((cumulative, index) => (
                      <Box key={index} sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          {index + 1} Factor{index > 0 ? 's' : ''}: {(cumulative * 100).toFixed(1)}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={cumulative * 100}
                          sx={{ height: 4, borderRadius: 2 }}
                          color="primary"
                        />
                      </Box>
                    ))}
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Item Analysis Tab */}
      {analysisResults?.item_analysis_results && activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Item Analysis Results
                </Typography>

                {renderItemAnalysisTable(analysisResults.item_analysis_results)}

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Item Statistics Summary
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5">
                          {Object.keys(analysisResults.item_analysis_results).length}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Total Items
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5">
                          {Object.values(analysisResults.item_analysis_results)
                            .filter(item => Math.abs(item.discrimination) >= 0.4).length}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Excellent Items (r &ge; 0.4)
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5">
                          {Object.values(analysisResults.item_analysis_results)
                            .filter(item => Math.abs(item.discrimination) >= 0.3 && Math.abs(item.discrimination) < 0.4).length}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Good Items (0.3 &lt;= r &lt; 0.4)
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h5">
                          {Object.values(analysisResults.item_analysis_results)
                            .filter(item => Math.abs(item.discrimination) < 0.3).length}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Poor Items (r &lt; 0.3)
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Recommendations Tab */}
      {analysisResults && activeTab === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recommendations & Next Steps
                </Typography>

                <List>
                  {analysisResults.recommendations.map((recommendation, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        {recommendation.includes('Excellent') ? <CheckCircle color="success" /> :
                         recommendation.includes('Good') ? <CheckCircle color="primary" /> :
                         recommendation.includes('Poor') || recommendation.includes('Low') ? <Warning color="error" /> :
                         <Info color="info" />}
                      </ListItemIcon>
                      <ListItemText primary={recommendation} />
                    </ListItem>
                  ))}
                </List>

                {analysisResults.reliability_results?.cronbach_alpha.recommendations && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>
                      Reliability-Specific Recommendations
                    </Typography>
                    <List>
                      {analysisResults.reliability_results.cronbach_alpha.recommendations.map((rec, index) => (
                        <ListItem key={index}>
                          <ListItemIcon><Assessment color="primary" /></ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default ReliabilityValidity;