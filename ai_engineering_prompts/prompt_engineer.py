#!/usr/bin/env python3
"""
AI Engineering Prompts CLI for PsychSync
A comprehensive tool for running AI-powered engineering analysis prompts
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

console = Console()


class PromptEngineer:
    """Main class for managing and executing AI engineering prompts"""

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize the PromptEngineer with a registry path"""
        if registry_path is None:
            registry_path = Path(__file__).parent / "prompts_registry.yaml"

        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict:
        """Load the prompts registry from YAML file"""
        if not self.registry_path.exists():
            console.print(
                f"[red]❌ Registry file not found: {self.registry_path}[/red]"
            )
            sys.exit(1)

        with open(self.registry_path, "r") as f:
            return yaml.safe_load(f)

    def list_categories(self) -> List[Dict]:
        """Get all categories from the registry"""
        return self.registry.get("registry", {}).get("categories", [])

    def get_category(self, category_id: str) -> Optional[Dict]:
        """Get a specific category by ID"""
        for category in self.list_categories():
            if category["id"] == category_id:
                return category
        return None

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a specific prompt by ID across all categories"""
        for category in self.list_categories():
            for prompt in category.get("prompts", []):
                if prompt["id"] == prompt_id:
                    return {**prompt, "category": category}
        return None

    def search_prompts(self, query: str) -> List[Dict]:
        """Search prompts by name, description, or content"""
        results = []
        query_lower = query.lower()

        for category in self.list_categories():
            for prompt in category.get("prompts", []):
                # Search in name, description, and prompt content
                if (
                    query_lower in prompt["name"].lower()
                    or query_lower in prompt.get("description", "").lower()
                    or query_lower in prompt["prompt"].lower()
                ):
                    results.append({**prompt, "category": category})

        return results

    def filter_by_scope(self, scope: str) -> List[Dict]:
        """Filter prompts by scope (backend, frontend, api, etc.)"""
        results = []

        for category in self.list_categories():
            for prompt in category.get("prompts", []):
                if scope in prompt.get("scope", []):
                    results.append({**prompt, "category": category})

        return results

    def filter_by_complexity(self, complexity: str) -> List[Dict]:
        """Filter prompts by complexity level (low, medium, high)"""
        results = []

        for category in self.list_categories():
            for prompt in category.get("prompts", []):
                if prompt.get("complexity") == complexity:
                    results.append({**prompt, "category": category})

        return results


class UIHelpers:
    """Helper methods for UI rendering"""

    @staticmethod
    def display_banner():
        """Display the application banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan] [bold yellow]🤖 PsychSync AI Engineering Prompts[/bold yellow]                [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan] [dim]Comprehensive AI-Powered Codebase Analysis[/dim]         [bold cyan]║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]
