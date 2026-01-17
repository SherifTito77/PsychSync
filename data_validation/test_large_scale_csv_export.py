#!/usr/bin/env python3
"""
Large-Scale CSV Export Testing Module
Tests exporting 10,000 user results to CSV with performance and accuracy validation
"""

import asyncio
import json
import time
import statistics
import csv
import io
import gzip
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import psutil
import os

# Import the scoring engine from previous tests
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_psychometric_scoring_consistency import (
    AssessmentType, AssessmentQuestion, AssessmentResponse, ScoringResult,
    PsychometricScoringEngine
)

class ExportFormat(Enum):
    """Different export formats to test"""
    CSV = "csv"
    CSV_GZIP = "csv_gzip"
    CSV_ZIP = "csv_zip"
    JSON = "json"

class ChunkSize(Enum):
    """Different chunk sizes for memory-efficient processing"""
    SMALL = 100      # 100 records per chunk
    MEDIUM = 500     # 500 records per chunk
    LARGE = 1000     # 1000 records per chunk
    EXTRA_LARGE = 2000 # 2000 records per chunk

@dataclass
class ExportConfiguration:
    """Configuration for export testing"""
    user_count: int
    export_format: ExportFormat
    chunk_size: ChunkSize
    include_headers: bool = True
    compression_level: int = 6
    parallel_processing: bool = False

@dataclass
class PerformanceMetrics:
    """Performance metrics for export operations"""
    total_time: float
    processing_rate: float  # records per second
    peak_memory_usage: float  # MB
    average_memory_usage: float  # MB
    cpu_usage: float  # percentage
    disk_io: Dict[str, float]  # read/write MB/s

@dataclass
class DataIntegrityResult:
    """Result of data integrity validation"""
    records_exported: int
    records_validated: int
    validation_errors: int
    data_accuracy: float  # percentage
    missing_fields: List[str]
    corrupted_records: int

@dataclass
class LargeScaleExportResult:
    """Result of large-scale export testing"""
    configuration: ExportConfiguration
    performance_metrics: PerformanceMetrics
    data_integrity: DataIntegrityResult
    file_size: int  # bytes
    compression_ratio: float
    success: bool
    error_details: List[str]

@dataclass
class ExportTestResult:
    """Overall export test result"""
    test_name: str
    assessment_type: str
    export_results: List[LargeScaleExportResult]
    best_performance: LargeScaleExportResult
    worst_performance: LargeScaleExportResult
    overall_success_rate: float
    recommendations: List[str]
    timestamp: datetime

