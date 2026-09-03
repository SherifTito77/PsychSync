"""
Code Review Toxicity Signal Service

Detects hostile code review patterns from PR METADATA ONLY:
  - PR rejection asymmetry (same reviewer blocking same author)
  - Review gatekeeping (one person blocking many authors)
  - Hostile reject-to-approve ratio per reviewer→author pair
  - Review delay asymmetry (fast for some, slow for others)

Uses only PR state changes, reviewer assignments, and timestamps.
NEVER reads PR descriptions, code diffs, or review comments.

Data sources: GitHub REST/GraphQL API, GitLab API
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


@dataclass
class PRReviewRecord:
    """One PR review event — no code, diffs, or comment text."""

    pr_id: str
    pr_number: int
    author_email: str
    reviewer_email: str
    submitted_at: datetime
    state: str  # "approved", "changes_requested", "commented", "dismissed"
    review_turnaround_hours: Optional[float] = None  # time from request to review
    pr_created_at: Optional[datetime] = None
    pr_merged_at: Optional[datetime] = None
    pr_closed_at: Optional[datetime] = None
    iteration_count: int = 1  # how many review rounds this PR went through


@dataclass
class CodeReviewToxicitySignals:
    """Toxicity signals from code review patterns."""

    # Rejection patterns
    avg_rejection_rate: float
    rejection_asymmetry_score: float

    # Gatekeeping
    gatekeeping_score: float

    # Review delay
    avg_review_turnaround_hours: float
    turnaround_asymmetry_score: float

    # Review cycles
    avg_iterations: float
    excessive_iteration_prs: int

    # Composite
    toxicity_score: float
    risk_label: str

    # Fields with defaults (must come last)
    hostile_pairs: List[Dict[str, Any]] = field(default_factory=list)
    top_blockers: List[Dict[str, Any]] = field(default_factory=list)
    slowest_pair: Optional[Dict[str, Any]] = None
    signals: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CodeReviewConnector(ABC):
    """Base for code review metadata connectors.

    Must NEVER request PR descriptions, code diffs, or review comments.
    Only state changes, reviewer/author identifiers, and timestamps.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_reviews(
        self,
        org_or_repo: str,
        start: datetime,
        end: datetime,
    ) -> List[PRReviewRecord]: ...