"""
        console.print(banner)

    @staticmethod
    def display_metadata(registry: Dict):
        """Display registry metadata"""
        metadata = registry.get("registry", {}).get("metadata", {})

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Version", metadata.get("version", "N/A"))
        table.add_row("Last Updated", metadata.get("last_updated", "N/A"))
        table.add_row("Project", metadata.get("project", "N/A"))

        console.print(table)
        console.print()

    @staticmethod
    def display_categories(categories: List[Dict]):
        """Display all categories in a table"""
        table = Table(
            title="📋 Prompt Categories", show_header=True, header_style="bold magenta"
        )
        table.add_column("ID", style="dim cyan", width=15)
        table.add_column("Icon", style="bold", width=5)
        table.add_column("Category Name", style="bold white", width=30)
        table.add_column("Description", style="dim", width=50)
        table.add_column("Prompts", justify="right", style="green", width=8)

        for category in categories:
            prompt_count = len(category.get("prompts", []))
            table.add_row(
                category["id"],
                category.get("icon", "📁"),
                category["name"],
                category.get("description", ""),
                str(prompt_count),
            )

        console.print(table)

    @staticmethod
    def display_prompts(prompts: List[Dict], show_category: bool = False):
        """Display prompts in a table"""
        table = Table(
            title="🎯 Available Prompts", show_header=True, header_style="bold magenta"
        )
        table.add_column("ID", style="dim cyan", width=20)
        if show_category:
            table.add_column("Category", style="cyan", width=15)
        table.add_column("Name", style="bold white", width=35)
        table.add_column("Complexity", style="yellow", width=10)
        table.add_column("Time", style="blue", width=12)
        table.add_column("Scope", style="green", width=30)

        for prompt in prompts:
            complexity = prompt.get("complexity", "unknown")
            complexity_color = {"low": "green", "medium": "yellow", "high": "red"}.get(
                complexity, "white"
            )

            row = [
                prompt["id"],
                prompt["name"],
                f"[{complexity_color}]{complexity.upper()}[/{complexity_color}]",
                prompt.get("estimated_time", "N/A"),
                ", ".join(prompt.get("scope", [])),
            ]

            if show_category:
                row.insert(1, prompt.get("category", {}).get("name", "N/A"))

            table.add_row(*row)

        console.print(table)

    @staticmethod
    def display_prompt_details(prompt: Dict):
        """Display detailed information about a single prompt"""
        category = prompt.get("category", {})

        # Header
        console.print(f"\n[bold cyan]═══ {prompt['name']} [/bold cyan]\n")

        # Metadata panel
        metadata_table = Table(show_header=False, box=None, padding=(0, 2))
        metadata_table.add_column("Field", style="cyan")
        metadata_table.add_column("Value", style="white")

        metadata_table.add_row("ID", prompt["id"])
        metadata_table.add_row(
            "Category", f"{category.get('icon', '')} {category.get('name', 'N/A')}"
        )
        metadata_table.add_row(
            "Complexity", prompt.get("complexity", "unknown").upper()
        )
        metadata_table.add_row("Estimated Time", prompt.get("estimated_time", "N/A"))
        metadata_table.add_row("Scope", ", ".join(prompt.get("scope", [])))

        console.print(
            Panel(metadata_table, title="📊 Prompt Metadata", border_style="cyan")
        )

        # Prompt content
        console.print("\n[bold yellow]📝 Prompt Content:[/bold yellow]\n")
        prompt_panel = Panel(
            prompt["prompt"], title="Prompt", border_style="yellow", padding=(1, 2)
        )
        console.print(prompt_panel)

    @staticmethod
    def export_prompt(prompt: Dict, output_path: Path):
        """Export a prompt to a file"""
        content = f"""# {prompt['name']}

**ID:** {prompt['id']}
**Category:** {prompt.get('category', {}).get('name', 'N/A')}
**Complexity:** {prompt.get('complexity', 'unknown').upper()}
**Estimated Time:** {prompt.get('estimated_time', 'N/A')}
**Scope:** {', '.join(prompt.get('scope', []))}

## Prompt

{prompt['prompt']}

## Execution Notes