class LargeScaleCSVExportTester:
    """Comprehensive testing suite for large-scale CSV export"""

    def __init__(self):
        self.engine = PsychometricScoringEngine()
        self.memory_baseline = self._get_memory_usage()
        self.performance_targets = {
            "min_processing_rate": 100,  # records per second
            "max_memory_usage": 1024,    # MB
            "max_cpu_usage": 80,         # percentage
            "min_data_accuracy": 99.9    # percentage
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    async def generate_large_dataset(self, assessment_type: AssessmentType,
                                   user_count: int) -> List[ScoringResult]:
        """Generate large dataset of assessment results"""
        print(f"Generating {user_count} assessment results for {assessment_type.value}...")
        results = []

        # Batch processing for memory efficiency
        batch_size = 100
        for batch_start in range(0, user_count, batch_size):
            batch_end = min(batch_start + batch_size, user_count)
            batch_results = []

            for user_id in range(batch_start, batch_end):
                # Generate responses with some variation
                questions = self.engine.question_banks[assessment_type]
                responses = []

                # Create user patterns for more realistic data
                user_pattern = user_id % 5
                for question in questions:
                    if user_pattern == 0:
                        # High achievers
                        answer_value = random.choice([4, 5, 5, 4, 3])
                    elif user_pattern == 1:
                        # Low achievers
                        answer_value = random.choice([1, 2, 1, 2, 3])
                    elif user_pattern == 2:
                        # Mixed but positive
                        answer_value = random.choice([3, 4, 4, 3, 2])
                    elif user_pattern == 3:
                        # Mixed but negative
                        answer_value = random.choice([2, 3, 2, 1, 2])
                    else:
                        # Random
                        answer_value = random.randint(1, 5)

                    response = AssessmentResponse(
                        question_id=question.id,
                        answer_value=answer_value,
                        response_time=random.uniform(1.0, 20.0),
                        timestamp=datetime.now() - timedelta(days=random.randint(1, 365))
                    )
                    responses.append(response)

                # Score the assessment
                result = await self.engine.score_assessment(assessment_type, responses)
                batch_results.append(result)

            results.extend(batch_results)

            # Progress indicator
            if batch_end % 1000 == 0 or batch_end == user_count:
                print(f"  Generated {batch_end}/{user_count} results")

        return results

    def _prepare_export_data(self, results: List[ScoringResult],
                           include_headers: bool = True) -> List[Dict[str, Any]]:
        """Prepare assessment results for export"""
        export_data = []

        for i, result in enumerate(results):
            row = {
                "user_id": f"user_{i+1:06d}",
                "assessment_type": result.assessment_type.value,
                "personality_type": result.personality_type or "N/A",
                "confidence_score": round(result.confidence_score, 2),
                "processing_time": round(result.processing_time, 3),
                "timestamp": datetime.now().isoformat()
            }

            # Add normalized scores
            for category, score in result.normalized_scores.items():
                row[f"score_{category.lower()}"] = round(score, 2)

            # Add percentiles (mock calculation)
            for category, score in result.normalized_scores.items():
                percentile = min(99, max(1, int(score * 0.99 + random.uniform(-5, 5))))
                row[f"percentile_{category.lower()}"] = percentile

            export_data.append(row)

        return export_data

    async def export_to_csv(self, data: List[Dict[str, Any]],
                          config: ExportConfiguration) -> LargeScaleExportResult:
        """Export data to CSV with specified configuration"""
        start_time = time.time()
        memory_readings = []
        cpu_readings = []

        # Start performance monitoring
        def monitor_performance():
            memory_readings.append(self._get_memory_usage())
            cpu_readings.append(self._get_cpu_usage())

        # Create CSV content
        csv_content = io.StringIO()

        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(csv_content, fieldnames=fieldnames)

            if config.include_headers:
                writer.writeheader()

            # Process in chunks for memory efficiency
            chunk_size = config.chunk_size.value
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                writer.writerows(chunk)

                # Monitor performance after each chunk
                monitor_performance()

        csv_bytes = csv_content.getvalue().encode('utf-8')

        # Apply compression if needed
        if config.export_format == ExportFormat.CSV_GZIP:
            compressed_content = gzip.compress(csv_bytes, compresslevel=config.compression_level)
            file_content = compressed_content
        elif config.export_format == ExportFormat.CSV_ZIP:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr("assessment_results.csv", csv_bytes)
            file_content = zip_buffer.getvalue()
        else:
            file_content = csv_bytes

        # Calculate performance metrics
        total_time = time.time() - start_time
        processing_rate = len(data) / total_time if total_time > 0 else 0
        peak_memory = max(memory_readings) if memory_readings else self.memory_baseline
        avg_memory = statistics.mean(memory_readings) if memory_readings else self.memory_baseline
        avg_cpu = statistics.mean(cpu_readings) if cpu_readings else 0

        # Calculate compression ratio
        original_size = len(csv_bytes)
        compressed_size = len(file_content)
        compression_ratio = compressed_size / original_size if original_size > 0 else 1

        # Validate data integrity
        integrity_result = await self._validate_export_integrity(
            data, file_content, config
        )

        # Check success criteria
        success = (
            integrity_result.data_accuracy >= self.performance_targets["min_data_accuracy"] and
            processing_rate >= self.performance_targets["min_processing_rate"] and
            peak_memory <= self.performance_targets["max_memory_usage"]
        )

        # Generate error details if any
        error_details = []
        if integrity_result.validation_errors > 0:
            error_details.append(f"Found {integrity_result.validation_errors} validation errors")
        if processing_rate < self.performance_targets["min_processing_rate"]:
            error_details.append(f"Processing rate {processing_rate:.1f} below target {self.performance_targets['min_processing_rate']}")
        if peak_memory > self.performance_targets["max_memory_usage"]:
            error_details.append(f"Peak memory {peak_memory:.1f}MB exceeds limit {self.performance_targets['max_memory_usage']}MB")

        performance_metrics = PerformanceMetrics(
            total_time=total_time,
            processing_rate=processing_rate,
            peak_memory_usage=peak_memory,
            average_memory_usage=avg_memory,
            cpu_usage=avg_cpu,
            disk_io={
                "write_speed": len(file_content) / (1024 * 1024) / total_time if total_time > 0 else 0
            }
        )

        return LargeScaleExportResult(
            configuration=config,
            performance_metrics=performance_metrics,
            data_integrity=integrity_result,
            file_size=len(file_content),
            compression_ratio=compression_ratio,
            success=success,
            error_details=error_details
        )

    async def _validate_export_integrity(self, original_data: List[Dict[str, Any]],
                                       exported_content: bytes,
                                       config: ExportConfiguration) -> DataIntegrityResult:
        """Validate data integrity of exported content"""
        try:
            # Decompress if needed
            if config.export_format == ExportFormat.CSV_GZIP:
                content = gzip.decompress(exported_content).decode('utf-8')
            elif config.export_format == ExportFormat.CSV_ZIP:
                zip_buffer = io.BytesIO(exported_content)
                with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                    content = zip_file.read("assessment_results.csv").decode('utf-8')
            else:
                content = exported_content.decode('utf-8')

            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(content))
            exported_data = list(csv_reader)

            # Validate record count
            records_exported = len(exported_data)
            records_validated = 0
            validation_errors = 0
            missing_fields = []
            corrupted_records = 0

            expected_fields = set(original_data[0].keys()) if original_data else set()

            # Validate each record
            for i, (original, exported) in enumerate(zip(original_data, exported_data)):
                try:
                    # Check for missing fields
                    exported_fields = set(exported.keys())
                    missing = expected_fields - exported_fields
                    if missing:
                        missing_fields.extend(list(missing))
                        validation_errors += 1

                    # Validate numeric fields
                    numeric_fields = ['confidence_score', 'processing_time']
                    for field in numeric_fields:
                        if field in exported and field in original:
                            try:
                                original_val = float(original[field])
                                exported_val = float(exported[field])
                                # Allow small rounding differences
                                if abs(original_val - exported_val) > 0.01:
                                    validation_errors += 1
                            except (ValueError, TypeError):
                                validation_errors += 1

                    records_validated += 1

                except Exception as e:
                    corrupted_records += 1
                    validation_errors += 1

            # Calculate data accuracy
            if records_exported > 0:
                data_accuracy = ((records_validated - validation_errors) / records_exported) * 100
            else:
                data_accuracy = 0

            return DataIntegrityResult(
                records_exported=records_exported,
                records_validated=records_validated,
                validation_errors=validation_errors,
                data_accuracy=data_accuracy,
                missing_fields=list(set(missing_fields)),
                corrupted_records=corrupted_records
            )

        except Exception as e:
            return DataIntegrityResult(
                records_exported=0,
                records_validated=0,
                validation_errors=1,
                data_accuracy=0,
                missing_fields=[],
                corrupted_records=len(original_data)
            )

    async def test_large_scale_export(self, assessment_type: AssessmentType,
                                    user_count: int = 10000) -> List[LargeScaleExportResult]:
        """Test large-scale export with different configurations"""
        print(f"Testing large-scale export for {assessment_type.value} with {user_count} users...")

        # Generate test data
        assessment_results = await self.generate_large_dataset(assessment_type, user_count)
        export_data = self._prepare_export_data(assessment_results)

        # Test different export configurations
        test_configs = [
            # Standard CSV
            ExportConfiguration(
                user_count=user_count,
                export_format=ExportFormat.CSV,
                chunk_size=ChunkSize.MEDIUM
            ),
            # CSV with GZIP compression
            ExportConfiguration(
                user_count=user_count,
                export_format=ExportFormat.CSV_GZIP,
                chunk_size=ChunkSize.LARGE,
                compression_level=6
            ),
            # CSV with ZIP compression
            ExportConfiguration(
                user_count=user_count,
                export_format=ExportFormat.CSV_ZIP,
                chunk_size=ChunkSize.LARGE
            ),
            # Small chunk size for memory efficiency
            ExportConfiguration(
                user_count=user_count,
                export_format=ExportFormat.CSV,
                chunk_size=ChunkSize.SMALL
            ),
            # Large chunk size for speed
            ExportConfiguration(
                user_count=user_count,
                export_format=ExportFormat.CSV,
                chunk_size=ChunkSize.EXTRA_LARGE
            )
        ]

        export_results = []

        for i, config in enumerate(test_configs):
            print(f"  Testing configuration {i+1}/{len(test_configs)}: {config.export_format.value} "
                  f"with {config.chunk_size.value} record chunks...")

            result = await self.export_to_csv(export_data, config)
            export_results.append(result)

            # Print quick status
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            print(f"    {status} - {result.performance_metrics.processing_rate:.1f} records/sec, "
                  f"{result.performance_metrics.peak_memory_usage:.1f}MB memory")

        return export_results

    def analyze_export_performance(self, export_results: List[LargeScaleExportResult]) -> Dict[str, Any]:
        """Analyze export performance across different configurations"""
        if not export_results:
            return {}

        # Find best and worst performance
        best_result = max(export_results, key=lambda r: r.performance_metrics.processing_rate)
        worst_result = min(export_results, key=lambda r: r.performance_metrics.processing_rate)

        # Calculate statistics
        processing_rates = [r.performance_metrics.processing_rate for r in export_results]
        memory_usage = [r.performance_metrics.peak_memory_usage for r in export_results]
        file_sizes = [r.file_size for r in export_results]
        data_accuracies = [r.data_integrity.data_accuracy for r in export_results]

        # Compression analysis
        csv_results = [r for r in export_results if r.configuration.export_format == ExportFormat.CSV]
        compressed_results = [r for r in export_results if r.configuration.export_format in [ExportFormat.CSV_GZIP, ExportFormat.CSV_ZIP]]

        return {
            "performance_summary": {
                "avg_processing_rate": statistics.mean(processing_rates),
                "max_processing_rate": max(processing_rates),
                "min_processing_rate": min(processing_rates),
                "avg_memory_usage": statistics.mean(memory_usage),
                "max_memory_usage": max(memory_usage),
                "min_memory_usage": min(memory_usage),
                "avg_file_size": statistics.mean(file_sizes),
                "avg_data_accuracy": statistics.mean(data_accuracies)
            },
            "compression_analysis": {
                "uncompressed_avg_size": statistics.mean([r.file_size for r in csv_results]) if csv_results else 0,
                "compressed_avg_size": statistics.mean([r.file_size for r in compressed_results]) if compressed_results else 0,
                "avg_compression_ratio": statistics.mean([r.compression_ratio for r in compressed_results]) if compressed_results else 1,
                "space_savings_percent": (1 - statistics.mean([r.compression_ratio for r in compressed_results])) * 100 if compressed_results else 0
            },
            "best_performance": {
                "processing_rate": best_result.performance_metrics.processing_rate,
                "memory_usage": best_result.performance_metrics.peak_memory_usage,
                "config": f"{best_result.configuration.export_format.value}_{best_result.configuration.chunk_size.value}"
            },
            "worst_performance": {
                "processing_rate": worst_result.performance_metrics.processing_rate,
                "memory_usage": worst_result.performance_metrics.peak_memory_usage,
                "config": f"{worst_result.configuration.export_format.value}_{worst_result.configuration.chunk_size.value}"
            }
        }

    async def run_comprehensive_export_tests(self) -> Dict[str, Any]:
        """Run comprehensive large-scale export tests"""
        print("📊 LARGE-SCALE CSV EXPORT TESTING")
        print("=" * 80)

        assessment_types = [AssessmentType.BIG_FIVE, AssessmentType.MBTI]
        test_results = []

        for assessment_type in assessment_types:
            print(f"\n🔍 Testing {assessment_type.value} assessment export...")

            # Test with 10,000 users
            results = await self.test_large_scale_export(assessment_type, user_count=10000)

            # Analyze performance
            performance_analysis = self.analyze_export_performance(results)

            # Create test result
            best_result = max(results, key=lambda r: r.performance_metrics.processing_rate)
            worst_result = min(results, key=lambda r: r.performance_metrics.processing_rate)
            success_rate = sum(1 for r in results if r.success) / len(results) * 100

            # Generate recommendations
            recommendations = []
            if success_rate < 80:
                recommendations.append("Low success rate - review export configuration and memory management")

            avg_processing_rate = performance_analysis["performance_summary"]["avg_processing_rate"]
            if avg_processing_rate < self.performance_targets["min_processing_rate"]:
                recommendations.append("Processing speed below target - optimize chunking and compression")

            avg_memory = performance_analysis["performance_summary"]["avg_memory_usage"]
            if avg_memory > self.performance_targets["max_memory_usage"]:
                recommendations.append("High memory usage - reduce chunk size or implement streaming")

            avg_accuracy = performance_analysis["performance_summary"]["avg_data_accuracy"]
            if avg_accuracy < self.performance_targets["min_data_accuracy"]:
                recommendations.append("Data accuracy below target - review export validation logic")

            # Compression recommendations
            compression_analysis = performance_analysis["compression_analysis"]
            if compression_analysis["space_savings_percent"] > 50:
                recommendations.append("Good compression achieved - consider using compression for large exports")

            if not recommendations:
                recommendations.append("Export performance meets all targets - system ready for production")

            test_result = ExportTestResult(
                test_name="large_scale_csv_export",
                assessment_type=assessment_type.value,
                export_results=results,
                best_performance=best_result,
                worst_performance=worst_result,
                overall_success_rate=success_rate,
                recommendations=recommendations,
                timestamp=datetime.now()
            )

            test_results.append(test_result)

        # Calculate overall metrics
        overall_success_rate = statistics.mean([r.overall_success_rate for r in test_results])
        total_users_exported = sum(len(r.export_results[0].configuration.user_count * [r.export_results[0].configuration.user_count]) for r in test_results)
        avg_processing_rate = statistics.mean([r.best_performance.performance_metrics.processing_rate for r in test_results])

        # Generate comprehensive report
        report = {
            "test_summary": {
                "total_assessments_tested": len(test_results),
                "overall_success_rate": overall_success_rate,
                "total_users_exported": 10000 * len(test_results),
                "avg_processing_rate": avg_processing_rate,
                "target_processing_rate": self.performance_targets["min_processing_rate"],
                "meets_targets": overall_success_rate >= 80 and avg_processing_rate >= self.performance_targets["min_processing_rate"]
            },
            "assessment_results": [
                {
                    "assessment_type": result.assessment_type,
                    "success_rate": result.overall_success_rate,
                    "best_performance": {
                        "processing_rate": result.best_performance.performance_metrics.processing_rate,
                        "memory_usage": result.best_performance.performance_metrics.peak_memory_usage,
                        "config": result.best_performance.configuration.export_format.value
                    },
                    "worst_performance": {
                        "processing_rate": result.worst_performance.performance_metrics.processing_rate,
                        "memory_usage": result.worst_performance.performance_metrics.peak_memory_usage
                    },
                    "recommendations": result.recommendations
                }
                for result in test_results
            ],
            "performance_analysis": {
                result.assessment_type: self.analyze_export_performance(result.export_results)
                for result in test_results
            },
            "recommendations": self._generate_overall_export_recommendations(test_results)
        }

        return report

    def _generate_overall_export_recommendations(self, test_results: List[ExportTestResult]) -> List[str]:
        """Generate overall export recommendations"""
        recommendations = []

        # Overall performance analysis
        avg_success_rate = statistics.mean([r.overall_success_rate for r in test_results])
        avg_processing_rate = statistics.mean([r.best_performance.performance_metrics.processing_rate for r in test_results])

        if avg_success_rate < 90:
            recommendations.append("Improve overall export reliability - target 95%+ success rate")

        if avg_processing_rate < 200:  # Target 200+ records/second
            recommendations.append("Optimize export performance - target 200+ records/second")

        # Memory usage recommendations
        max_memory = max([r.best_performance.performance_metrics.peak_memory_usage for r in test_results])
        if max_memory > 512:  # 512MB threshold
            recommendations.append("Implement memory-efficient streaming for very large exports")

        # Compression recommendations
        all_configs = []
        for result in test_results:
            all_configs.extend(result.export_results)

        compressed_configs = [c for c in all_configs if c.configuration.export_format in [ExportFormat.CSV_GZIP, ExportFormat.CSV_ZIP]]
        if compressed_configs:
            avg_compression = statistics.mean([c.compression_ratio for c in compressed_configs])
            if avg_compression < 0.3:  # Less than 30% of original size
                recommendations.append("Compression highly effective - recommend for all large exports")

        # Configuration recommendations
        best_configs = [r.best_performance.configuration for r in test_results]
        csv_configs = [c for c in best_configs if c.export_format == ExportFormat.CSV]
        if csv_configs:
            best_chunk_size = statistics.mode([c.chunk_size for c in csv_configs])
            recommendations.append(f"Optimal chunk size appears to be {best_chunk_size.value} records")

        # Data integrity recommendations
        min_accuracy = min([r.best_performance.data_integrity.data_accuracy for r in test_results])
        if min_accuracy < 99.5:
            recommendations.append("Improve data validation to ensure 99.5%+ accuracy")

        if not recommendations:
            recommendations.append("Large-scale export system meets all performance and quality targets")

        return recommendations

