"""
Longitudinal Analysis & Growth Trajectories for PsychSync
Analyze change over time, intervention effectiveness, and predict future outcomes.

Requirements:
    pip install pandas numpy scipy statsmodels
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import UnivariateSpline
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


@dataclass
class GrowthTrajectory:
    """Representation of a growth/decline trajectory."""
    trajectory_type: str  # 'linear', 'quadratic', 'cubic', 'exponential'
    baseline_value: float
    current_value: float
    rate_of_change: float
    predicted_values: List[Dict]
    model_fit: float  # R-squared
    confidence: float
    interpretation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InterventionEffect:
    """Results of intervention effectiveness analysis."""
    intervention_name: str
    start_date: str
    effect_size: float
    p_value: float
    is_significant: bool
    mean_before: float
    mean_after: float
    change: float
    percent_change: float
    interpretation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LongitudinalAnalyzer:
    """
    Analyze longitudinal data to track change over time.
    """
    
    def __init__(self):
        """Initialize longitudinal analyzer."""
        pass
    
    def analyze_trajectory(
        self,
        data: pd.DataFrame,
        value_column: str = 'score',
        date_column: str = 'date',
        trajectory_type: str = 'auto',
        prediction_periods: int = 4
    ) -> GrowthTrajectory:
        """
        Analyze growth trajectory and predict future values.
        
        Args:
            data: DataFrame with time-series data
            value_column: Column containing outcome values
            date_column: Column containing dates
            trajectory_type: Type of trajectory ('linear', 'quadratic', 'auto')
            prediction_periods: Number of future periods to predict
            
        Returns:
            GrowthTrajectory object
        """
        # Ensure data is sorted by date
        data = data.sort_values(date_column).copy()
        
        # Convert dates to numeric (days since start)
        data['days'] = (
            pd.to_datetime(data[date_column]) - 
            pd.to_datetime(data[date_column].iloc[0])
        ).dt.days
        
        X = data['days'].values
        y = data[value_column].values
        
        if trajectory_type == 'auto':
            # Try different models and select best
            trajectory_type, model_fit = self._select_best_trajectory(X, y)
        
        # Fit selected model
        if trajectory_type == 'linear':
            coeffs, r_squared = self._fit_linear(X, y)
            predict_fn = lambda x: coeffs[0] * x + coeffs[1]
        elif trajectory_type == 'quadratic':
            coeffs, r_squared = self._fit_polynomial(X, y, degree=2)
            predict_fn = lambda x: np.polyval(coeffs, x)
        elif trajectory_type == 'cubic':
            coeffs, r_squared = self._fit_polynomial(X, y, degree=3)
            predict_fn = lambda x: np.polyval(coeffs, x)
        else:
            # Default to linear
            coeffs, r_squared = self._fit_linear(X, y)
            predict_fn = lambda x: coeffs[0] * x + coeffs[1]
            trajectory_type = 'linear'
        
        # Calculate rate of change
        if trajectory_type == 'linear':
            rate_of_change = coeffs[0]
        else:
            # For non-linear, calculate rate at current time
            current_x = X[-1]
            rate_of_change = predict_fn(current_x + 1) - predict_fn(current_x)
        
        # Generate predictions
        last_date = pd.to_datetime(data[date_column].iloc[-1])
        prediction_interval = (X[-1] - X[-2]) if len(X) > 1 else 1
        
        predicted_values = []
        for i in range(1, prediction_periods + 1):
            pred_x = X[-1] + (prediction_interval * i)
            pred_y = predict_fn(pred_x)
            pred_date = last_date + timedelta(days=int(prediction_interval * i))
            
            # Calculate confidence interval (simplified)
            residuals = y - np.array([predict_fn(x) for x in X])
            std_error = np.std(residuals)
            ci_lower = pred_y - 1.96 * std_error
            ci_upper = pred_y + 1.96 * std_error
            
            predicted_values.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_value': float(pred_y),
                'confidence_interval': (float(ci_lower), float(ci_upper))
            })
        
        # Interpret trajectory
        baseline = y[0]
        current = y[-1]
        change = current - baseline
        
        if abs(rate_of_change) < 0.1:
            interpretation = 'stable'
        elif rate_of_change < -0.1:
            interpretation = 'improving'  # Assuming lower scores are better
        else:
            interpretation = 'declining'
        
        return GrowthTrajectory(
            trajectory_type=trajectory_type,
            baseline_value=float(baseline),
            current_value=float(current),
            rate_of_change=float(rate_of_change),
            predicted_values=predicted_values,
            model_fit=float(r_squared),
            confidence=float(r_squared),
            interpretation=interpretation
        )
    
    def _fit_linear(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit linear model and return coefficients and R²."""
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        return np.array([slope, intercept]), r_value ** 2
    
    def _fit_polynomial(
        self,
        X: np.ndarray,
        y: np.ndarray,
        degree: int
    ) -> Tuple[np.ndarray, float]:
        """Fit polynomial model and return coefficients and R²."""
        coeffs = np.polyfit(X, y, degree)
        y_pred = np.polyval(coeffs, X)
        r_squared = 1 - (np.sum((y - y_pred)**2) / np.sum((y - y.mean())**2))
        return coeffs, r_squared
    
    def _select_best_trajectory(self, X: np.ndarray, y: np.ndarray) -> Tuple[str, float]:
        """Select best-fitting trajectory type."""
        models = {
            'linear': self._fit_linear(X, y)[1],
            'quadratic': self._fit_polynomial(X, y, 2)[1],
            'cubic': self._fit_polynomial(X, y, 3)[1]
        }
        
        # Penalize complexity (AIC-like)
        penalties = {'linear': 0, 'quadratic': 0.02, 'cubic': 0.05}
        adjusted = {k: v - penalties[k] for k, v in models.items()}
        
        best_model = max(adjusted, key=adjusted.get)
        return best_model, models[best_model]
    
    def compare_phases(
        self,
        data: pd.DataFrame,
        phase_column: str,
        value_column: str = 'score'
    ) -> Dict:
        """
        Compare outcomes across different treatment phases.
        
        Args:
            data: DataFrame with phase information
            phase_column: Column indicating phase
            value_column: Column with outcome values
            
        Returns:
            Dictionary with phase comparison statistics
        """
        phases = data[phase_column].unique()
        
        if len(phases) < 2:
            return {'error': 'Need at least 2 phases to compare'}
        
        # Calculate statistics for each phase
        phase_stats = []
        for phase in phases:
            phase_data = data[data[phase_column] == phase][value_column]
            
            phase_stats.append({
                'phase': str(phase),
                'n': len(phase_data),
                'mean': float(phase_data.mean()),
                'std': float(phase_data.std()),
                'min': float(phase_data.min()),
                'max': float(phase_data.max()),
                'median': float(phase_data.median())
            })
        
        # Pairwise comparisons
        comparisons = []
        for i in range(len(phases)):
            for j in range(i + 1, len(phases)):
                data1 = data[data[phase_column] == phases[i]][value_column]
                data2 = data[data[phase_column] == phases[j]][value_column]
                
                # T-test
                t_stat, p_value = stats.ttest_ind(data1, data2)
                
                # Effect size
                pooled_std = np.sqrt((data1.std()**2 + data2.std()**2) / 2)
                cohens_d = (data1.mean() - data2.mean()) / pooled_std if pooled_std > 0 else 0
                
                comparisons.append({
                    'phase1': str(phases[i]),
                    'phase2': str(phases[j]),
                    'mean_diff': float(data1.mean() - data2.mean()),
                    'p_value': float(p_value),
                    'cohens_d': float(cohens_d),
                    'significant': p_value < 0.05
                })
        
        return {
            'phase_statistics': phase_stats,
            'pairwise_comparisons': comparisons
        }
    
    def calculate_reliable_change(
        self,
        baseline: float,
        current: float,
        test_reliability: float = 0.90,
        population_sd: float = 5.0
    ) -> Dict:
        """
        Calculate if change is statistically reliable (Jacobson-Truax method).
        
        Args:
            baseline: Initial score
            current: Current score
            test_reliability: Test-retest reliability
            population_sd: Population standard deviation
            
        Returns:
            Dictionary with reliable change analysis
        """
        # Standard error of difference
        se_diff = population_sd * np.sqrt(2 * (1 - test_reliability))
        
        # Reliable change index
        rci = (current - baseline) / se_diff
        
        # Critical value (1.96 for p < .05, two-tailed)
        is_reliable = abs(rci) > 1.96
        
        # Clinical significance cutoff (2 SD below population mean)
        # Assuming population mean = 10 for simplicity
        clinical_cutoff = 10 - (2 * population_sd)
        is_clinically_significant = current < clinical_cutoff
        
        # Classify outcome
        if is_reliable and is_clinically_significant:
            outcome = 'recovered'
        elif is_reliable and not is_clinically_significant:
            outcome = 'improved'
        elif not is_reliable:
            outcome = 'unchanged'
        else:
            outcome = 'deteriorated' if current > baseline else 'unchanged'
        
        return {
            'baseline_score': float(baseline),
            'current_score': float(current),
            'change': float(current - baseline),
            'rci': float(rci),
            'se_diff': float(se_diff),
            'is_reliable_change': bool(is_reliable),
            'is_clinically_significant': bool(is_clinically_significant),
            'outcome_category': outcome
        }
    
    def analyze_intervention_effectiveness(
        self,
        data: pd.DataFrame,
        intervention_date: datetime,
        intervention_name: str,
        value_column: str = 'score',
        date_column: str = 'date',
        pre_window_days: int = 30,
        post_window_days: int = 30
    ) -> InterventionEffect:
        """
        Analyze effectiveness of an intervention.
        
        Args:
            data: DataFrame with time-series data
            intervention_date: Date intervention started
            intervention_name: Name of intervention
            value_column: Column with scores
            date_column: Column with dates
            pre_window_days: Days before intervention to analyze
            post_window_days: Days after intervention to analyze
            
        Returns:
            InterventionEffect object
        """
        # Ensure date column is datetime
        data[date_column] = pd.to_datetime(data[date_column])
        
        # Define windows
        pre_start = intervention_date - timedelta(days=pre_window_days)
        post_end = intervention_date + timedelta(days=post_window_days)
        
        # Extract data
        pre_data = data[
            (data[date_column] >= pre_start) &
            (data[date_column] < intervention_date)
        ][value_column]
        
        post_data = data[
            (data[date_column] >= intervention_date) &
            (data[date_column] <= post_end)
        ][value_column]
        
        if len(pre_data) < 3 or len(post_data) < 3:
            # Not enough data
            return InterventionEffect(
                intervention_name=intervention_name,
                start_date=intervention_date.strftime('%Y-%m-%d'),
                effect_size=0.0,
                p_value=1.0,
                is_significant=False,
                mean_before=0.0,
                mean_after=0.0,
                change=0.0,
                percent_change=0.0,
                interpretation='insufficient_data'
            )
        
        # Calculate statistics
        mean_before = pre_data.mean()
        mean_after = post_data.mean()
        change = mean_after - mean_before
        percent_change = (change / mean_before * 100) if mean_before != 0 else 0
        
        # Statistical test
        t_stat, p_value = stats.ttest_ind(pre_data, post_data)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((pre_data.std()**2 + post_data.std()**2) / 2)
        cohens_d = (mean_before - mean_after) / pooled_std if pooled_std > 0 else 0
        
        # Interpretation
        if p_value >= 0.05:
            interpretation = 'no_significant_effect'
        elif cohens_d > 0.5:
            interpretation = 'large_positive_effect'
        elif cohens_d > 0.2:
            interpretation = 'moderate_positive_effect'
        elif cohens_d > 0:
            interpretation = 'small_positive_effect'
        elif cohens_d < -0.5:
            interpretation = 'large_negative_effect'
        elif cohens_d < -0.2:
            interpretation = 'moderate_negative_effect'
        else:
            interpretation = 'small_negative_effect'
        
        return InterventionEffect(
            intervention_name=intervention_name,
            start_date=intervention_date.strftime('%Y-%m-%d'),
            effect_size=float(cohens_d),
            p_value=float(p_value),
            is_significant=bool(p_value < 0.05),
            mean_before=float(mean_before),
            mean_after=float(mean_after),
            change=float(change),
            percent_change=float(percent_change),
            interpretation=interpretation
        )
    
    def calculate_growth_metrics(
        self,
        data: pd.DataFrame,
        value_column: str = 'score'
    ) -> Dict:
        """
        Calculate various growth/change metrics.
        
        Args:
            data: DataFrame with time-series data
            value_column: Column with scores
            
        Returns:
            Dictionary with growth metrics
        """
        values = data[value_column].values
        
        if len(values) < 2:
            return {'error': 'Need at least 2 data points'}
        
        # Total change
        total_change = values[-1] - values[0]
        
        # Average change per measurement
        avg_change = total_change / (len(values) - 1)
        
        # Rate of change (slope)
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Volatility (standard deviation of changes)
        changes = np.diff(values)
        volatility = np.std(changes)
        
        # Consistency (how linear is the change?)
        consistency = r_value ** 2
        
        # Momentum (recent vs. early change)
        if len(values) >= 4:
            early_slope = stats.linregress(x[:len(x)//2], values[:len(values)//2])[0]
            recent_slope = stats.linregress(x[len(x)//2:], values[len(values)//2:])[0]
            momentum = recent_slope - early_slope
        else:
            momentum = 0.0
        
        # Recovery percentage (if starting high and going low is good)
        if values[0] > 0:
            recovery_pct = (values[0] - values[-1]) / values[0] * 100
        else:
            recovery_pct = 0.0
        
        return {
            'total_change': float(total_change),
            'average_change_per_period': float(avg_change),
            'rate_of_change': float(slope),
            'volatility': float(volatility),
            'consistency_r2': float(consistency),
            'momentum': float(momentum),
            'recovery_percentage': float(recovery_pct),
            'n_measurements': len(values)
        }


class TimeSeriesForecaster:
    """
    Forecast future values using time-series analysis.
    """
    
    def __init__(self):
        """Initialize forecaster."""
        pass
    
    def forecast_simple_moving_average(
        self,
        data: pd.Series,
        window: int = 7,
        periods_ahead: int = 7
    ) -> Dict:
        """
        Forecast using simple moving average.
        
        Args:
            data: Time series data
            window: Moving average window
            periods_ahead: Number of periods to forecast
            
        Returns:
            Dictionary with forecast
        """
        if len(data) < window:
            return {'error': 'Not enough data for forecast'}
        
        # Calculate moving average
        ma = data.rolling(window=window).mean()
        last_ma = ma.iloc[-1]
        
        # Simple forecast: assume continuation
        forecasts = [last_ma] * periods_ahead
        
        # Estimate uncertainty from recent volatility
        recent_std = data.tail(window).std()
        
        forecast_data = []
        for i in range(periods_ahead):
            forecast_data.append({
                'period_ahead': i + 1,
                'forecast': float(forecasts[i]),
                'lower_bound': float(forecasts[i] - 1.96 * recent_std),
                'upper_bound': float(forecasts[i] + 1.96 * recent_std)
            })
        
        return {
            'forecast_type': 'simple_moving_average',
            'window': window,
            'forecasts': forecast_data
        }
    
    def forecast_exponential_smoothing(
        self,
        data: pd.Series,
        alpha: float = 0.3,
        periods_ahead: int = 7
    ) -> Dict:
        """
        Forecast using exponential smoothing.
        
        Args:
            data: Time series data
            alpha: Smoothing parameter (0-1)
            periods_ahead: Number of periods to forecast
            
        Returns:
            Dictionary with forecast
        """
        # Exponentially weighted moving average
        ewm = data.ewm(alpha=alpha, adjust=False).mean()
        last_ewm = ewm.iloc[-1]
        
        # Calculate trend
        if len(data) >= 2:
            recent_trend = data.iloc[-1] - data.iloc[-2]
        else:
            recent_trend = 0
        
        # Dampen trend for future periods
        forecasts = []
        for i in range(periods_ahead):
            damping = 0.9 ** i  # Trend dampens over time
            forecast = last_ewm + (recent_trend * damping * (i + 1))
            forecasts.append(forecast)
        
        # Estimate uncertainty
        residuals = data - ewm
        residual_std = residuals.std()
        
        forecast_data = []
        for i in range(periods_ahead):
            uncertainty = residual_std * np.sqrt(i + 1)  # Increases with time
            
            forecast_data.append({
                'period_ahead': i + 1,
                'forecast': float(forecasts[i]),
                'lower_bound': float(forecasts[i] - 1.96 * uncertainty),
                'upper_bound': float(forecasts[i] + 1.96 * uncertainty)
            })
        
        return {
            'forecast_type': 'exponential_smoothing',
            'alpha': alpha,
            'forecasts': forecast_data
        }


# Example usage
if __name__ == "__main__":
    print("Longitudinal Analysis Demo")
    print("=" * 60)
    
    # Generate sample longitudinal data
    dates = pd.date_range('2024-01-01', periods=50, freq='W')
    np.random.seed(42)
    
    # Simulate treatment response (quadratic improvement)
    t = np.arange(50)
    scores = 20 - 0.15 * t - 0.003 * t**2 + np.random.normal(0, 1, 50)
    scores = np.clip(scores, 0, 27)
    
    data = pd.DataFrame({
        'date': dates,
        'score': scores
    })
    
    # 1. Analyze growth trajectory
    print("\n1. Analyzing Growth Trajectory...")
    analyzer = LongitudinalAnalyzer()
    trajectory = analyzer.analyze_trajectory(data, prediction_periods=4)
    
    print(f"   Trajectory type: {trajectory.trajectory_type}")
    print(f"   Baseline: {trajectory.baseline_value:.2f}")
    print(f"   Current: {trajectory.current_value:.2f}")
    print(f"   Rate of change: {trajectory.rate_of_change:.3f} per week")
    print(f"   Model fit (R²): {trajectory.model_fit:.3f}")
    print(f"   Interpretation: {trajectory.interpretation}")
    
    print("\n   Predictions:")
    for pred in trajectory.predicted_values:
        print(f"      {pred['date']}: {pred['predicted_value']:.2f} "
              f"(CI: {pred['confidence_interval'][0]:.2f} - {pred['confidence_interval'][1]:.2f})")
    
    # 2. Calculate reliable change
    print("\n2. Calculating Reliable Change...")
    rci_result = analyzer.calculate_reliable_change(
        baseline=scores[0],
        current=scores[-1],
        test_reliability=0.90,
        population_sd=5.0
    )
    
    print(f"   Baseline: {rci_result['baseline_score']:.2f}")
    print(f"   Current: {rci_result['current_score']:.2f}")
    print(f"   Change: {rci_result['change']:.2f}")
    print(f"   RCI: {rci_result['rci']:.3f}")
    print(f"   Reliable change: {rci_result['is_reliable_change']}")
    print(f"   Outcome: {rci_result['outcome_category']}")
    
    # 3. Analyze intervention effectiveness
    print("\n3. Analyzing Intervention Effectiveness...")
    intervention_date = pd.to_datetime('2024-06-15')
    
    intervention_effect = analyzer.analyze_intervention_effectiveness(
        data,
        intervention_date,
        'Medication Addition',
        pre_window_days=60,
        post_window_days=60
    )
    
    print(f"   Intervention: {intervention_effect.intervention_name}")
    print(f"   Mean before: {intervention_effect.mean_before:.2f}")
    print(f"   Mean after: {intervention_effect.mean_after:.2f}")
    print(f"   Change: {intervention_effect.change:.2f} ({intervention_effect.percent_change:.1f}%)")
    print(f"   Effect size (Cohen's d): {intervention_effect.effect_size:.3f}")
    print(f"   P-value: {intervention_effect.p_value:.4f}")
    print(f"   Significant: {intervention_effect.is_significant}")
    print(f"   Interpretation: {intervention_effect.interpretation}")
    
    # 4. Calculate growth metrics
    print("\n4. Calculating Growth Metrics...")
    metrics = analyzer.calculate_growth_metrics(data)
    
    print(f"   Total change: {metrics['total_change']:.2f}")
    print(f"   Avg change per period: {metrics['average_change_per_period']:.3f}")
    print(f"   Rate of change: {metrics['rate_of_change']:.3f}")
    print(f"   Volatility: {metrics['volatility']:.3f}")
    print(f"   Consistency (R²): {metrics['consistency_r2']:.3f}")
    print(f"   Recovery %: {metrics['recovery_percentage']:.1f}%")
    
    # 5. Forecast future values
    print("\n5. Forecasting Future Values...")
    forecaster = TimeSeriesForecaster()
    forecast = forecaster.forecast_exponential_smoothing(
        data['score'],
        alpha=0.3,
        periods_ahead=4
    )
    
    print(f"   Forecast type: {forecast['forecast_type']}")
    for f in forecast['forecasts']:
        print(f"      Period +{f['period_ahead']}: {f['forecast']:.2f} "
              f"(CI: {f['lower_bound']:.2f} - {f['upper_bound']:.2f})")
    
    print("\n" + "=" * 60)
    print("Demo complete!")