# ══════════════════════════════════════════════════════════════════
# GITHUB CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GitHubReviewConnector(CodeReviewConnector):
    """GitHub REST API — PR review metadata only.

    Uses /repos/{owner}/{repo}/pulls/{number}/reviews
    with fields limited to: state, user.login, submitted_at
    """

    def __init__(self, token: str = "", org: str = ""):
        self.token = token
        self.org = org
        self.base_url = "https://api.github.com"

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.token and self.org),
            "provider": "github",
            "scopes": ["repo:status", "read:org"],
            "note": "PR review state only — no diffs or comments",
        }

    async def fetch_reviews(
        self,
        org_or_repo: str,
        start: datetime,
        end: datetime,
    ) -> List[PRReviewRecord]:
        if not self.token:
            return []

        records: List[PRReviewRecord] = []
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                # List repos in org
                repos_resp = await client.get(
                    f"{self.base_url}/orgs/{org_or_repo}/repos",
                    headers=headers,
                    params={"type": "all", "per_page": 50, "sort": "pushed"},
                )
                if repos_resp.status_code != 200:
                    return []

                for repo in repos_resp.json():
                    repo_name = repo["full_name"]

                    # List recent PRs
                    prs_resp = await client.get(
                        f"{self.base_url}/repos/{repo_name}/pulls",
                        headers=headers,
                        params={
                            "state": "all",
                            "per_page": 50,
                            "sort": "updated",
                            "direction": "desc",
                        },
                    )
                    if prs_resp.status_code != 200:
                        continue

                    for pr in prs_resp.json():
                        pr_created = datetime.fromisoformat(
                            pr["created_at"].replace("Z", "+00:00")
                        )
                        if pr_created < start:
                            continue

                        # Fetch reviews for this PR
                        reviews_resp = await client.get(
                            f"{self.base_url}/repos/{repo_name}/pulls/{pr['number']}/reviews",
                            headers=headers,
                        )
                        if reviews_resp.status_code != 200:
                            continue

                        author = pr.get("user", {}).get("login", "")
                        pr_merged = None
                        if pr.get("merged_at"):
                            pr_merged = datetime.fromisoformat(
                                pr["merged_at"].replace("Z", "+00:00")
                            )

                        for review in reviews_resp.json():
                            reviewer = review.get("user", {}).get("login", "")
                            if reviewer == author:
                                continue  # self-reviews don't count

                            submitted = datetime.fromisoformat(
                                review["submitted_at"].replace("Z", "+00:00")
                            )
                            turnaround = (submitted - pr_created).total_seconds() / 3600

                            records.append(
                                PRReviewRecord(
                                    pr_id=str(pr["id"]),
                                    pr_number=pr["number"],
                                    author_email=author,
                                    reviewer_email=reviewer,
                                    submitted_at=submitted,
                                    state=review.get("state", "").lower(),
                                    review_turnaround_hours=turnaround,
                                    pr_created_at=pr_created,
                                    pr_merged_at=pr_merged,
                                )
                            )

            logger.info("GitHub: fetched %d review records", len(records))
        except ImportError:
            logger.warning("httpx not installed — GitHub connector disabled")
        except Exception as e:
            logger.error("GitHub review fetch error: %s", e)
        return records

    async def _count_iterations(
        self, client, repo_name: str, pr_number: int, headers: dict
    ) -> int:
        """Count review iterations from timeline events."""
        try:
            resp = await client.get(
                f"{self.base_url}/repos/{repo_name}/pulls/{pr_number}/reviews",
                headers=headers,
            )
            if resp.status_code == 200:
                reviews = resp.json()
                changes_requested = sum(
                    1 for r in reviews if r.get("state") == "CHANGES_REQUESTED"
                )
                return changes_requested + 1
        except Exception:
            pass
        return 1