async def main():
    """Main function to run large-scale CSV export tests"""
    tester = LargeScaleCSVExportTester()

    # Run comprehensive tests
    results = await tester.run_comprehensive_export_tests()

    # Print summary
    print(f"\n{'='*80}")
    print("LARGE-SCALE CSV EXPORT TEST RESULTS")
    print(f"{'='*80}")

    summary = results["test_summary"]
    print(f"Assessments Tested: {summary['total_assessments_tested']}")
    print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
    print(f"Total Users Exported: {summary['total_users_exported']:,}")
    print(f"Average Processing Rate: {summary['avg_processing_rate']:.1f} records/second")
    print(f"Target Processing Rate: {summary['target_processing_rate']} records/second")
    print(f"Meets Targets: {'✅ YES' if summary['meets_targets'] else '❌ NO'}")

    print(f"\nPer Assessment Results:")
    for result in results["assessment_results"]:
        print(f"  📊 {result['assessment_type'].upper()}:")
        print(f"     Success Rate: {result['success_rate']:.1f}%")
        print(f"     Best Performance: {result['best_performance']['processing_rate']:.1f} records/sec")
        print(f"     Best Config: {result['best_performance']['config']}")
        print(f"     Memory Usage: {result['best_performance']['memory_usage']:.1f}MB")

    print(f"\nPerformance Analysis:")
    for assessment, analysis in results["performance_analysis"].items():
        if "performance_summary" in analysis:
            perf = analysis["performance_summary"]
            print(f"  🔍 {assessment.upper()}:")
            print(f"     Avg Processing Rate: {perf['avg_processing_rate']:.1f} records/sec")
            print(f"     Max Processing Rate: {perf['max_processing_rate']:.1f} records/sec")
            print(f"     Avg Memory Usage: {perf['avg_memory_usage']:.1f}MB")
            print(f"     Data Accuracy: {perf['avg_data_accuracy']:.2f}%")

    print(f"\nRecommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"large_scale_csv_export_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())
