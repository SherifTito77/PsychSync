#!/usr/bin/env python3
"""
Product Management Prompts Service
A standalone Flask-based web service for managing and executing product management prompts

Port: 5001
"""

import json
import random
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Constants
BASE_DIR = Path(__file__).parent
PROMPTS_FILE = BASE_DIR / "product_management_prompts.json"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


class ProductPromptsManager:
    """Manages product management prompts loading and filtering"""

    def __init__(self):
        self.prompts_data = None
        self.load_prompts()

    def load_prompts(self):
        """Load prompts from JSON file"""
        try:
            with open(PROMPTS_FILE, "r") as f:
                self.prompts_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Prompts file not found at {PROMPTS_FILE}")
            self.prompts_data = {"categories": {}, "metadata": {"total_prompts": 0}}

    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        categories = []
        for cat_id, cat_data in self.prompts_data.get("categories", {}).items():
            categories.append(
                {
                    "id": cat_id,
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "icon": cat_data["icon"],
                    "prompt_count": len(cat_data["prompts"]),
                }
            )
        return categories

    def get_category(self, category_id: str) -> Optional[Dict]:
        """Get a specific category"""
        category = self.prompts_data.get("categories", {}).get(category_id)
        if category:
            return {"id": category_id, **category}
        return None

    def get_all_prompts(self) -> List[Dict]:
        """Get all prompts from all categories"""
        prompts = []
        for cat_id, cat_data in self.prompts_data.get("categories", {}).items():
            category = {
                "id": cat_id,
                "name": cat_data["name"],
                "icon": cat_data["icon"],
            }
            for prompt in cat_data.get("prompts", []):
                prompts.append({**prompt, "category": category})
        return prompts

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get a specific prompt by ID"""
        for cat_id, cat_data in self.prompts_data.get("categories", {}).items():
            for prompt in cat_data.get("prompts", []):
                if prompt["id"] == prompt_id:
                    return {
                        **prompt,
                        "category": {"id": cat_id, "name": cat_data["name"]},
                    }
        return None

    def filter_prompts(
        self,
        category_id: Optional[str] = None,
        complexity: Optional[str] = None,
        type_: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict]:
        """Filter prompts by various criteria"""
        prompts = self.get_all_prompts()

        if category_id:
            prompts = [p for p in prompts if p["category"]["id"] == category_id]

        if complexity:
            prompts = [p for p in prompts if p["complexity"] == complexity]

        if type_:
            prompts = [p for p in prompts if p["type"] == type_]

        if search:
            search_lower = search.lower()
            prompts = [
                p
                for p in prompts
                if search_lower in p["prompt"].lower()
                or any(search_lower in uc.lower() for uc in p["use_cases"])
            ]

        return prompts

    def get_workflow(self, goal: str) -> List[Dict]:
        """Get prompts for a specific workflow goal"""
        workflows = {
            "feature_launch": ["rs_002", "an_002", "ux_001", "op_004", "op_010"],
            "retention_improvement": ["gm_002", "an_005", "ux_007", "gm_003", "an_004"],
            "enterprise_expansion": ["rs_003", "ux_005", "op_002", "op_011", "gm_006"],
            "quarterly_planning": ["rs_001", "an_007", "rs_005", "an_001", "op_003"],
        }

        prompt_ids = workflows.get(goal, [])
        workflow_prompts = []
        for pid in prompt_ids:
            prompt = self.get_prompt(pid)
            if prompt:
                workflow_prompts.append(prompt)
        return workflow_prompts


# Initialize manager
manager = ProductPromptsManager()

# Track executions (in-memory for demo)
executions = []


# ============================================================================
# Web Routes
# ============================================================================


@app.route("/")
def index():
    """Render the main web interface"""
    return render_template("product_prompts.html")


@app.route("/api/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "Product Management Prompts",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/categories")
def get_categories():
    """Get all categories"""
    categories = manager.get_categories()
    return jsonify({"success": True, "categories": categories})


@app.route("/api/categories/<category_id>")
def get_category(category_id):
    """Get a specific category with its prompts"""
    category = manager.get_category(category_id)
    if category:
        return jsonify({"success": True, "category": category})
    else:
        return jsonify({"success": False, "error": "Category not found"}), 404


@app.route("/api/categories/<category_id>/prompts")
def get_category_prompts(category_id):
    """Get prompts from a specific category"""
    prompts = manager.filter_prompts(category_id=category_id)
    return jsonify({"success": True, "prompts": prompts, "count": len(prompts)})


@app.route("/api/prompts")
def get_prompts():
    """Get all prompts with optional filtering"""
    category_id = request.args.get("category")
    complexity = request.args.get("complexity")
    type_ = request.args.get("type")
    search = request.args.get("search")

    prompts = manager.filter_prompts(
        category_id=category_id, complexity=complexity, type_=type_, search=search
    )

    return jsonify(
        {
            "success": True,
            "prompts": prompts,
            "count": len(prompts),
            "filters": {
                "category": category_id,
                "complexity": complexity,
                "type": type_,
                "search": search,
            },
        }
    )


@app.route("/api/prompts/<prompt_id>")
def get_prompt(prompt_id):
    """Get a specific prompt"""
    prompt = manager.get_prompt(prompt_id)
    if prompt:
        return jsonify({"success": True, "prompt": prompt})
    else:
        return jsonify({"success": False, "error": "Prompt not found"}), 404


@app.route("/api/prompts/<prompt_id>/related")
def get_related_prompts(prompt_id):
    """Get prompts related to a specific prompt"""
    prompt = manager.get_prompt(prompt_id)
    if prompt and prompt.get("related_prompts"):
        related = []
        for rel_id in prompt["related_prompts"]:
            rel_prompt = manager.get_prompt(rel_id)
            if rel_prompt:
                related.append(rel_prompt)
        return jsonify({"success": True, "related": related})
    else:
        return (
            jsonify(
                {"success": False, "error": "Prompt not found or no related prompts"}
            ),
            404,
        )


@app.route("/api/prompts/search/<query>")
def search_prompts(query):
    """Search prompts by keyword"""
    prompts = manager.filter_prompts(search=query)
    return jsonify(
        {"success": True, "prompts": prompts, "count": len(prompts), "query": query}
    )


@app.route("/api/workflows/<goal>")
def get_workflow(goal):
    """Get prompts for a specific workflow goal"""
    workflow = manager.get_workflow(goal)
    if workflow:
        return jsonify(
            {
                "success": True,
                "goal": goal,
                "workflow": workflow,
                "count": len(workflow),
            }
        )
    else:
        return jsonify({"success": False, "error": f"Workflow not found: {goal}"}), 404


@app.route("/api/workflows")
def list_workflows():
    """List all available workflows"""
    workflows = [
        {
            "id": "feature_launch",
            "name": "Feature Launch",
            "description": "Complete workflow from ideation to announcement",
            "prompt_count": 5,
            "goals": [
                "Generate feature brief",
                "Define specs",
                "Map journey",
                "Write criteria",
                "Announce",
            ],
        },
        {
            "id": "retention_improvement",
            "name": "Retention Improvement",
            "description": "Reduce churn and improve user retention",
            "prompt_count": 5,
            "goals": [
                "Retention levers",
                "Churn prediction",
                "Lifecycle",
                "Pain points",
                "Success KPIs",
            ],
        },
        {
            "id": "enterprise_expansion",
            "name": "Enterprise Expansion",
            "description": "Expand into B2B and enterprise markets",
            "prompt_count": 5,
            "goals": ["Strategy", "Personas", "Permissions", "SLAs", "Pricing"],
        },
        {
            "id": "quarterly_planning",
            "name": "Quarterly Planning",
            "description": "Plan your quarterly product roadmap",
            "prompt_count": 5,
            "goals": ["Roadmap", "OKRs", "Innovation", "KPIs", "Collaboration"],
        },
    ]
    return jsonify({"success": True, "workflows": workflows})


@app.route("/api/execute", methods=["POST"])
def execute_prompt():
    """Execute a prompt (demo - tracks execution)"""
    data = request.json
    prompt_id = data.get("prompt_id")
    context = data.get("context", {})

    prompt = manager.get_prompt(prompt_id)
    if not prompt:
        return jsonify({"success": False, "error": "Prompt not found"}), 404

    # Create execution record
    execution = {
        "id": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        "prompt_id": prompt_id,
        "prompt": prompt["prompt"],
        "executed_at": datetime.now().isoformat(),
        "context": context,
        "status": "completed",
    }
    executions.append(execution)

    return jsonify({"success": True, "execution": execution, "prompt": prompt})


@app.route("/api/executions")
def get_executions():
    """Get execution history"""
    return jsonify(
        {
            "success": True,
            "executions": executions[-50:],  # Last 50
            "count": len(executions),
        }
    )


@app.route("/api/stats")
def get_stats():
    """Get usage statistics"""
    all_prompts = manager.get_all_prompts()

    # Count by complexity
    complexity_counts = {}
    for prompt in all_prompts:
        comp = prompt["complexity"]
        complexity_counts[comp] = complexity_counts.get(comp, 0) + 1

    # Count by type
    type_counts = {}
    for prompt in all_prompts:
        type_ = prompt["type"]
        type_counts[type_] = type_counts.get(type_, 0) + 1

    return jsonify(
        {
            "success": True,
            "stats": {
                "total_prompts": len(all_prompts),
                "total_categories": len(manager.get_categories()),
                "total_executions": len(executions),
                "complexity_distribution": complexity_counts,
                "type_distribution": type_counts,
            },
        }
    )


# ============================================================================
# Error Handlers
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Product Management Prompts Service")
    print("=" * 80)
    print(f"📝 Total Prompts: {manager.prompts_data['metadata']['total_prompts']}")
    print(f"📂 Categories: {len(manager.get_categories())}")
    print(f"🌐 Web Interface: http://0.0.0.0:5001")
    print(f"📡 API Base: http://0.0.0.0:5001/api")
    print("=" * 80)
    print("\n✨ Starting server...\n")

    app.run(host="0.0.0.0", port=5001, debug=True)
