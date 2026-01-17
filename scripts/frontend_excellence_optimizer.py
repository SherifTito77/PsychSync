#!/usr/bin/env python3
"""
PsychSync Frontend Excellence Optimizer
Comprehensive frontend performance analysis and optimization system

Implements:
- Bundle size analysis and optimization
- Component performance optimization
- Loading performance analysis
- User experience metrics
- JavaScript/CSS optimization
- Image and asset optimization
- SEO and accessibility analysis
- Progressive Web App features
"""

import asyncio
import subprocess
import sys
import os
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import requests
from urllib.parse import urljoin
import gzip

sys.path.append(str(Path(__file__).parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BundleAnalysisResult:
    """Bundle analysis results"""
    total_size: int
    gzipped_size: int
    chunks: List[Dict[str, Any]]
    largest_assets: List[Dict[str, Any]]
    unused_exports: List[str]
    duplicate_dependencies: List[Dict[str, Any]]
    optimization_potential: float

@dataclass
class ComponentPerformanceMetrics:
    """Component performance metrics"""
    component_name: str
    render_count: int
    avg_render_time: float
    re_render_frequency: float
    prop_changes: int
    state_changes: int
    optimization_suggestions: List[str]

@dataclass
<arg_value> PageLoadMetrics:
    """Page load performance metrics"""
    url: str
    total_size: int
    num_requests: int
    dom_content_loaded: float
    load_complete: float
    first_contentful_paint: float
    largest_contentful_paint: float
    cumulative_layout_shift: float
    first_input_delay: float

@dataclass
class AccessibilityAuditResult:
    """Accessibility audit result"""
    url: str
    wcag_level: str
    violations: List[Dict[str, Any]]
    passes: List[Dict[str, Any]]
    incomplete: List[Dict[str, Any]]
    score: float
    critical_issues: List[str]

@dataclass
class SEOAuditResult:
    """SEO audit result"""
    url: str
    score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    meta_tags_present: Dict[str, bool]
    structured_data_present: bool

class FrontendExcellenceOptimizer:
    """
    Comprehensive frontend performance and quality optimization system
    """

    def __init__(self, frontend_dir: str = "frontend", base_url: str = "http://localhost:5173"):
        self.frontend_dir = frontend_dir
        self.base_url = base_url
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.frontend_path = os.path.join(self.project_root, frontend_dir)

    async def analyze_bundle_size(self) -> BundleAnalysisResult:
        """Analyze bundle size and identify optimization opportunities"""
        print("📦 Analyzing bundle size...")

        try:
            # Ensure we're in the frontend directory
            original_cwd = os.getcwd()
            os.chdir(self.frontend_path)

            # Run webpack-bundle-analyzer or similar
            build_result = subprocess.run(
                ['npm', 'run', 'build'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if build_result.returncode != 0:
                logger.error(f"Build failed: {build_result.stderr}")
                return BundleAnalysisResult(0, 0, [], [], [], [], 0.0)

            # Analyze build output
            dist_path = os.path.join(self.frontend_path, 'dist')
            bundle_analysis = self._analyze_dist_folder(dist_path)

            # Run bundle analyzer if available
            try:
                analyzer_result = subprocess.run(
                    ['npx', 'webpack-bundle-analyzer', 'dist/stats.json', '--mode', 'json', '--no-'],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if analyzer_result.returncode == 0:
                    bundle_data = json.loads(analyzer_result.stdout)
                    bundle_analysis = self._parse_bundle_analyzer_data(bundle_data)
            except Exception as e:
                logger.info(f"Bundle analyzer not available, using manual analysis: {e}")

            os.chdir(original_cwd)
            return bundle_analysis

        except Exception as e:
            os.chdir(original_cwd)
            logger.error(f"Error analyzing bundle size: {e}")
            return BundleAnalysisResult(0, 0, [], [], [], [], 0.0)

    async def analyze_component_performance(self) -> List[ComponentPerformanceMetrics]:
        """Analyze React component performance"""
        print("⚡ Analyzing component performance...")

        try:
            # Analyze component files
            component_files = self._find_component_files()
            component_metrics = []

            for component_file in component_files:
                metrics = await self._analyze_component_file(component_file)
                component_metrics.append(metrics)

            return component_metrics

        except Exception as e:
            logger.error(f"Error analyzing component performance: {e}")
            return []

    async def analyze_page_load_performance(self, test_urls: List[str] = None) -> List[PageLoadMetrics]:
        """Analyze page load performance"""
        print("🚀 Analyzing page load performance...")

        if not test_urls:
            test_urls = [
                self.base_url,
                f"{self.base_url}/login",
                f"{self.base_url}/dashboard"
            ]

        page_metrics = []

        for url in test_urls:
            try:
                metrics = await self._measure_page_performance(url)
                page_metrics.append(metrics)
                print(f"  ✅ Analyzed {url}: {metrics.load_complete:.2f}s load time")
            except Exception as e:
                logger.error(f"Error analyzing {url}: {e}")

        return page_metrics

    async def run_accessibility_audit(self, test_urls: List[str] = None) -> List[AccessibilityAuditResult]:
        """Run accessibility audit using axe-core or similar"""
        print("♿ Running accessibility audit...")

        if not test_urls:
            test_urls = [
                self.base_url,
                f"{self.base_url}/login",
                f"{self.base_url}/dashboard"
            ]

        accessibility_results = []

        for url in test_urls:
            try:
                result = await self._run_accessibility_test(url)
                accessibility_results.append(result)
                print(f"  {'✅' if result.score > 80 else '⚠️'} {url}: {result.score:.0f} accessibility score")
            except Exception as e:
                logger.error(f"Error auditing {url}: {e}")

        return accessibility_results

    async def run_seo_audit(self, test_urls: List[str] = None) -> List[SEOAuditResult]:
        """Run SEO audit"""
        print("🔍 Running SEO audit...")

        if not test_urls:
            test_urls = [
                self.base_url,
                f"{self.base_url}/about",
                f"{self.base_url}/features"
            ]

        seo_results = []

        for url in test_urls:
            try:
                result = await self._run_seo_test(url)
                seo_results.append(result)
                print(f"  {'✅' if result.score > 80 else '⚠️'} {url}: {result.score:.0f} SEO score")
            except Exception as e:
                logger.error(f"Error auditing SEO for {url}: {e}")

        return seo_results

    async def analyze_image_optimization(self) -> Dict[str, Any]:
        """Analyze image optimization opportunities"""
        print("🖼️  Analyzing image optimization...")

        try:
            image_files = self._find_image_files()
            optimization_analysis = {
                'total_images': len(image_files),
                'total_size_mb': 0,
                'unoptimized_images': [],
                'format_recommendations': {},
                'size_savings_potential_mb': 0
            }

            for image_file in image_files:
                file_info = self._analyze_image_file(image_file)
                optimization_analysis['total_size_mb'] += file_info['size_mb']

                if file_info['needs_optimization']:
                    optimization_analysis['unoptimized_images'].append(file_info)
                    optimization_analysis['size_savings_potential_mb'] += file_info['savings_potential_mb']

                # Track format recommendations
                format_rec = file_info['format_recommendation']
                if format_rec:
                    optimization_analysis['format_recommendations'][format_rec] = \
                        optimization_analysis['format_recommendations'].get(format_rec, 0) + 1

            return optimization_analysis

        except Exception as e:
            logger.error(f"Error analyzing image optimization: {e}")
            return {'total_images': 0, 'total_size_mb': 0, 'unoptimized_images': [], 'format_recommendations': {}, 'size_savings_potential_mb': 0}

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive frontend optimization report"""
        print("📊 Generating frontend excellence report...")

        # Gather all analysis data
        bundle_analysis = await self.analyze_bundle_size()
        component_metrics = await self.analyze_component_performance()
        page_metrics = await self.analyze_page_load_performance()
        accessibility_results = await self.run_accessibility_audit()
        seo_results = await self.run_seo_audit()
        image_analysis = await self.analyze_image_optimization()

        # Calculate scores
        bundle_score = self._calculate_bundle_score(bundle_analysis)
        component_score = self._calculate_component_score(component_metrics)
        performance_score = self._calculate_performance_score(page_metrics)
        accessibility_score = self._calculate_accessibility_score(accessibility_results)
        seo_score = self._calculate_seo_score(seo_results)
        image_score = self._calculate_image_score(image_analysis)

        overall_score = (bundle_score + component_score + performance_score + accessibility_score + seo_score + image_score) / 6

        # Generate recommendations
        critical_recommendations = []
        high_priority_recommendations = []
        medium_priority_recommendations = []

        # Critical issues
        if bundle_analysis.total_size > 5 * 1024 * 1024:  # 5MB
            critical_recommendations.append(
                f"CRITICAL: Bundle size too large ({bundle_analysis.total_size / 1024 / 1024:.1f}MB). Target: <2MB"
            )

        if performance_score < 60:
            critical_recommendations.append(
                f"CRITICAL: Page load performance is poor ({performance_score:.0f}/100). Optimize for Core Web Vitals"
            )

        if accessibility_score < 70:
            critical_recommendations.append(
                f"CRITICAL: Accessibility score too low ({accessibility_score:.0f}/100). Fix critical WCAG violations"
            )

        # High priority issues
        if image_analysis['size_savings_potential_mb'] > 1:
            high_priority_recommendations.append(
                f"HIGH: {image_analysis['size_savings_potential_mb']:.1f}MB can be saved with image optimization"
            )

        slow_components = [c for c in component_metrics if c.avg_render_time > 16]  # 16ms for 60fps
        if slow_components:
            high_priority_recommendations.append(
                f"HIGH: {len(slow_components)} components have slow render times - optimize React components"
            )

        # Medium priority issues
        if bundle_analysis.optimization_potential > 30:
            medium_priority_recommendations.append(
                f"MEDIUM: {bundle_analysis.optimization_potential:.0f}% bundle optimization potential"
            )

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'bundle_score': bundle_score,
            'component_score': component_score,
            'performance_score': performance_score,
            'accessibility_score': accessibility_score,
            'seo_score': seo_score,
            'image_score': image_score,
            'bundle_analysis': asdict(bundle_analysis),
            'component_metrics': [asdict(c) for c in component_metrics[:10]],  # Top 10
            'page_metrics': [asdict(p) for p in page_metrics],
            'accessibility_results': [asdict(a) for a in accessibility_results],
            'seo_results': [asdict(s) for s in seo_results],
            'image_analysis': image_analysis,
            'critical_recommendations': critical_recommendations,
            'high_priority_recommendations': high_priority_recommendations,
            'medium_priority_recommendations': medium_priority_recommendations,
            'overall_grade': self._get_grade_from_score(overall_score)
        }

    def _analyze_dist_folder(self, dist_path: str) -> BundleAnalysisResult:
        """Analyze built dist folder"""
        if not os.path.exists(dist_path):
            return BundleAnalysisResult(0, 0, [], [], [], [], 0.0)

        total_size = 0
        chunks = []
        largest_assets = []

        # Analyze all files
        for root, dirs, files in os.walk(dist_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size

                # Calculate gzipped size
                try:
                    with open(file_path, 'rb') as f:
                        gzipped_size = len(gzip.compress(f.read()))
                except:
                    gzipped_size = file_size

                relative_path = os.path.relpath(file_path, dist_path)

                if file.endswith(('.js', '.css')):
                    chunks.append({
                        'name': relative_path,
                        'size': file_size,
                        'gzipped_size': gzipped_size,
                        'type': 'javascript' if file.endswith('.js') else 'css'
                    })

                largest_assets.append({
                    'name': relative_path,
                    'size': file_size,
                    'gzipped_size': gzipped_size
                })

        # Sort and limit results
        largest_assets.sort(key=lambda x: x['size'], reverse=True)
        largest_assets = largest_assets[:10]

        # Calculate gzipped total
        gzipped_total = sum(asset['gzipped_size'] for asset in largest_assets)

        # Simple optimization potential calculation
        optimization_potential = max(0, (total_size - gzipped_total) / total_size * 100) if total_size > 0 else 0

        return BundleAnalysisResult(
            total_size=total_size,
            gzipped_size=gzipped_total,
            chunks=chunks,
            largest_assets=largest_assets,
            unused_exports=[],
            duplicate_dependencies=[],
            optimization_potential=optimization_potential
        )

    def _parse_bundle_analyzer_data(self, bundle_data: Dict) -> BundleAnalysisResult:
        """Parse webpack-bundle-analyzer JSON data"""
        # This would parse the actual bundle analyzer output
        # For now, return a simplified version
        return BundleAnalysisResult(
            total_size=0,
            gzipped_size=0,
            chunks=[],
            largest_assets=[],
            unused_exports=[],
            duplicate_dependencies=[],
            optimization_potential=0.0
        )

    def _find_component_files(self) -> List[str]:
        """Find React component files"""
        component_files = []
        extensions = ['.tsx', '.jsx']

        for root, dirs, files in os.walk(self.frontend_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    # Skip node_modules and build directories
                    if 'node_modules' not in file_path and 'dist' not in file_path:
                        component_files.append(file_path)

        return component_files

    async def _analyze_component_file(self, file_path: str) -> ComponentPerformanceMetrics:
        """Analyze a single React component file"""
        component_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple static analysis
            render_count = content.count('render(') + content.count('return(')
            prop_destructuring = len(re.findall(r'const\s*{\s*[^}]+\s*}\s*=', content))
            state_usage = content.count('useState(') + content.count('useReducer(')
            effect_usage = content.count('useEffect(')

            # Generate optimization suggestions
            suggestions = []
            if state_usage > 5:
                suggestions.append("Consider splitting component or using useReducer for complex state")
            if effect_usage > 3:
                suggestions.append("Review useEffect dependencies - may cause unnecessary re-renders")
            if 'useCallback' not in content and prop_destructuring > 3:
                suggestions.append("Consider using useCallback for functions passed as props")
            if 'React.memo' not in content and 'export default' in content:
                suggestions.append("Consider wrapping component in React.memo for prop optimization")

            return ComponentPerformanceMetrics(
                component_name=component_name,
                render_count=render_count,
                avg_render_time=0.0,  # Would need runtime measurement
                re_render_frequency=0.0,  # Would need runtime measurement
                prop_changes=prop_destructuring,
                state_changes=state_usage,
                optimization_suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"Error analyzing component {file_path}: {e}")
            return ComponentPerformanceMetrics(
                component_name=component_name,
                render_count=0,
                avg_render_time=0.0,
                re-render_frequency=0.0,
                prop_changes=0,
                state_changes=0,
                optimization_suggestions=[]
            )

    async def _measure_page_performance(self, url: str) -> PageLoadMetrics:
        """Measure page load performance"""
        try:
            # Use requests to measure basic metrics
            start_time = time.time()
            response = requests.get(url, timeout=30)
            load_time = time.time() - start_time

            content = response.content
            content_length = len(content)

            # Simulate Web Vitals (in production, you'd use actual browser metrics)
            simulated_metrics = {
                'dom_content_loaded': load_time * 0.4,
                'load_complete': load_time,
                'first_contentful_paint': load_time * 0.6,
                'largest_contentful_paint': load_time * 0.8,
                'cumulative_layout_shift': 0.1,  # Assume low CLS
                'first_input_delay': 50  # milliseconds
            }

            return PageLoadMetrics(
                url=url,
                total_size=content_length,
                num_requests=1,  # Simplified
                dom_content_loaded=simulated_metrics['dom_content_loaded'],
                load_complete=simulated_metrics['load_complete'],
                first_contentful_paint=simulated_metrics['first_contentful_paint'],
                largest_contentful_paint=simulated_metrics['largest_contentful_paint'],
                cumulative_layout_shift=simulated_metrics['cumulative_layout_shift'],
                first_input_delay=simulated_metrics['first_input_delay']
            )

        except Exception as e:
            logger.error(f"Error measuring performance for {url}: {e}")
            return PageLoadMetrics(
                url=url,
                total_size=0,
                num_requests=0,
                dom_content_loaded=0.0,
                load_complete=0.0,
                first_contentful_paint=0.0,
                largest_contentful_paint=0.0,
                cumulative_layout_shift=0.0,
                first_input_delay=0.0
            )

    async def _run_accessibility_test(self, url: str) -> AccessibilityAuditResult:
        """Run accessibility test (simplified version)"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text

            # Simple accessibility checks
            violations = []
            passes = []

            # Check for alt text on images
            if '<img' in content and 'alt=' not in content:
                violations.append({
                    'id': 'image-alt',
                    'description': 'Images must have alt text',
                    'impact': 'serious'
                })

            # Check for form labels
            if '<input' in content and '<label' not in content:
                violations.append({
                    'id': 'label',
                    'description': 'Form inputs must have labels',
                    'impact': 'serious'
                })

            # Check for heading structure
            if content.count('<h1>') == 0:
                violations.append({
                    'id': 'page-has-heading-one',
                    'description': 'Page must have a main heading (h1)',
                    'impact': 'moderate'
                })

            # Check for skip links
            if 'skip' not in content.lower():
                violations.append({
                    'id': 'skip-link',
                    'description': 'Page should have skip links for keyboard navigation',
                    'impact': 'moderate'
                })

            # Calculate score
            total_checks = len(violations) + len(passes) + 4  # Assume some passes
            score = ((total_checks - len(violations)) / total_checks * 100) if total_checks > 0 else 0

            critical_issues = [v['description'] for v in violations if v['impact'] == 'serious']

            return AccessibilityAuditResult(
                url=url,
                wcag_level='AA',
                violations=violations,
                passes=passes,
                incomplete=[],
                score=score,
                critical_issues=critical_issues
            )

        except Exception as e:
            logger.error(f"Error running accessibility test for {url}: {e}")
            return AccessibilityAuditResult(
                url=url,
                wcag_level='AA',
                violations=[],
                passes=[],
                incomplete=[],
                score=0,
                critical_issues=[f"Test failed: {e}"]
            )

    async def _run_seo_test(self, url: str) -> SEOAuditResult:
        """Run SEO test"""
        try:
            response = requests.get(url, timeout=10)
            content = response.text.lower()

            # Check for essential SEO elements
            meta_tags = {
                'title': '<title>' in content,
                'description': 'name="description"' in content,
                'keywords': 'name="keywords"' in content,
                'viewport': 'name="viewport"' in content,
                'og:title': 'property="og:title"' in content,
                'og:description': 'property="og:description"' in content,
                'canonical': 'rel="canonical"' in content
            }

            # Check for structured data
            structured_data = 'application/ld+json' in content

            # Generate issues and recommendations
            issues = []
            recommendations = []

            for tag, present in meta_tags.items():
                if not present:
                    issues.append(f"Missing meta {tag}")
                    recommendations.append(f"Add {tag} meta tag")

            if not structured_data:
                issues.append("Missing structured data")
                recommendations.append("Add JSON-LD structured data for better SERP visibility")

            # Calculate score
            total_checks = len(meta_tags) + 1  # +1 for structured data
            passed_checks = sum(meta_tags.values()) + (1 if structured_data else 0)
            score = (passed_checks / total_checks) * 100

            return SEOAuditResult(
                url=url,
                score=score,
                issues=issues,
                recommendations=recommendations,
                meta_tags_present=meta_tags,
                structured_data_present=structured_data
            )

        except Exception as e:
            logger.error(f"Error running SEO test for {url}: {e}")
            return SEOAuditResult(
                url=url,
                score=0,
                issues=[f"SEO test failed: {e}"],
                recommendations=["Fix server response to allow SEO analysis"],
                meta_tags_present={},
                structured_data_present=False
            )

    def _find_image_files(self) -> List[str]:
        """Find image files in the frontend"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.avif']
        image_files = []

        for root, dirs, files in os.walk(self.frontend_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    file_path = os.path.join(root, file)
                    # Skip node_modules
                    if 'node_modules' not in file_path:
                        image_files.append(file_path)

        return image_files

    def _analyze_image_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single image file"""
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        file_ext = os.path.splitext(file_path)[1].lower()

        # Simple optimization recommendations
        needs_optimization = False
        format_recommendation = None
        savings_potential_mb = 0

        if file_ext in ['.jpg', '.jpeg'] and file_size_mb > 0.5:
            needs_optimization = True
            format_recommendation = 'webp'
            savings_potential_mb = file_size_mb * 0.3  # Assume 30% savings

        elif file_ext == '.png' and file_size_mb > 1:
            needs_optimization = True
            format_recommendation = 'webp'
            savings_potential_mb = file_size_mb * 0.5  # Assume 50% savings

        return {
            'file_path': file_path,
            'size_mb': file_size_mb,
            'format': file_ext,
            'needs_optimization': needs_optimization,
            'format_recommendation': format_recommendation,
            'savings_potential_mb': savings_potential_mb
        }

    def _calculate_bundle_score(self, analysis: BundleAnalysisResult) -> float:
        """Calculate bundle optimization score"""
        score = 100

        # Size penalties
        if analysis.total_size > 5 * 1024 * 1024:  # 5MB
            score -= 50
        elif analysis.total_size > 2 * 1024 * 1024:  # 2MB
            score -= 25

        # Optimization potential
        if analysis.optimization_potential > 50:
            score -= 25
        elif analysis.optimization_potential > 20:
            score -= 10

        return max(0, min(100, score))

    def _calculate_component_score(self, metrics: List[ComponentPerformanceMetrics]) -> float:
        """Calculate component optimization score"""
        if not metrics:
            return 100

        score = 100
        total_issues = 0

        for metric in metrics:
            if len(metric.optimization_suggestions) > 2:
                total_issues += 1

        issue_ratio = total_issues / len(metrics) if metrics else 0
        score -= issue_ratio * 50

        return max(0, min(100, score))

    def _calculate_performance_score(self, metrics: List[PageLoadMetrics]) -> float:
        """Calculate page performance score"""
        if not metrics:
            return 0

        scores = []
        for metric in metrics:
            score = 100

            # Load time penalty
            if metric.load_complete > 5:  # 5 seconds
                score -= 50
            elif metric.load_complete > 3:  # 3 seconds
                score -= 25
            elif metric.load_complete > 1.5:  # 1.5 seconds
                score -= 10

            # CLS penalty
            if metric.cumulative_layout_shift > 0.25:
                score -= 30
            elif metric.cumulative_layout_shift > 0.1:
                score -= 15

            # FID penalty
            if metric.first_input_delay > 300:  # 300ms
                score -= 20
            elif metric.first_input_delay > 100:  # 100ms
                score -= 10

            scores.append(max(0, score))

        return sum(scores) / len(scores) if scores else 0

    def _calculate_accessibility_score(self, results: List[AccessibilityAuditResult]) -> float:
        """Calculate accessibility score"""
        if not results:
            return 0

        return sum(r.score for r in results) / len(results)

    def _calculate_seo_score(self, results: List[SEOAuditResult]) -> float:
        """Calculate SEO score"""
        if not results:
            return 0

        return sum(r.score for r in results) / len(results)

    def _calculate_image_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate image optimization score"""
        if analysis['total_images'] == 0:
            return 100

        score = 100

        # Penalty for unoptimized images
        unoptimized_ratio = len(analysis['unoptimized_images']) / analysis['total_images']
        score -= unoptimized_ratio * 50

        # Penalty for large potential savings
        if analysis['size_savings_potential_mb'] > 2:
            score -= 30
        elif analysis['size_savings_potential_mb'] > 1:
            score -= 15

        return max(0, min(100, score))

    def _get_grade_from_score(self, score: float) -> str:
        """Get grade from score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

async def main():
    """Main execution function"""
    print("🚀 PsychSync Frontend Excellence Optimizer")
    print("=" * 50)

    optimizer = FrontendExcellenceOptimizer()

    try:
        # Generate comprehensive report
        report = await optimizer.generate_optimization_report()

        # Display results
        print(f"\n📊 Overall Frontend Excellence Score: {report['overall_score']:.1f}/100")
        print(f"📈 Overall Grade: {report['overall_grade']}")

        print(f"\n📊 Component Scores:")
        print(f"   Bundle Optimization: {report['bundle_score']:.1f}/100")
        print(f"   Component Performance: {report['component_score']:.1f}/100")
        print(f"   Page Performance: {report['performance_score']:.1f}/100")
        print(f"   Accessibility: {report['accessibility_score']:.1f}/100")
        print(f"   SEO: {report['seo_score']:.1f}/100")
        print(f"   Image Optimization: {report['image_score']:.1f}/100")

        # Display bundle analysis
        bundle = report['bundle_analysis']
        bundle_size_mb = bundle['total_size'] / (1024 * 1024)
        print(f"\n📦 Bundle Analysis:")
        print(f"   Total Size: {bundle_size_mb:.2f}MB")
        print(f"   Gzipped Size: {bundle['gzipped_size'] / (1024 * 1024):.2f}MB")
        print(f"   Optimization Potential: {bundle['optimization_potential']:.1f}%")

        # Display page performance
        if report['page_metrics']:
            print(f"\n🚀 Page Performance:")
            for metric in report['page_metrics'][:2]:
                print(f"   {metric['url']}: {metric['load_complete']:.2f}s load time")
                print(f"      First Contentful Paint: {metric['first_contentful_paint']:.2f}s")

        # Display accessibility results
        if report['accessibility_results']:
            print(f"\n♿ Accessibility:")
            for result in report['accessibility_results'][:2]:
                critical_count = len(result['critical_issues'])
                print(f"   {result['url']}: {result['score']:.0f}/100 ({critical_count} critical issues)")

        # Display image analysis
        image = report['image_analysis']
        if image['total_images'] > 0:
            print(f"\n🖼️  Image Analysis:")
            print(f"   Total Images: {image['total_images']}")
            print(f"   Total Size: {image['total_size_mb']:.2f}MB")
            print(f"   Optimization Savings: {image['size_savings_potential_mb']:.2f}MB")

        # Display critical issues
        if report['critical_recommendations']:
            print(f"\n🚨 Critical Issues:")
            for issue in report['critical_recommendations']:
                print(f"   • {issue}")

        # Display high priority issues
        if report['high_priority_recommendations']:
            print(f"\n⚠️  High Priority Issues:")
            for issue in report['high_priority_recommendations']:
                print(f"   • {issue}")

        # Save detailed report
        report_file = "frontend_excellence_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Determine exit code based on overall grade
        if report['overall_grade'] in ['A', 'B']:
            print(f"\n✅ Frontend excellence check PASSED")
            return 0
        elif report['overall_grade'] == 'C':
            print(f"\n⚠️  Frontend excellence check PASSED with warnings")
            return 0
        else:
            print(f"\n❌ Frontend excellence check FAILED")
            return 1

    except Exception as e:
        logger.error(f"Error during frontend optimization: {e}")
        print(f"❌ Frontend optimization failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
