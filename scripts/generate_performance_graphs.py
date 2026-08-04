#!/usr/bin/env python3
"""
Performance Graphs Generation Script
Creates visualizations from load test and performance data
"""

import argparse
import json
import os
import warnings
from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Suppress matplotlib warnings
warnings.filterwarnings("ignore")

# Set style
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")


class PerformanceGraphGenerator:
    """Generate comprehensive performance graphs"""

    def __init__(self, output_dir: str = "performance_graphs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Configure matplotlib for better output
        plt.rcParams["figure.figsize"] = (12, 8)
        plt.rcParams["font.size"] = 10
        plt.rcParams["axes.titlesize"] = 14
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["xtick.labelsize"] = 10
        plt.rcParams["ytick.labelsize"] = 10
        plt.rcParams["legend.fontsize"] = 10

    def load_locust_data(self, csv_file: str) -> pd.DataFrame:
        """Load Locust CSV data"""
        try:
            df = pd.read_csv(csv_file)
            print(f"✅ Loaded Locust data: {len(df)} records")
            return df
        except Exception as e:
            print(f"❌ Error loading Locust data: {e}")
            return pd.DataFrame()

    def generate_response_time_graph(self, df: pd.DataFrame):
        """Generate response time analysis graphs"""
        if df.empty:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Response Time Analysis", fontsize=16, fontweight="bold")

        # Response Time Over Time
        axes[0, 0].plot(
            df["Timestamp"],
            df["Average Response Time"],
            linewidth=2,
            alpha=0.8,
            color="blue",
        )
        axes[0, 0].fill_between(
            df["Timestamp"], df["Average Response Time"], alpha=0.3, color="blue"
        )
        axes[0, 0].set_title("Average Response Time Over Time")
        axes[0, 0].set_xlabel("Timestamp")
        axes[0, 0].set_ylabel("Response Time (ms)")
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].tick_params(axis="x", rotation=45)

        # Response Time Distribution
        if "95%" in df.columns and "99%" in df.columns:
            axes[0, 1].plot(
                df["Timestamp"], df["95%"], label="95th Percentile", linewidth=2
            )
            axes[0, 1].plot(
                df["Timestamp"], df["99%"], label="99th Percentile", linewidth=2
            )
            axes[0, 1].plot(
                df["Timestamp"],
                df["Average Response Time"],
                label="Average",
                linewidth=2,
                alpha=0.8,
            )
            axes[0, 1].set_title("Response Time Percentiles")
            axes[0, 1].set_xlabel("Timestamp")
            axes[0, 1].set_ylabel("Response Time (ms)")
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis="x", rotation=45)

        # Response Time Histogram
        axes[1, 0].hist(
            df["Average Response Time"],
            bins=30,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
        )
        axes[1, 0].axvline(
            df["Average Response Time"].mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {df['Average Response Time'].mean():.2f}ms",
        )
        axes[1, 0].set_title("Response Time Distribution")
        axes[1, 0].set_xlabel("Response Time (ms)")
        axes[1, 0].set_ylabel("Frequency")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Response Time vs RPS
        if "Requests/s" in df.columns:
            scatter = axes[1, 1].scatter(
                df["Requests/s"],
                df["Average Response Time"],
                alpha=0.6,
                s=30,
                c=df["User Count"],
                cmap="viridis",
            )
            axes[1, 1].set_title("Response Time vs Requests per Second")
            axes[1, 1].set_xlabel("Requests per Second")
            axes[1, 1].set_ylabel("Average Response Time (ms)")
            plt.colorbar(scatter, ax=axes[1, 1], label="User Count")
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/response_time_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        print("📊 Response time analysis graph saved")

    def generate_throughput_graph(self, df: pd.DataFrame):
        """Generate throughput analysis graphs"""
        if df.empty:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Throughput Analysis", fontsize=16, fontweight="bold")

        # Requests per Second Over Time
        if "Requests/s" in df.columns:
            axes[0, 0].plot(
                df["Timestamp"], df["Requests/s"], linewidth=2, alpha=0.8, color="green"
            )
            axes[0, 0].fill_between(
                df["Timestamp"], df["Requests/s"], alpha=0.3, color="green"
            )
            axes[0, 0].set_title("Requests per Second Over Time")
            axes[0, 0].set_xlabel("Timestamp")
            axes[0, 0].set_ylabel("Requests per Second")
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].tick_params(axis="x", rotation=45)

        # Total Requests Over Time
        if "Total Requests" in df.columns:
            axes[0, 1].plot(
                df["Timestamp"],
                df["Total Requests"],
                linewidth=2,
                alpha=0.8,
                color="orange",
            )
            axes[0, 1].set_title("Cumulative Requests Over Time")
            axes[0, 1].set_xlabel("Timestamp")
            axes[0, 1].set_ylabel("Total Requests")
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis="x", rotation=45)

        # Throughput vs User Count
        if "User Count" in df.columns and "Requests/s" in df.columns:
            axes[1, 0].scatter(
                df["User Count"], df["Requests/s"], alpha=0.7, s=40, color="purple"
            )

            # Add trend line
            z = np.polyfit(df["User Count"], df["Requests/s"], 1)
            p = np.poly1d(z)
            axes[1, 0].plot(
                df["User Count"].sort_values(),
                p(df["User Count"].sort_values()),
                "r--",
                alpha=0.8,
                linewidth=2,
            )

            axes[1, 0].set_title("Throughput vs User Count")
            axes[1, 0].set_xlabel("User Count")
            axes[1, 0].set_ylabel("Requests per Second")
            axes[1, 0].grid(True, alpha=0.3)

        # Failures Over Time
        if "Failures/s" in df.columns:
            axes[1, 1].plot(
                df["Timestamp"], df["Failures/s"], linewidth=2, alpha=0.8, color="red"
            )
            axes[1, 1].set_title("Failures per Second Over Time")
            axes[1, 1].set_xlabel("Timestamp")
            axes[1, 1].set_ylabel("Failures per Second")
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/throughput_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        print("📊 Throughput analysis graph saved")

    def generate_error_analysis_graph(self, df: pd.DataFrame):
        """Generate error analysis graphs"""
        if df.empty:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Error Analysis", fontsize=16, fontweight="bold")

        # Error Rate Over Time
        if "Error Count" in df.columns and "Total Requests" in df.columns:
            error_rate = (df["Error Count"] / df["Total Requests"] * 100).fillna(0)
            axes[0, 0].plot(
                df["Timestamp"], error_rate, linewidth=2, alpha=0.8, color="red"
            )
            axes[0, 0].fill_between(df["Timestamp"], error_rate, alpha=0.3, color="red")
            axes[0, 0].set_title("Error Rate Over Time")
            axes[0, 0].set_xlabel("Timestamp")
            axes[0, 0].set_ylabel("Error Rate (%)")
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].tick_params(axis="x", rotation=45)

        # Success Rate Over Time
        if "Total Requests" in df.columns and "Error Count" in df.columns:
            success_rate = (
                (df["Total Requests"] - df["Error Count"]) / df["Total Requests"] * 100
            ).fillna(100)
            axes[0, 1].plot(
                df["Timestamp"], success_rate, linewidth=2, alpha=0.8, color="green"
            )
            axes[0, 1].fill_between(
                df["Timestamp"], success_rate, alpha=0.3, color="green"
            )
            axes[0, 1].set_title("Success Rate Over Time")
            axes[0, 1].set_xlabel("Timestamp")
            axes[0, 1].set_ylabel("Success Rate (%)")
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].tick_params(axis="x", rotation=45)

        # Error Distribution
        if "Error Count" in df.columns:
            axes[1, 0].bar(range(len(df)), df["Error Count"], alpha=0.7, color="red")
            axes[1, 0].set_title("Error Count Distribution")
            axes[1, 0].set_xlabel("Time Period")
            axes[1, 0].set_ylabel("Error Count")
            axes[1, 0].grid(True, alpha=0.3)

        # Response Time with Error Overlay
        if "Error Count" in df.columns:
            ax2 = axes[1, 1].twinx()

            # Plot response time
            line1 = axes[1, 1].plot(
                df["Timestamp"],
                df["Average Response Time"],
                "b-",
                label="Response Time",
                linewidth=2,
                alpha=0.8,
            )
            axes[1, 1].set_xlabel("Timestamp")
            axes[1, 1].set_ylabel("Response Time (ms)", color="b")
            axes[1, 1].tick_params(axis="y", labelcolor="b")
            axes[1, 1].tick_params(axis="x", rotation=45)

            # Plot error count on secondary axis
            line2 = ax2.plot(
                df["Timestamp"],
                df["Error Count"],
                "r-",
                label="Error Count",
                linewidth=2,
                alpha=0.8,
            )
            ax2.set_ylabel("Error Count", color="r")
            ax2.tick_params(axis="y", labelcolor="r")

            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            axes[1, 1].legend(lines, labels, loc="upper left")
            axes[1, 1].set_title("Response Time vs Error Count")
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/error_analysis.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        print("📊 Error analysis graph saved")

    def generate_performance_summary_graph(self, df: pd.DataFrame):
        """Generate performance summary dashboard"""
        if df.empty:
            return

        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        fig.suptitle(
            "Performance Test Summary Dashboard", fontsize=18, fontweight="bold"
        )

        # Key Metrics
        avg_response_time = df["Average Response Time"].mean()
        max_response_time = df["Average Response Time"].max()
        total_requests = (
            df["Total Requests"].iloc[-1] if "Total Requests" in df.columns else 0
        )
        total_errors = df["Error Count"].sum() if "Error Count" in df.columns else 0
        avg_rps = df["Requests/s"].mean() if "Requests/s" in df.columns else 0

        # Summary Metrics Box
        ax_metrics = fig.add_subplot(gs[0, 0])
        ax_metrics.axis("off")
        metrics_text = f"""
        Performance Metrics Summary
        ─────────────────────
        Avg Response Time: {avg_response_time:.2f}ms
        Max Response Time: {max_response_time:.2f}ms
        Total Requests: {total_requests:,}
        Total Errors: {total_errors:,}
        Avg Throughput: {avg_rps:.1f} RPS
        Error Rate: {(total_errors/total_requests*100):.2f}%
        """
        ax_metrics.text(
            0.1,
            0.5,
            metrics_text,
            fontsize=12,
            verticalalignment="center",
            family="monospace",
        )

        # Response Time Trend
        ax_response = fig.add_subplot(gs[0, 1:])
        ax_response.plot(
            df["Timestamp"],
            df["Average Response Time"],
            linewidth=2,
            color="blue",
            alpha=0.8,
        )
        ax_response.fill_between(
            df["Timestamp"], df["Average Response Time"], alpha=0.3, color="blue"
        )
        ax_response.set_title("Response Time Trend")
        ax_response.set_xlabel("Time")
        ax_response.set_ylabel("Response Time (ms)")
        ax_response.tick_params(axis="x", rotation=45)
        ax_response.grid(True, alpha=0.3)

        # Throughput Trend
        if "Requests/s" in df.columns:
            ax_throughput = fig.add_subplot(gs[1, :2])
            ax_throughput.plot(
                df["Timestamp"], df["Requests/s"], linewidth=2, color="green", alpha=0.8
            )
            ax_throughput.fill_between(
                df["Timestamp"], df["Requests/s"], alpha=0.3, color="green"
            )
            ax_throughput.set_title("Throughput Trend")
            ax_throughput.set_xlabel("Time")
            ax_throughput.set_ylabel("Requests per Second")
            ax_throughput.tick_params(axis="x", rotation=45)
            ax_throughput.grid(True, alpha=0.3)

        # Error Rate
        if "Error Count" in df.columns and "Total Requests" in df.columns:
            ax_errors = fig.add_subplot(gs[1, 2])
            error_rate = (df["Error Count"] / df["Total Requests"] * 100).fillna(0)
            ax_errors.plot(
                df["Timestamp"], error_rate, linewidth=2, color="red", alpha=0.8
            )
            ax_errors.fill_between(df["Timestamp"], error_rate, alpha=0.3, color="red")
            ax_errors.set_title("Error Rate")
            ax_errors.set_xlabel("Time")
            ax_errors.set_ylabel("Error Rate (%)")
            ax_errors.tick_params(axis="x", rotation=45)
            ax_errors.grid(True, alpha=0.3)

        # Response Time Distribution
        ax_hist = fig.add_subplot(gs[2, 0])
        ax_hist.hist(
            df["Average Response Time"],
            bins=20,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
        )
        ax_hist.axvline(
            avg_response_time,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {avg_response_time:.2f}ms",
        )
        ax_hist.set_title("Response Time Distribution")
        ax_hist.set_xlabel("Response Time (ms)")
        ax_hist.set_ylabel("Frequency")
        ax_hist.legend()
        ax_hist.grid(True, alpha=0.3)

        # Performance Heatmap
        if "User Count" in df.columns and "Requests/s" in df.columns:
            ax_heatmap = fig.add_subplot(gs[2, 1:])

            # Create bins for heatmap
            user_bins = pd.cut(df["User Count"], bins=10)
            rps_bins = pd.cut(df["Requests/s"], bins=10)

            heatmap_data = (
                df.groupby([user_bins, rps_bins])["Average Response Time"]
                .mean()
                .unstack()
            )

            sns.heatmap(
                heatmap_data,
                annot=True,
                fmt=".1f",
                cmap="YlOrRd",
                ax=ax_heatmap,
                cbar_kws={"label": "Response Time (ms)"},
            )
            ax_heatmap.set_title("Response Time Heatmap (Users vs Throughput)")
            ax_heatmap.set_xlabel("Requests per Second")
            ax_heatmap.set_ylabel("User Count")

        plt.savefig(
            f"{self.output_dir}/performance_summary_dashboard.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        print("📊 Performance summary dashboard saved")

    def generate_from_json_report(self, json_file: str):
        """Generate graphs from JSON performance report"""
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            print(f"✅ Loaded JSON performance report")

            # Generate graphs based on available data
            if "query_performance" in data:
                self._generate_query_performance_graph(data["query_performance"])

            if "concurrent_access" in data:
                self._generate_concurrent_access_graph(data["concurrent_access"])

            if "write_performance" in data:
                self._generate_write_performance_graph(data["write_performance"])

        except Exception as e:
            print(f"❌ Error loading JSON report: {e}")

    def _generate_query_performance_graph(self, query_data: List[Dict]):
        """Generate query performance graphs from JSON data"""
        if not query_data:
            return

        df = pd.DataFrame(query_data)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            "Database Query Performance Analysis", fontsize=16, fontweight="bold"
        )

        # Query Response Times
        response_times = [q["avg_time_ms"] for q in query_data]
        query_names = [
            (
                q["description"][:30] + "..."
                if len(q["description"]) > 30
                else q["description"]
            )
            for q in query_data
        ]

        axes[0, 0].barh(query_names, response_times, alpha=0.7, color="steelblue")
        axes[0, 0].set_title("Average Query Response Times")
        axes[0, 0].set_xlabel("Response Time (ms)")
        axes[0, 0].tick_params(axis="y", rotation=0)

        # Query Performance Comparison
        metrics = ["avg_time_ms", "p95_time_ms", "p99_time_ms"]
        for metric in metrics:
            if all(metric in q for q in query_data):
                values = [q[metric] for q in query_data]
                axes[0, 1].plot(
                    values,
                    label=metric.replace("_", " ").title(),
                    linewidth=2,
                    marker="o",
                )

        axes[0, 1].set_title("Query Performance Metrics")
        axes[0, 1].set_xlabel("Query Index")
        axes[0, 1].set_ylabel("Response Time (ms)")
        axes[0, 1].legend()
        axes[0, 1].set_xticks(range(len(query_data)))
        axes[0, 1].grid(True, alpha=0.3)

        # Performance Variability
        if "std_dev_ms" in query_data[0]:
            std_devs = [q["std_dev_ms"] for q in query_data]
            axes[1, 0].bar(range(len(query_data)), std_devs, alpha=0.7, color="orange")
            axes[1, 0].set_title("Query Performance Variability (Std Dev)")
            axes[1, 0].set_xlabel("Query Index")
            axes[1, 0].set_ylabel("Standard Deviation (ms)")
            axes[1, 0].set_xticks(range(len(query_data)))
            axes[1, 0].grid(True, alpha=0.3)

        # Performance Ranking
        performance_score = []
        for q in query_data:
            # Simple scoring: lower avg_time and std_dev is better
            score = 1000 / (q["avg_time_ms"] + q.get("std_dev_ms", 0) + 1)
            performance_score.append(score)

        sorted_indices = sorted(
            range(len(performance_score)),
            key=lambda i: performance_score[i],
            reverse=True,
        )
        sorted_scores = [performance_score[i] for i in sorted_indices]
        sorted_names = [
            (
                query_data[i]["description"][:25] + "..."
                if len(query_data[i]["description"]) > 25
                else query_data[i]["description"]
            )
            for i in sorted_indices
        ]

        axes[1, 1].barh(sorted_names, sorted_scores, alpha=0.7, color="green")
        axes[1, 1].set_title("Query Performance Ranking")
        axes[1, 1].set_xlabel("Performance Score (higher is better)")
        axes[1, 1].tick_params(axis="y", rotation=0)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/query_performance_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        print("📊 Query performance analysis graph saved")

    def _generate_concurrent_access_graph(self, concurrent_data: List[Dict]):
        """Generate concurrent access performance graphs"""
        if not concurrent_data:
            return

        df = pd.DataFrame(concurrent_data)

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(
            "Concurrent Access Performance Analysis", fontsize=16, fontweight="bold"
        )

        # Throughput vs Thread Count
        axes[0].plot(
            df["num_threads"],
            df["throughput_qps"],
            marker="o",
            linewidth=2,
            markersize=8,
            color="blue",
        )
        axes[0].set_title("Throughput vs Thread Count")
        axes[0].set_xlabel("Number of Threads")
        axes[0].set_ylabel("Queries per Second")
        axes[0].grid(True, alpha=0.3)

        # Response Time vs Thread Count
        axes[1].plot(
            df["num_threads"],
            df["avg_time_ms"],
            marker="s",
            linewidth=2,
            markersize=8,
            color="red",
        )
        axes[1].plot(
            df["num_threads"],
            df["p95_time_ms"],
            marker="^",
            linewidth=2,
            markersize=8,
            color="orange",
            label="P95",
        )
        axes[1].set_title("Response Time vs Thread Count")
        axes[1].set_xlabel("Number of Threads")
        axes[1].set_ylabel("Response Time (ms)")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # P99 Response Time vs Thread Count
        if "p99_time_ms" in df.columns:
            axes[2].plot(
                df["num_threads"],
                df["p99_time_ms"],
                marker="d",
                linewidth=2,
                markersize=8,
                color="purple",
            )
            axes[2].set_title("P99 Response Time vs Thread Count")
            axes[2].set_xlabel("Number of Threads")
            axes[2].set_ylabel("P99 Response Time (ms)")
            axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/concurrent_access_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        print("📊 Concurrent access analysis graph saved")

    def _generate_write_performance_graph(self, write_data: List[Dict]):
        """Generate write performance graphs"""
        if not write_data:
            return

        df = pd.DataFrame(write_data)

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Write Performance Analysis", fontsize=16, fontweight="bold")

        # Write Time vs Batch Size
        axes[0].plot(
            df["batch_size"],
            df["avg_time_ms"],
            marker="o",
            linewidth=2,
            markersize=8,
            color="green",
        )
        axes[0].set_title("Write Time vs Batch Size")
        axes[0].set_xlabel("Batch Size")
        axes[0].set_ylabel("Average Write Time (ms)")
        axes[0].set_xscale("log")
        axes[0].grid(True, alpha=0.3)

        # Throughput vs Batch Size
        axes[1].plot(
            df["batch_size"],
            df["throughput_records_per_second"],
            marker="s",
            linewidth=2,
            markersize=8,
            color="purple",
        )
        axes[1].set_title("Write Throughput vs Batch Size")
        axes[1].set_xlabel("Batch Size")
        axes[1].set_ylabel("Throughput (records/second)")
        axes[1].set_xscale("log")
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(
            f"{self.output_dir}/write_performance_analysis.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        print("📊 Write performance analysis graph saved")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate performance graphs")
    parser.add_argument("--locust-csv", help="Locust CSV results file")
    parser.add_argument("--json-report", help="JSON performance report file")
    parser.add_argument(
        "--output-dir", default="performance_graphs", help="Output directory for graphs"
    )

    args = parser.parse_args()

    print("📊 Performance Graph Generator")
    print("=" * 40)

    generator = PerformanceGraphGenerator(args.output_dir)

    if args.locust_csv:
        if not os.path.exists(args.locust_csv):
            print(f"❌ Locust CSV file not found: {args.locust_csv}")
            return 1

        df = generator.load_locust_data(args.locust_csv)
        if not df.empty:
            generator.generate_response_time_graph(df)
            generator.generate_throughput_graph(df)
            generator.generate_error_analysis_graph(df)
            generator.generate_performance_summary_graph(df)

    if args.json_report:
        if not os.path.exists(args.json_report):
            print(f"❌ JSON report file not found: {args.json_report}")
            return 1

        generator.generate_from_json_report(args.json_report)

    print(f"\n✅ All performance graphs saved to: {args.output_dir}/")
    return 0


if __name__ == "__main__":
    exit(main())