- Created: {prompt.get('created_at', 'N/A')}
- Registry Version: {prompt.get('registry_version', 'N/A')}
"""

        with open(output_path, "w") as f:
            f.write(content)

        console.print(f"[green]✅ Prompt exported to: {output_path}[/green]")


def cmd_list(args):
    """List categories or prompts"""
    pe = PromptEngineer(args.registry)

    UIHelpers.display_banner()

    if args.categories:
        # List categories
        categories = pe.list_categories()
        UIHelpers.display_metadata(pe.registry)
        UIHelpers.display_categories(categories)

    elif args.category:
        # List prompts in a specific category
        category = pe.get_category(args.category)
        if not category:
            console.print(f"[red]❌ Category not found: {args.category}[/red]")
            sys.exit(1)

        console.print(
            f"\n[bold cyan]Category: {category['icon']} {category['name']}[/bold cyan]\n"
        )
        UIHelpers.display_prompts(category.get("prompts", []))

    else:
        # List all prompts
        all_prompts = []
        for category in pe.list_categories():
            for prompt in category.get("prompts", []):
                all_prompts.append({**prompt, "category": category})

        UIHelpers.display_metadata(pe.registry)
        UIHelpers.display_prompts(all_prompts, show_category=True)


def cmd_show(args):
    """Show details of a specific prompt"""
    pe = PromptEngineer(args.registry)

    prompt = pe.get_prompt(args.prompt_id)
    if not prompt:
        console.print(f"[red]❌ Prompt not found: {args.prompt_id}[/red]")
        sys.exit(1)

    UIHelpers.display_banner()
    UIHelpers.display_prompt_details(prompt)

    # Export if requested
    if args.export:
        output_path = Path(args.export)
        UIHelpers.export_prompt(prompt, output_path)


def cmd_search(args):
    """Search for prompts"""
    pe = PromptEngineer(args.registry)

    UIHelpers.display_banner()
    console.print(
        f"[bold cyan]🔍 Searching for: [yellow]{args.query}[/yellow][/bold cyan]\n"
    )

    results = pe.search_prompts(args.query)

    if not results:
        console.print("[dim]No prompts found matching your query.[/dim]")
        return

    console.print(f"[green]Found {len(results)} prompt(s)[/green]\n")
    UIHelpers.display_prompts(results, show_category=True)


def cmd_filter(args):
    """Filter prompts by scope or complexity"""
    pe = PromptEngineer(args.registry)

    UIHelpers.display_banner()

    if args.scope:
        console.print(
            f"[bold cyan]🔍 Filtering by scope: [yellow]{args.scope}[/yellow][/bold cyan]\n"
        )
        results = pe.filter_by_scope(args.scope)
        filter_name = f"Scope: {args.scope}"

    elif args.complexity:
        console.print(
            f"[bold cyan]🔍 Filtering by complexity: [yellow]{args.complexity}[/yellow][/bold cyan]\n"
        )
        results = pe.filter_by_complexity(args.complexity)
        filter_name = f"Complexity: {args.complexity}"

    else:
        console.print("[red]❌ Please specify --scope or --complexity[/red]")
        sys.exit(1)

    if not results:
        console.print("[dim]No prompts found matching your filter.[/dim]")
        return

    console.print(f"[green]Found {len(results)} prompt(s)[/green]\n")
    UIHelpers.display_prompts(results, show_category=True)


def cmd_interactive(args):
    """Interactive prompt selection mode"""
    pe = PromptEngineer(args.registry)

    UIHelpers.display_banner()
    UIHelpers.display_metadata(pe.registry)

    while True:
        console.print(
            "\n[bold cyan]🤖 AI Engineering Prompts - Interactive Mode[/bold cyan]\n"
        )

        # Show menu
        console.print("[bold]1.[/bold] List all categories")
        console.print("[bold]2.[/bold] Browse by category")
        console.print("[bold]3.[/bold] Search prompts")
        console.print("[bold]4.[/bold] View prompt details")
        console.print("[bold]5.[/bold] Filter by scope")
        console.print("[bold]6.[/bold] Filter by complexity")
        console.print("[bold]0.[/bold] Exit\n")

        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="0",
        )

        if choice == "0":
            console.print("[green]👋 Goodbye![/green]")
            break

        elif choice == "1":
            # List categories
            categories = pe.list_categories()
            UIHelpers.display_categories(categories)

        elif choice == "2":
            # Browse by category
            categories = pe.list_categories()
            category_ids = [c["id"] for c in categories]

            console.print("\n[bold]Available Categories:[/bold]")
            for cat in categories:
                console.print(
                    f"  {cat['icon']} [cyan]{cat['id']}[/cyan] - {cat['name']}"
                )

            cat_choice = Prompt.ask(
                "\n[bold cyan]Enter category ID[/bold cyan]", choices=category_ids
            )

            category = pe.get_category(cat_choice)
            prompts = category.get("prompts", [])

            console.print(f"\n[bold cyan]Prompts in {category['name']}:[/bold cyan]")
            UIHelpers.display_prompts(prompts)

        elif choice == "3":
            # Search prompts
            query = Prompt.ask("[bold cyan]Enter search query[/bold cyan]")
            results = pe.search_prompts(query)

            if results:
                console.print(f"\n[green]Found {len(results)} prompt(s)[/green]")
                UIHelpers.display_prompts(results, show_category=True)
            else:
                console.print("[dim]No results found.[/dim]")

        elif choice == "4":
            # View prompt details
            prompt_id = Prompt.ask("[bold cyan]Enter prompt ID[/bold cyan]")
            prompt = pe.get_prompt(prompt_id)

            if prompt:
                UIHelpers.display_prompt_details(prompt)

                if Confirm.ask(
                    "[bold cyan]Export this prompt?[/bold cyan]", default=False
                ):
                    filename = Prompt.ask(
                        "[bold cyan]Output filename[/bold cyan]",
                        default=f"{prompt_id}.md",
                    )
                    UIHelpers.export_prompt(prompt, Path(filename))
            else:
                console.print("[red]❌ Prompt not found[/red]")

        elif choice == "5":
            # Filter by scope
            scopes = [
                "backend",
                "frontend",
                "api",
                "database",
                "devops",
                "testing",
                "security",
                "architecture",
                "all",
                "analytics",
            ]
            console.print(f"\n[bold]Available scopes:[/bold] {', '.join(scopes)}")

            scope = Prompt.ask("[bold cyan]Enter scope[/bold cyan]", choices=scopes)

            results = pe.filter_by_scope(scope)
            if results:
                console.print(f"\n[green]Found {len(results)} prompt(s)[/green]")
                UIHelpers.display_prompts(results, show_category=True)
            else:
                console.print("[dim]No results found.[/dim]")

        elif choice == "6":
            # Filter by complexity
            complexities = ["low", "medium", "high"]
            console.print(
                f"\n[bold]Available complexities:[/bold] {', '.join(complexities)}"
            )

            complexity = Prompt.ask(
                "[bold cyan]Enter complexity level[/bold cyan]", choices=complexities
            )

            results = pe.filter_by_complexity(complexity)
            if results:
                console.print(f"\n[green]Found {len(results)} prompt(s)[/green]")
                UIHelpers.display_prompts(results, show_category=True)
            else:
                console.print("[dim]No results found.[/dim]")


def cmd_stats(args):
    """Show statistics about the prompt registry"""
    pe = PromptEngineer(args.registry)

    UIHelpers.display_banner()

    categories = pe.list_categories()
    total_prompts = sum(len(c.get("prompts", [])) for c in categories)

    # Count by complexity
    complexity_counts = {"low": 0, "medium": 0, "high": 0}
    scope_counts = {}

    for category in categories:
        for prompt in category.get("prompts", []):
            # Count complexity
            complexity = prompt.get("complexity", "unknown")
            if complexity in complexity_counts:
                complexity_counts[complexity] += 1

            # Count scopes
            for scope in prompt.get("scope", []):
                scope_counts[scope] = scope_counts.get(scope, 0) + 1

    # Display stats
    stats_table = Table(title="📊 Registry Statistics", show_header=False)
    stats_table.add_column("Metric", style="cyan", width=30)
    stats_table.add_column("Value", style="bold white", width=20)

    stats_table.add_row("Total Categories", str(len(categories)))
    stats_table.add_row("Total Prompts", str(total_prompts))
    stats_table.add_row("Low Complexity", str(complexity_counts["low"]))
    stats_table.add_row("Medium Complexity", str(complexity_counts["medium"]))
    stats_table.add_row("High Complexity", str(complexity_counts["high"]))

    console.print(stats_table)

    # Scope distribution
    console.print("\n[bold]Scope Distribution:[/bold]")
    scope_table = Table(show_header=True)
    scope_table.add_column("Scope", style="cyan")
    scope_table.add_column("Count", justify="right", style="green")

    for scope, count in sorted(scope_counts.items(), key=lambda x: x[1], reverse=True):
        scope_table.add_row(scope, str(count))

    console.print(scope_table)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Engineering Prompts CLI for PsychSync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all categories
  %(prog)s list --categories

  # List all prompts
  %(prog)s list

  # List prompts in a category
  %(prog)s list --category architecture

  # Show prompt details
  %(prog)s show audit-architecture

  # Search prompts
  %(prog)s search "performance"

  # Filter by scope
  %(prog)s filter --scope backend

  # Filter by complexity
  %(prog)s filter --complexity high

  # Interactive mode
  %(prog)s interactive

  # Show statistics
  %(prog)s stats
        """,
    )

    parser.add_argument(
        "--registry", type=Path, default=None, help="Path to prompts registry YAML file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List categories and prompts")
    list_parser.add_argument(
        "--categories", action="store_true", help="List all categories"
    )
    list_parser.add_argument(
        "--category", type=str, help="List prompts in a specific category"
    )
    list_parser.set_defaults(func=cmd_list)

    # Show command
    show_parser = subparsers.add_parser("show", help="Show prompt details")
    show_parser.add_argument("prompt_id", type=str, help="Prompt ID")
    show_parser.add_argument("--export", type=str, help="Export prompt to file")
    show_parser.set_defaults(func=cmd_show)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search prompts")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.set_defaults(func=cmd_search)

    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter prompts")
    filter_group = filter_parser.add_mutually_exclusive_group(required=True)
    filter_group.add_argument("--scope", type=str, help="Filter by scope")
    filter_group.add_argument(
        "--complexity",
        type=str,
        choices=["low", "medium", "high"],
        help="Filter by complexity",
    )
    filter_parser.set_defaults(func=cmd_filter)

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    interactive_parser.set_defaults(func=cmd_interactive)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show registry statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
