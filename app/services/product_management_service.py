"""
Product Management Prompts Service

Provides access to 50 curated product management prompts for PsychSync.
Supports prompt retrieval, categorization, and execution with optional AI enhancement.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import logger
from app.db.models.product_management import PromptExecution, PromptTemplate


class ProductManagementPromptsService:
    """
    Service for managing and executing product management prompts.

    Features:
    - Load prompts from JSON configuration
    - Retrieve by category, complexity, or use case
    - Track prompt execution and results
    - Optional AI enhancement for prompt outputs
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.prompts_file = (
            Path(__file__).parent.parent / "db" / "product_management_prompts.json"
        )
        self._prompts_cache: Optional[Dict[str, Any]] = None

    async def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from JSON file with caching."""
        if self._prompts_cache is None:
            try:
                with open(self.prompts_file, "r") as f:
                    self._prompts_cache = json.load(f)
                logger.info(
                    f"Loaded {self._prompts_cache['metadata']['total_prompts']} product management prompts"
                )
            except FileNotFoundError:
                logger.error(f"Prompts file not found: {self.prompts_file}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in prompts file: {e}")
                raise
        return self._prompts_cache

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Get all prompt categories with metadata.

        Returns:
            List of category dictionaries with name, description, icon, and prompt count
        """
        data = await self._load_prompts()
        categories = []

        for cat_id, cat_data in data["categories"].items():
            prompt_count = len(cat_data["prompts"])
            categories.append(
                {
                    "id": cat_id,
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "icon": cat_data["icon"],
                    "prompt_count": prompt_count,
                }
            )

        return categories

    async def get_prompts_by_category(
        self,
        category_id: str,
        complexity_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all prompts in a category with optional filtering.

        Args:
            category_id: Category identifier (e.g., 'roadmap_strategy', 'user_experience')
            complexity_filter: Filter by complexity ('low', 'medium', 'high')
            type_filter: Filter by type ('strategic', 'tactical', 'analytical', 'technical', 'creative', 'experimental')

        Returns:
            List of prompt dictionaries
        """
        data = await self._load_prompts()
        category = data["categories"].get(category_id)

        if not category:
            raise ValueError(f"Category not found: {category_id}")

        prompts = category["prompts"]

        # Apply filters
        if complexity_filter:
            prompts = [p for p in prompts if p["complexity"] == complexity_filter]

        if type_filter:
            prompts = [p for p in prompts if p["type"] == type_filter]

        return prompts

    async def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific prompt by its ID.

        Args:
            prompt_id: Prompt identifier (e.g., 'rs_001', 'ux_002')

        Returns:
            Prompt dictionary or None if not found
        """
        data = await self._load_prompts()

        for category_data in data["categories"].values():
            for prompt in category_data["prompts"]:
                if prompt["id"] == prompt_id:
                    # Add category context
                    prompt["category"] = {
                        "id": list(data["categories"].keys())[
                            list(data["categories"].values()).index(category_data)
                        ],
                        "name": category_data["name"],
                    }
                    return prompt

        return None

    async def search_prompts(
        self, query: str, category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search prompts by keyword in prompt text, use cases, and outputs.

        Args:
            query: Search query string
            category_id: Optional category to limit search

        Returns:
            List of matching prompts ranked by relevance
        """
        data = await self._load_prompts()
        results = []
        query_lower = query.lower()

        categories_to_search = (
            [category_id] if category_id else list(data["categories"].keys())
        )

        for cat_id in categories_to_search:
            category = data["categories"][cat_id]
            for prompt in category["prompts"]:
                # Search in prompt text, use cases, and outputs
                searchable_text = (
                    f"{prompt['prompt']} "
                    f"{' '.join(prompt['use_cases'])} "
                    f"{' '.join(prompt['outputs'])}"
                ).lower()

                if query_lower in searchable_text:
                    results.append(
                        {
                            **prompt,
                            "category_id": cat_id,
                            "category_name": category["name"],
                        }
                    )

        # Sort by relevance (exact matches first)
        results.sort(key=lambda p: query_lower in p["prompt"].lower(), reverse=True)

        return results

    async def get_prompts_by_use_case(self, use_case: str) -> List[Dict[str, Any]]:
        """
        Get prompts relevant to a specific use case.

        Args:
            use_case: Use case scenario (e.g., 'Quarterly planning', 'Feature development')

        Returns:
            List of relevant prompts
        """
        data = await self._load_prompts()
        results = []
        use_case_lower = use_case.lower()

        for cat_id, category in data["categories"].items():
            for prompt in category["prompts"]:
                if any(use_case_lower in uc.lower() for uc in prompt["use_cases"]):
                    results.append(
                        {
                            **prompt,
                            "category_id": cat_id,
                            "category_name": category["name"],
                        }
                    )

        return results

    async def execute_prompt(
        self,
        prompt_id: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a prompt and track the execution.

        Args:
            prompt_id: Prompt identifier
            user_id: User executing the prompt
            context: Additional context for prompt execution
            use_ai: Whether to use AI enhancement for output generation

        Returns:
            Execution result with prompt details and any generated content
        """
        prompt = await self.get_prompt_by_id(prompt_id)

        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_id}")

        # Create execution record
        execution = PromptExecution(
            prompt_id=prompt_id,
            user_id=user_id,
            context=context or {},
            executed_at=datetime.utcnow(),
            use_ai=use_ai,
        )

        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(f"Prompt {prompt_id} executed by user {user_id}")

        result = {
            "prompt": prompt,
            "execution_id": execution.id,
            "executed_at": execution.executed_at.isoformat(),
            "use_ai": use_ai,
        }

        # If AI enhancement requested, generate initial output
        if use_ai:
            result["ai_suggestion"] = await self._generate_ai_output(prompt, context)

        return result

    async def _generate_ai_output(
        self, prompt: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate AI-enhanced output for a prompt.

        This is a placeholder for AI integration. In production, this would
        call an AI service (e.g., OpenAI, Anthropic) to generate contextual
        outputs based on the prompt and provided context.
        """
        # TODO: Integrate with AI service
        ai_prompt = f"""
        You are a product management expert. Based on the following prompt,
        generate a structured output:

        Prompt: {prompt['prompt']}

        Expected Outputs: {', '.join(prompt['outputs'])}

        Context: {json.dumps(context, indent=2) if context else 'None provided'}

        Provide a structured, actionable response.
        """

        # Placeholder - replace with actual AI service call
        return f"AI-generated output for prompt: {prompt['prompt']}"

    async def get_execution_history(
        self,
        user_id: Optional[int] = None,
        prompt_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get historical prompt executions with filtering.

        Args:
            user_id: Filter by user (None for all users)
            prompt_id: Filter by prompt (None for all prompts)
            limit: Maximum number of results

        Returns:
            List of execution records
        """
        query = select(PromptExecution)

        if user_id:
            query = query.where(PromptExecution.user_id == user_id)

        if prompt_id:
            query = query.where(PromptExecution.prompt_id == prompt_id)

        query = query.order_by(PromptExecution.executed_at.desc()).limit(limit)

        result = await self.db.execute(query)
        executions = result.scalars().all()

        return [
            {
                "id": exec.id,
                "prompt_id": exec.prompt_id,
                "user_id": exec.user_id,
                "executed_at": exec.executed_at.isoformat(),
                "context": exec.context,
                "use_ai": exec.use_ai,
            }
            for exec in executions
        ]

    async def get_related_prompts(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get prompts related to a given prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of related prompts
        """
        prompt = await self.get_prompt_by_id(prompt_id)

        if not prompt or not prompt.get("related_prompts"):
            return []

        related = []
        for related_id in prompt["related_prompts"]:
            related_prompt = await self.get_prompt_by_id(related_id)
            if related_prompt:
                related.append(related_prompt)

        return related

    async def get_prompt_workflow(self, goal: str) -> List[Dict[str, Any]]:
        """
        Get a suggested workflow of prompts for a specific goal.

        Args:
            goal: High-level goal (e.g., 'Launch new feature', 'Improve retention')

        Returns:
            Ordered list of prompts to execute
        """
        # Define common workflows
        workflows = {
            "feature_launch": [
                "rs_002",  # Generate feature brief
                "an_002",  # Define product inputs for engineering specs
                "ux_001",  # Define user journey
                "op_004",  # Write UX acceptance criteria
                "op_010",  # Design announcement playbook
            ],
            "retention_improvement": [
                "gm_002",  # Produce retention levers
                "an_005",  # Generate churn prediction signals
                "ux_007",  # Define customer lifecycle
                "gm_003",  # Turn pain points into opportunities
                "an_004",  # Create KPIs for feature success
            ],
            "enterprise_expansion": [
                "rs_003",  # Create enterprise strategy
                "ux_005",  # Define enterprise personas
                "op_002",  # Define permissions matrix
                "op_011",  # Generate SLAs and SLOs
                "gm_006",  # Create pricing tiers
            ],
            "quarterly_planning": [
                "rs_001",  # Create roadmap based on value vs complexity
                "an_007",  # Build quarterly OKRs
                "rs_005",  # Create innovation roadmap
                "an_001",  # Create KPI dashboard
                "op_003",  # Design collaboration workflows
            ],
        }

        # Match goal to workflow
        goal_lower = goal.lower()
        workflow_key = None

        if "feature" in goal_lower and (
            "launch" in goal_lower or "develop" in goal_lower
        ):
            workflow_key = "feature_launch"
        elif "retention" in goal_lower or "churn" in goal_lower:
            workflow_key = "retention_improvement"
        elif "enterprise" in goal_lower or "b2b" in goal_lower:
            workflow_key = "enterprise_expansion"
        elif (
            "quarterly" in goal_lower or "planning" in goal_lower or "okr" in goal_lower
        ):
            workflow_key = "quarterly_planning"

        if not workflow_key or workflow_key not in workflows:
            # Return empty list if no workflow matches
            return []

        # Fetch prompt details for workflow
        workflow_prompts = []
        for prompt_id in workflows[workflow_key]:
            prompt = await self.get_prompt_by_id(prompt_id)
            if prompt:
                workflow_prompts.append(prompt)

        return workflow_prompts

    async def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated statistics about prompt usage.

        Returns:
            Dictionary with usage metrics
        """
        # Get total executions
        total_executions = await self.db.execute(select(PromptExecution).count())

        # Get most used prompts
        most_used = await self.db.execute(
            select(PromptExecution.prompt_id)
            .group_by(PromptExecution.prompt_id)
            .order_by(PromptExecution.prompt_id.desc())
            .limit(10)
        )

        return {
            "total_executions": total_executions,
            "most_used_prompts": most_used,
            "categories_count": len(await self.get_all_categories()),
            "total_prompts": (await self._load_prompts())["metadata"]["total_prompts"],
        }