# ══════════════════════════════════════════════════════════════════
# GITLAB CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GitLabReviewConnector(CodeReviewConnector):
    """GitLab API — merge request approval metadata only."""

    def __init__(self, base_url: str = "https://gitlab.com", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.token),
            "provider": "gitlab",
            "note": "MR approval metadata — no diffs or comments",
        }

    async def fetch_reviews(
        self,
        org_or_repo: str,
        start: datetime,
        end: datetime,
    ) -> List[PRReviewRecord]:
        if not self.token:
            return []

        records: List[PRReviewRecord] = []
        try:
            import httpx

            headers = {"PRIVATE-TOKEN": self.token}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v4/groups/{org_or_repo}/merge_requests",
                    headers=headers,
                    params={
                        "state": "all",
                        "created_after": start.isoformat(),
                        "per_page": 100,
                    },
                )
                if resp.status_code != 200:
                    return []

                for mr in resp.json():
                    project_id = mr.get("project_id")
                    mr_iid = mr.get("iid")

                    # Get approvals
                    approvals_resp = await client.get(
                        f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/approvals",
                        headers=headers,
                    )
                    if approvals_resp.status_code != 200:
                        continue

                    approvals = approvals_resp.json()
                    author = mr.get("author", {}).get("username", "")
                    created = datetime.fromisoformat(
                        mr["created_at"].replace("Z", "+00:00")
                    )

                    for approver in approvals.get("approved_by", []):
                        reviewer = approver.get("user", {}).get("username", "")
                        if reviewer == author:
                            continue
                        records.append(
                            PRReviewRecord(
                                pr_id=str(mr["id"]),
                                pr_number=mr_iid,
                                author_email=author,
                                reviewer_email=reviewer,
                                submitted_at=created,
                                state="approved",
                                pr_created_at=created,
                            )
                        )

            logger.info("GitLab: fetched %d review records", len(records))
        except ImportError:
            logger.warning("httpx not installed — GitLab connector disabled")
        except Exception as e:
            logger.error("GitLab review fetch error: %s", e)
        return records


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class CodeReviewToxicityAnalyzer:
    """Detects hostile code review patterns from PR metadata.

    Three core toxicity signals:
    1. Rejection asymmetry — same reviewer rejecting same author disproportionately
    2. Gatekeeping — one reviewer blocking many different authors
    3. Turnaround asymmetry — reviewer is fast for some authors, slow for others
    """

    MIN_REVIEWS_FOR_SIGNAL = 3  # need at least 3 reviews per pair

    def analyze(
        self,
        reviews: List[PRReviewRecord],
        days: int = 30,
    ) -> CodeReviewToxicitySignals:
        if not reviews:
            return self._empty_signals()

        rejection = self._analyze_rejection_patterns(reviews)
        gatekeeping = self._analyze_gatekeeping(reviews)
        turnaround = self._analyze_turnaround_asymmetry(reviews)
        iterations = self._analyze_iterations(reviews)

        toxicity = (
            rejection["asymmetry_score"] * 0.30
            + gatekeeping["score"] * 0.25
            + turnaround["asymmetry_score"] * 0.25
            + min(100, iterations["excessive_prs"] * 10) * 0.20
        )

        signals = []
        if rejection["hostile_pairs"]:
            pairs_str = len(rejection["hostile_pairs"])
            signals.append(
                f"{pairs_str} hostile reviewer-author pair(s) with >50% rejection rate"
            )
        if gatekeeping["score"] > 40:
            for b in gatekeeping["top_blockers"][:2]:
                signals.append(
                    f"Reviewer {b['reviewer']} blocks {b['unique_authors_blocked']} "
                    f"authors at {b['rejection_rate']*100:.0f}% rejection rate"
                )
        if turnaround["asymmetry_score"] > 40:
            signals.append(
                f"Review turnaround asymmetry: "
                f"{turnaround['fastest_avg']:.1f}h vs {turnaround['slowest_avg']:.1f}h "
                "for different authors"
            )
        if iterations["excessive_prs"] > 0:
            signals.append(
                f"{iterations['excessive_prs']} PRs required >3 review rounds"
            )

        label = (
            "Critical"
            if toxicity >= 60
            else (
                "Elevated"
                if toxicity >= 35
                else "Monitor" if toxicity >= 15 else "Healthy"
            )
        )

        recs = self._generate_recommendations(
            rejection, gatekeeping, turnaround, iterations
        )

        return CodeReviewToxicitySignals(
            avg_rejection_rate=round(rejection["avg_rate"], 3),
            rejection_asymmetry_score=round(rejection["asymmetry_score"], 1),
            hostile_pairs=rejection["hostile_pairs"],
            gatekeeping_score=round(gatekeeping["score"], 1),
            top_blockers=gatekeeping["top_blockers"],
            avg_review_turnaround_hours=round(turnaround["avg_turnaround"], 1),
            turnaround_asymmetry_score=round(turnaround["asymmetry_score"], 1),
            slowest_pair=turnaround.get("slowest_pair"),
            avg_iterations=round(iterations["avg_iterations"], 1),
            excessive_iteration_prs=iterations["excessive_prs"],
            toxicity_score=round(toxicity, 1),
            risk_label=label,
            signals=signals,
            recommendations=recs,
        )

    def _analyze_rejection_patterns(
        self, reviews: List[PRReviewRecord]
    ) -> Dict[str, Any]:
        """Find reviewer→author pairs with disproportionate rejection rates."""
        pair_stats: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "rejected": 0}
        )

        for r in reviews:
            pair = (r.reviewer_email, r.author_email)
            pair_stats[pair]["total"] += 1
            if r.state in ("changes_requested", "request_changes"):
                pair_stats[pair]["rejected"] += 1

        # Org-wide rejection rate
        total = sum(s["total"] for s in pair_stats.values())
        total_rejected = sum(s["rejected"] for s in pair_stats.values())
        avg_rate = total_rejected / max(total, 1)

        # Find hostile pairs (rate > 2x org average AND >= 50%)
        hostile_pairs = []
        threshold = max(avg_rate * 2, 0.40)
        for (reviewer, author), stats in pair_stats.items():
            if stats["total"] < self.MIN_REVIEWS_FOR_SIGNAL:
                continue
            rate = stats["rejected"] / stats["total"]
            if rate >= threshold:
                hostile_pairs.append(
                    {
                        "reviewer": reviewer,
                        "author": author,
                        "rejection_rate": round(rate, 3),
                        "reviews": stats["total"],
                    }
                )

        # Asymmetry score: variance of per-pair rejection rates
        rates = [
            s["rejected"] / s["total"]
            for s in pair_stats.values()
            if s["total"] >= self.MIN_REVIEWS_FOR_SIGNAL
        ]
        if len(rates) >= 2:
            mean = sum(rates) / len(rates)
            variance = sum((r - mean) ** 2 for r in rates) / len(rates)
            asymmetry = min(100, variance * 500 + len(hostile_pairs) * 15)
        else:
            asymmetry = 0

        return {
            "avg_rate": avg_rate,
            "asymmetry_score": asymmetry,
            "hostile_pairs": sorted(
                hostile_pairs, key=lambda x: x["rejection_rate"], reverse=True
            ),
        }

    def _analyze_gatekeeping(self, reviews: List[PRReviewRecord]) -> Dict[str, Any]:
        """Detect one reviewer blocking many different authors."""
        reviewer_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "rejected": 0, "authors_blocked": set()}
        )

        for r in reviews:
            reviewer_stats[r.reviewer_email]["total"] += 1
            if r.state in ("changes_requested", "request_changes"):
                reviewer_stats[r.reviewer_email]["rejected"] += 1
                reviewer_stats[r.reviewer_email]["authors_blocked"].add(r.author_email)

        top_blockers = []
        for reviewer, stats in reviewer_stats.items():
            if stats["total"] < 5:
                continue
            rate = stats["rejected"] / stats["total"]
            blocked = len(stats["authors_blocked"])
            if rate > 0.40 and blocked >= 2:
                top_blockers.append(
                    {
                        "reviewer": reviewer,
                        "rejection_rate": round(rate, 3),
                        "unique_authors_blocked": blocked,
                        "total_reviews": stats["total"],
                    }
                )

        top_blockers.sort(key=lambda x: x["rejection_rate"], reverse=True)
        score = min(
            100,
            sum(
                b["rejection_rate"] * b["unique_authors_blocked"] * 20
                for b in top_blockers
            ),
        )

        return {"score": score, "top_blockers": top_blockers[:5]}

    def _analyze_turnaround_asymmetry(
        self, reviews: List[PRReviewRecord]
    ) -> Dict[str, Any]:
        """Detect if reviewers are fast for some authors but slow for others."""
        pair_turnarounds: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        for r in reviews:
            if r.review_turnaround_hours is not None and r.review_turnaround_hours > 0:
                pair_turnarounds[(r.reviewer_email, r.author_email)].append(
                    r.review_turnaround_hours
                )

        if not pair_turnarounds:
            return {
                "avg_turnaround": 0,
                "asymmetry_score": 0,
                "fastest_avg": 0,
                "slowest_avg": 0,
            }

        # Average turnaround per pair
        pair_avgs: Dict[Tuple[str, str], float] = {}
        for pair, times in pair_turnarounds.items():
            if len(times) >= 2:
                pair_avgs[pair] = sum(times) / len(times)

        if not pair_avgs:
            all_times = [t for times in pair_turnarounds.values() for t in times]
            return {
                "avg_turnaround": sum(all_times) / len(all_times) if all_times else 0,
                "asymmetry_score": 0,
                "fastest_avg": 0,
                "slowest_avg": 0,
            }

        all_avgs = list(pair_avgs.values())
        overall_avg = sum(all_avgs) / len(all_avgs)
        fastest = min(all_avgs)
        slowest = max(all_avgs)

        # Asymmetry: ratio between slowest and fastest
        if fastest > 0:
            ratio = slowest / fastest
            asymmetry = min(100, (ratio - 1) * 15)
        else:
            asymmetry = 0

        # Find the slowest pair
        slowest_pair_key = max(pair_avgs, key=pair_avgs.get)
        slowest_pair = {
            "reviewer": slowest_pair_key[0],
            "author": slowest_pair_key[1],
            "avg_hours": round(pair_avgs[slowest_pair_key], 1),
        }

        return {
            "avg_turnaround": overall_avg,
            "asymmetry_score": asymmetry,
            "fastest_avg": fastest,
            "slowest_avg": slowest,
            "slowest_pair": slowest_pair,
        }

    def _analyze_iterations(self, reviews: List[PRReviewRecord]) -> Dict[str, Any]:
        """Count review iterations per PR — excessive rounds indicate hostility."""
        pr_iterations: Dict[str, int] = defaultdict(int)
        for r in reviews:
            if r.state in ("changes_requested", "request_changes"):
                pr_iterations[r.pr_id] += 1

        if not pr_iterations:
            return {"avg_iterations": 1, "excessive_prs": 0}

        iterations = list(pr_iterations.values())
        avg = sum(iterations) / len(iterations) + 1  # +1 for initial submission
        excessive = sum(1 for i in iterations if i > 3)

        return {"avg_iterations": avg, "excessive_prs": excessive}

    def _generate_recommendations(
        self,
        rejection: dict,
        gatekeeping: dict,
        turnaround: dict,
        iterations: dict,
    ) -> List[str]:
        recs = []
        if rejection["hostile_pairs"]:
            recs.append(
                "Hostile reviewer-author pairs detected. "
                "Consider rotating review assignments or adding a second reviewer."
            )
        if gatekeeping["score"] > 40:
            recs.append(
                "Review gatekeeping pattern found. "
                "Distribute CODEOWNERS more broadly to reduce single-reviewer bottlenecks."
            )
        if turnaround["asymmetry_score"] > 40:
            recs.append(
                "Review turnaround varies significantly by author. "
                "Set SLA targets for review response time regardless of author."
            )
        if iterations["excessive_prs"] > 0:
            recs.append(
                f"{iterations['excessive_prs']} PRs had >3 review rounds. "
                "Encourage pre-review discussions to align on approach before coding."
            )
        if not recs:
            recs.append(
                "Code review patterns look healthy. No toxicity signals detected."
            )
        return recs

    def _empty_signals(self) -> CodeReviewToxicitySignals:
        return CodeReviewToxicitySignals(
            avg_rejection_rate=0,
            rejection_asymmetry_score=0,
            gatekeeping_score=0,
            avg_review_turnaround_hours=0,
            turnaround_asymmetry_score=0,
            avg_iterations=1,
            excessive_iteration_prs=0,
            toxicity_score=0,
            risk_label="No Data",
            signals=["No code review data available."],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class CodeReviewToxicityRegistry:
    CONNECTOR_TYPES = {
        "github": GitHubReviewConnector,
        "gitlab": GitLabReviewConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, CodeReviewConnector] = {}

    def register(self, name: str, connector: CodeReviewConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered code review connector: %s", name)

    def get(self, name: str) -> Optional[CodeReviewConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


code_review_toxicity_registry = CodeReviewToxicityRegistry()
