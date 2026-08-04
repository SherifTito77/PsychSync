#!/usr/bin/env python3
"""
DEPENDENCY GRAPH VISUALIZER
Generates visual representations of module dependencies

This tool creates dependency graphs showing:
- Module import relationships
- Fan-in/Fan-out metrics
- Potential circular dependencies
- Hot spots in the codebase

Requirements:
    pip install graphviz pygraphviz (optional)

Usage:
    python scripts/visualize_dependencies.py
    python scripts/visualize_dependencies.py --format dot --output deps.dot
    python scripts/visualize_dependencies.py --format text --output deps.txt
"""

import argparse
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyGraphBuilder:
    """Builds and analyzes dependency graphs"""

    def __init__(self, app_dir: str = "app"):
        self.app_dir = Path(app_dir)
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
        self.module_info = {}

    def build_graph(self):
        """Build dependency graph from import analysis"""
        for root, dirs, files in os.walk(self.app_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.app_dir)
                    module_name = rel_path.replace(".py", "").replace(os.sep, ".")

                    imports = self._extract_imports(file_path)
                    self.graph[module_name] = imports
                    self.module_info[module_name] = {
                        "file": rel_path,
                        "import_count": len(imports),
                        "line_count": self._count_lines(file_path),
                    }

                    # Build reverse graph (fan-in)
                    for imp in imports:
                        self.reverse_graph[imp].add(module_name)

    def _extract_imports(self, file_path: str) -> Set[str]:
        """Extract app.* imports from a file"""
        imports = set()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("from app.") and "import" in line:
                        # Extract module name
                        parts = line.split()
                        if len(parts) >= 2:
                            import_path = parts[1].replace("app.", "")
                            # Get top-level module
                            module = import_path.split(".")[0]
                            imports.add(module)
        except:
            pass
        return imports

    def _count_lines(self, file_path: str) -> int:
        """Count non-empty lines in a file"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(
                    1 for line in f if line.strip() and not line.strip().startswith("#")
                )
        except:
            return 0

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.graph:
            if node not in visited:
                dfs(node)

        return cycles

    def get_metrics(self) -> Dict:
        """Calculate graph metrics"""
        # Fan-out (how many modules this one imports)
        fan_out = {module: len(imports) for module, imports in self.graph.items()}

        # Fan-in (how many modules import this one)
        fan_in = {
            module: len(importers) for module, importers in self.reverse_graph.items()
        }

        # Top modules by various metrics
        top_fan_out = sorted(fan_out.items(), key=lambda x: x[1], reverse=True)[:10]
        top_fan_in = sorted(fan_in.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_modules": len(self.graph),
            "total_dependencies": sum(len(imports) for imports in self.graph.values()),
            "avg_fan_out": sum(fan_out.values()) / len(fan_out) if fan_out else 0,
            "max_fan_out": max(fan_out.values()) if fan_out else 0,
            "max_fan_in": max(fan_in.values()) if fan_in else 0,
            "top_fan_out": top_fan_out,
            "top_fan_in": top_fan_in,
        }

    def export_dot(self) -> str:
        """Export graph in DOT format for Graphviz"""
        lines = [
            "digraph DependencyGraph {",
            "  rankdir=LR;",
            "  node [shape=box, style=rounded];",
            "  ",
            "  // Node definitions with sizes",
        ]

        # Add nodes with size information
        for module, info in self.module_info.items():
            label = f"{module}\\n{info['line_count']} lines"
            lines.append(f'  "{module}" [label="{label}"];')

        lines.append("  ")
        lines.append("  // Edges (imports)")

        # Add edges
        for module, imports in self.graph.items():
            for imp in imports:
                lines.append(f'  "{module}" -> "{imp}";')

        lines.append("}")

        return "\n".join(lines)

    def export_text(self) -> str:
        """Export graph as text report"""
        metrics = self.get_metrics()
        cycles = self.detect_cycles()

        lines = [
            "=" * 80,
            "DEPENDENCY GRAPH REPORT",
            "=" * 80,
            "",
            "📊 METRICS",
            "",
            f"Total modules: {metrics['total_modules']}",
            f"Total dependencies: {metrics['total_dependencies']}",
            f"Average fan-out: {metrics['avg_fan_out']:.2f}",
            f"Max fan-out: {metrics['max_fan_out']}",
            f"Max fan-in: {metrics['max_fan_in']}",
            "",
            "",
            "=" * 80,
            "TOP 10 MODULES BY FAN-OUT (most imports)",
            "=" * 80,
            "",
        ]

        for i, (module, count) in enumerate(metrics["top_fan_out"], 1):
            lines.append(f"{i:2}. {module}: {count} imports")

        lines.extend(
            [
                "",
                "",
                "=" * 80,
                "TOP 10 MODULES BY FAN-IN (most imported)",
                "=" * 80,
                "",
            ]
        )

        for i, (module, count) in enumerate(metrics["top_fan_in"], 1):
            lines.append(f"{i:2}. {module}: imported by {count} modules")

        if cycles:
            lines.extend(
                [
                    "",
                    "",
                    "=" * 80,
                    "⚠️  CIRCULAR DEPENDENCIES DETECTED",
                    "=" * 80,
                    "",
                ]
            )
            for i, cycle in enumerate(cycles, 1):
                lines.append(f"Cycle {i}: {' → '.join(cycle)}")
        else:
            lines.extend(
                [
                    "",
                    "",
                    "=" * 80,
                    "✅ NO CIRCULAR DEPENDENCIES",
                    "=" * 80,
                ]
            )

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Visualize module dependencies")
    parser.add_argument(
        "--app-dir", default="app", help="Application directory (default: app)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "dot"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    print("🔨 Building dependency graph...")
    builder = DependencyGraphBuilder(args.app_dir)
    builder.build_graph()
    print(f"✅ Analyzed {len(builder.graph)} modules")
    print()

    # Generate output
    if args.format == "dot":
        output = builder.export_dot()
    else:
        output = builder.export_text()

    # Write to file or stdout
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Output written to: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
