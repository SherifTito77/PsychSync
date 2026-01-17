#!/usr/bin/env python3
"""
Product Management Prompts CLI

Command-line interface for executing and managing product management prompts.
Provides quick access to all 50 prompts without needing to use the web interface.

Usage:
    python scripts/product_prompts_cli.py list
    python scripts/product_prompts_cli.py execute rs_001 --use-ai
    python scripts/product_prompts_cli.py search "roadmap"
    python scripts/product_prompts_cli.py workflow feature_launch
    python scripts/product_prompts_cli.py categories
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.product_management_service import ProductManagementPromptsService
from app.db.database import async_session_maker
import asyncio


def print_prompt(prompt: Dict[str, Any], index: int = None):
    """Pretty print a prompt."""
    if index is not None:
        print(f"\n{'='*80}")
        print(f"[{index}] {prompt['id']}: {prompt['prompt']}")
    else:
        print(f"\n{'='*80}")
        print(f"{prompt['id']}: {prompt['prompt']}")

    print(f"{'─'*80}")
    print(f"Type:        {prompt['type']}")
    print(f"Complexity:  {prompt['complexity']}")
    print(f"Time:        {prompt['estimated_time']}")

    print(f"\n📋 Expected Outputs:")
    for i, output in enumerate(prompt['outputs'], 1):
        print(f"   {i}. {output}")

    print(f"\n🎯 Use Cases:")
    for i, use_case in enumerate(prompt['use_cases'], 1):
        print(f"   {i}. {use_case}")

    if prompt.get('related_prompts'):
        print(f"\n🔗 Related Prompts: {', '.join(prompt['related_prompts'])}")


def print_category(category: Dict[str, Any]):
    """Pretty print a category."""
    icon_map = {
        'roadmap': '🗺️',
        'users': '👥',
        'trending-up': '📈',
        'chart-bar': '📊',
        'cog': '⚙️',
    }
    icon = icon_map.get(category['icon'], '📁')

    print(f"\n{icon}  {category['name']}")
    print(f"   {category['description']}")
    print(f"   Prompts: {category['prompt_count']}")


async def list_prompts(args):
    """List all prompts with optional filtering."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        if args.category:
            prompts = await service.get_prompts_by_category(
                args.category,
                args.complexity,
                args.type
            )
        else:
            # Get all prompts
            all_prompts = []
            categories = await service.get_all_categories()
            for cat in categories:
                cat_prompts = await service.get_prompts_by_category(
                    cat['id'],
                    args.complexity,
                    args.type
                )
                all_prompts.extend(cat_prompts)
            prompts = all_prompts

        if args.json:
            print(json.dumps(prompts, indent=2))
        else:
            print(f"\n📝 Found {len(prompts)} prompts\n")
            for i, prompt in enumerate(prompts, 1):
                if args.verbose:
                    print_prompt(prompt, i)
                else:
                    print(f"{i:2}. [{prompt['id']}] {prompt['prompt']}")


async def execute_prompt(args):
    """Execute a prompt."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        # Get prompt details
        prompt = await service.get_prompt_by_id(args.prompt_id)
        if not prompt:
            print(f"❌ Prompt not found: {args.prompt_id}")
            return 1

        print(f"\n🚀 Executing prompt: {prompt['prompt']}")
        print(f"   Type: {prompt['type']} | Complexity: {prompt['complexity']}")

        # Prepare context
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON in context: {args.context}")
                return 1

        # Execute prompt
        try:
            result = await service.execute_prompt(
                prompt_id=args.prompt_id,
                user_id=1,  # TODO: Get from auth
                context=context,
                use_ai=args.use_ai
            )

            print(f"\n✅ Prompt executed successfully!")
            print(f"   Execution ID: {result['execution_id']}")
            print(f"   Executed at: {result['executed_at']}")

            if result.get('ai_suggestion'):
                print(f"\n🤖 AI-Enhanced Output:")
                print("─"*80)
                print(result['ai_suggestion'])
                print("─"*80)

            if args.save:
                output_file = Path(args.save)
                output_file.write_text(json.dumps(result, indent=2))
                print(f"\n💾 Results saved to: {output_file}")

        except Exception as e:
            print(f"\n❌ Error executing prompt: {e}")
            return 1


async def search_prompts(args):
    """Search prompts by keyword."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        results = await service.search_prompts(args.query, args.category)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"\n🔍 Search results for '{args.query}': {len(results)} found\n")
            for i, prompt in enumerate(results, 1):
                if args.verbose:
                    print_prompt(prompt, i)
                else:
                    print(f"{i:2}. [{prompt['id']}] {prompt['prompt']}")


async def show_workflow(args):
    """Show workflow for a specific goal."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        workflow = await service.get_prompt_workflow(args.goal)

        if not workflow:
            print(f"❌ No workflow found for goal: {args.goal}")
            print(f"   Try: feature_launch, retention_improvement, enterprise_expansion, quarterly_planning")
            return 1

        print(f"\n📋 Workflow: {args.goal.replace('_', ' ').title()}")
        print(f"   Steps: {len(workflow)} prompts\n")

        for i, prompt in enumerate(workflow, 1):
            print(f"{i}. [{prompt['id']}] {prompt['prompt']}")
            print(f"   ⏱️  {prompt['estimated_time']} | 🎯 {prompt['use_cases'][0]}")
            print()

        if args.execute:
            response = input("Execute this workflow? (y/n): ")
            if response.lower() == 'y':
                for prompt in workflow:
                    print(f"\n{'='*80}")
                    print(f"Executing step {workflow.index(prompt)+1}/{len(workflow)}")
                    print_prompt(prompt)
                    input("\nPress Enter to continue...")


async def show_categories(args):
    """Show all prompt categories."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        categories = await service.get_all_categories()

        if args.json:
            print(json.dumps(categories, indent=2))
        else:
            print("\n📚 Product Management Prompt Categories\n")
            for category in categories:
                print_category(category)


async def show_prompt_details(args):
    """Show detailed information about a specific prompt."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        prompt = await service.get_prompt_by_id(args.prompt_id)

        if not prompt:
            print(f"❌ Prompt not found: {args.prompt_id}")
            return 1

        print_prompt(prompt)

        # Show related prompts
        if prompt.get('related_prompts'):
            print(f"\n🔗 Related Prompts:")
            for rel_id in prompt['related_prompts']:
                rel_prompt = await service.get_prompt_by_id(rel_id)
                if rel_prompt:
                    print(f"   [{rel_prompt['id']}] {rel_prompt['prompt']}")


async def show_history(args):
    """Show prompt execution history."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        history = await service.get_execution_history(
            prompt_id=args.prompt_id,
            limit=args.limit
        )

        if args.json:
            print(json.dumps(history, indent=2))
        else:
            print(f"\n📜 Execution History (showing {len(history['executions'])} records)\n")
            for exec in history['executions']:
                print(f"ID: {exec['id']}")
                print(f"Prompt: {exec['prompt_id']}")
                print(f"When: {exec['executed_at']}")
                print(f"AI: {'Yes' if exec['use_ai'] else 'No'}")
                if exec.get('quality_rating'):
                    print(f"Rating: {exec['quality_rating']}/5 ⭐")
                print()


async def show_statistics(args):
    """Show usage statistics."""
    async with async_session_maker() as db:
        service = ProductManagementPromptsService(db)

        stats = await service.get_usage_statistics()

        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("\n📊 Product Management Prompts Statistics\n")
            print(f"Total Prompts:     {stats['total_prompts']}")
            print(f"Categories:        {stats['categories_count']}")
            print(f"Total Executions:  {stats['total_executions']}")

            if stats.get('most_used_prompts'):
                print(f"\n🔥 Most Used Prompts:")
                for item in stats['most_used_prompts']:
                    print(f"   {item['prompt_id']}: {item.get('count', 'N/A')} executions")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Product Management Prompts CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                                    List all prompts
  %(prog)s list --category roadmap_strategy         List prompts in a category
  %(prog)s execute rs_001                          Execute a prompt
  %(prog)s execute rs_001 --use-ai                 Execute with AI enhancement
  %(prog)s search "roadmap"                         Search prompts
  %(prog)s workflow feature_launch                 Show workflow for goal
  %(prog)s prompt rs_001                           Show prompt details
  %(prog)s categories                              List all categories
  %(prog)s history --limit 10                      Show execution history
  %(prog)s statistics                              Show usage statistics
        """
    )

    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List prompts')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--complexity', choices=['low', 'medium', 'high'], help='Filter by complexity')
    list_parser.add_argument('--type', choices=['strategic', 'tactical', 'analytical', 'technical', 'creative', 'experimental'], help='Filter by type')

    # Execute command
    exec_parser = subparsers.add_parser('execute', help='Execute a prompt')
    exec_parser.add_argument('prompt_id', help='Prompt ID (e.g., rs_001)')
    exec_parser.add_argument('--use-ai', action='store_true', help='Use AI enhancement')
    exec_parser.add_argument('--context', help='Context as JSON string')
    exec_parser.add_argument('--save', help='Save output to file')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search prompts')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--category', help='Limit search to category')

    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Show workflow for goal')
    workflow_parser.add_argument('goal', choices=['feature_launch', 'retention_improvement', 'enterprise_expansion', 'quarterly_planning'], help='Workflow goal')
    workflow_parser.add_argument('--execute', action='store_true', help='Execute workflow interactively')

    # Categories command
    subparsers.add_parser('categories', help='List all categories')

    # Prompt details command
    prompt_parser = subparsers.add_parser('prompt', help='Show prompt details')
    prompt_parser.add_argument('prompt_id', help='Prompt ID')

    # History command
    history_parser = subparsers.add_parser('history', help='Show execution history')
    history_parser.add_argument('--prompt-id', help='Filter by prompt ID')
    history_parser.add_argument('--limit', type=int, default=20, help='Limit results')

    # Statistics command
    subparsers.add_parser('statistics', help='Show usage statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    commands = {
        'list': list_prompts,
        'execute': execute_prompt,
        'search': search_prompts,
        'workflow': show_workflow,
        'categories': show_categories,
        'prompt': show_prompt_details,
        'history': show_history,
        'statistics': show_statistics,
    }

    command_func = commands.get(args.command)
    if command_func:
        return asyncio.run(command_func(args))
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
