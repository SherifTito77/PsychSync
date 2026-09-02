"""
Git/GitHub Metadata Analysis Service

Analyzes Git METADATA ONLY — commit timestamps, file change counts,
PR lifecycle metrics, review patterns. Never reads code diffs or
commit message content beyond length.

Input signals (per developer):
  - commit frequency and timing (timestamps only)
  - lines changed (additions + deletions, aggregate counts)
  - file count per commit (breadth of change)
  - PR open → review → merge cycle time
  - review turnaround time
  - after-hours and weekend commit ratio
  - branch lifetime and merge frequency

Output behavioral signals:
  - work_intensity (commit volume + code churn)
  - boundary_erosion (after-hours/weekend commits)
  - review_bottleneck (slow reviews blocking flow)
  - collaboration_breadth (cross-repo, cross-team PRs)
  - burnout_risk composite

Privacy guarantees:
  - No commit message content (only character length)
  - No code diffs or file contents
  - No branch names or PR titles/descriptions
  - Only aggregate counts and timestamps

Required GitHub scopes (metadata-only):
  - repo (commit metadata, PR metadata)
  - read:org (team membership for cross-team analysis)
  - No: contents (would allow reading file content)
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================================================================
# NORMALIZED SCHEMA — timestamps and counts only
# ==================================================================


class CommitTimeOfDay(str, Enum):
    BUSINESS = "business"  # 9-18
    EVENING = "evening"  # 18-22
    NIGHT = "night"  # 22-06
    EARLY = "early"  # 06-09


@dataclass
class GitCommitRecord:
    """One commit's metadata — no message content, no diff."""

    sha: str
    author_id: str
    timestamp: datetime
    files_changed: int
    additions: int
    deletions: int
    is_merge: bool
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class PRMetadataRecord:
    """Pull request lifecycle metadata — no title, no description, no diff."""

    pr_id: str
    author_id: str
    created_at: datetime
    first_review_at: Optional[datetime]
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    review_count: int
    reviewer_count: int
    comments_count: int
    additions: int
    deletions: int
    files_changed: int
    is_merged: bool
    ci_checks_passed: int = 0
    ci_checks_failed: int = 0


@dataclass
class GitMetadataSignals:
    """Behavioral signals derived from Git/GitHub metadata analysis."""

    # Volume
    avg_daily_commits: float
    avg_daily_lines_changed: float
    total_commits: int
    total_prs: int

    # Code churn
    avg_additions_per_commit: float
    avg_deletions_per_commit: float
    avg_files_per_commit: float
    churn_ratio: float  # deletions / (additions + deletions)

    # Timing
    after_hours_ratio: float
    weekend_ratio: float
    peak_hour: int
    hourly_distribution: List[int]

    # PR lifecycle
    avg_pr_cycle_hours: float  # open → merge
    avg_review_wait_hours: float  # open → first review
    p90_review_wait_hours: float
    avg_reviews_per_pr: float
    pr_merge_rate: float  # merged / total

    # Collaboration
    avg_reviewers_per_pr: float
    review_turnaround_hours: float

    # Composite scores (0-100, higher = more concerning)
    work_intensity_score: float
    boundary_erosion_score: float
    review_bottleneck_score: float
    quality_degradation_score: float  # CI failure trend
    burnout_risk_score: float

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ==================================================================
# ABSTRACT CONNECTOR
# ==================================================================


class GitMetadataConnector(ABC):
    """Base interface for Git metadata connectors.

    Implementations must NEVER fetch file contents or diffs.
    Only commit/PR metadata (timestamps, counts, lifecycle).
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_commits(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[GitCommitRecord]: ...

    @abstractmethod
    async def fetch_prs(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[PRMetadataRecord]: ...


# ==================================================================
# GITHUB API CONNECTOR
# ==================================================================


class GitHubMetadataConnector(GitMetadataConnector):
    """GitHub API connector — commit and PR metadata only.

    Uses:
      GET /repos/{owner}/{repo}/commits — timestamps, stats
      GET /repos/{owner}/{repo}/pulls — lifecycle timestamps
      GET /repos/{owner}/{repo}/pulls/{n}/reviews — review timestamps

    Never uses:
      GET /repos/{owner}/{repo}/contents — would expose code
      GET /repos/{owner}/{repo}/commits/{sha} with diff — would expose patches
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        token: str = "",
        org: str = "",
        repos: Optional[List[str]] = None,
    ):
        self.token = token
        self.org = org
        self.repos = repos or []

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.token),
            "provider": "github_metadata",
            "scopes": ["repo (metadata only)", "read:org"],
            "note": "Fetches commit/PR timestamps and counts — never reads code",
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    async def fetch_commits(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[GitCommitRecord]:
        if not self.token:
            return []

        records: List[GitCommitRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                for repo in self.repos:
                    page = 1
                    while True:
                        resp = await client.get(
                            f"https://api.github.com/repos/{self.org}/{repo}/commits",
                            headers=self._headers(),
                            params={
                                "author": user_id,
                                "since": start.isoformat() + "Z",
                                "until": end.isoformat() + "Z",
                                "per_page": 100,
                                "page": page,
                            },
                        )
                        resp.raise_for_status()
                        commits = resp.json()
                        if not commits:
                            break

                        # List endpoint lacks stats — fetch per commit
                        for c in commits:
                            sha = c.get("sha", "")
                            if sha:
                                detail = await self._fetch_commit_detail(
                                    client, repo, sha
                                )
                                if detail:
                                    c.update(detail)
                            record = self._normalize_commit(c, user_id)
                            if record:
                                records.append(record)
                        page += 1

            logger.info(
                "GitHub: fetched %d commit records for %s", len(records), user_id
            )
        except ImportError:
            logger.warning("httpx not installed — GitHub connector disabled")
        except Exception as e:
            logger.error("GitHub commit fetch error: %s", e)
        return records

    async def _fetch_commit_detail(
        self,
        client,
        repo: str,
        sha: str,
    ) -> Optional[Dict]:
        """Fetch individual commit for stats (additions/deletions/files_changed)."""
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{self.org}/{repo}/commits/{sha}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "stats": data.get("stats", {}),
                    "files": data.get("files", []),
                }
        except Exception:
            pass
        return None

    async def fetch_prs(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[PRMetadataRecord]:
        if not self.token:
            return []

        records: List[PRMetadataRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                for repo in self.repos:
                    resp = await client.get(
                        f"https://api.github.com/repos/{self.org}/{repo}/pulls",
                        headers=self._headers(),
                        params={
                            "state": "all",
                            "sort": "created",
                            "direction": "desc",
                            "per_page": 100,
                        },
                    )
                    resp.raise_for_status()
                    prs = resp.json()

                    for pr in prs:
                        created = datetime.fromisoformat(
                            pr["created_at"].replace("Z", "+00:00")
                        )
                        if created < start:
                            break
                        if created > end:
                            continue

                        login = pr.get("user", {}).get("login", "")
                        if login != user_id:
                            continue

                        record = await self._normalize_pr(pr, client, repo)
                        if record:
                            records.append(record)

            logger.info("GitHub: fetched %d PR records for %s", len(records), user_id)
        except ImportError:
            logger.warning("httpx not installed — GitHub connector disabled")
        except Exception as e:
            logger.error("GitHub PR fetch error: %s", e)
        return records

    def _normalize_commit(self, data: dict, user_id: str) -> Optional[GitCommitRecord]:
        try:
            commit_data = data.get("commit", {})
            author_date = commit_data.get("author", {}).get("date", "")
            timestamp = datetime.fromisoformat(author_date.replace("Z", "+00:00"))

            stats = data.get("stats", {})
            parents = data.get("parents", [])

            return GitCommitRecord(
                sha=data.get("sha", "")[:8],
                author_id=user_id,
                timestamp=timestamp,
                files_changed=len(data.get("files", [])),
                additions=stats.get("additions", 0),
                deletions=stats.get("deletions", 0),
                is_merge=len(parents) > 1,
                is_after_hours=self._is_after_hours(timestamp),
                is_weekend=timestamp.weekday() >= 5,
            )
        except Exception:
            return None

    async def _normalize_pr(
        self,
        pr: dict,
        client,
        repo: str,
    ) -> Optional[PRMetadataRecord]:
        try:
            pr_number = pr.get("number", 0)
            created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
            merged = None
            if pr.get("merged_at"):
                merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
            closed = None
            if pr.get("closed_at"):
                closed = datetime.fromisoformat(pr["closed_at"].replace("Z", "+00:00"))

            # PR list endpoint lacks stats — fetch individual PR
            additions = pr.get("additions", 0)
            deletions = pr.get("deletions", 0)
            files_changed = pr.get("changed_files", 0)
            if additions == 0 and deletions == 0 and pr_number:
                detail = await self._fetch_pr_detail(client, repo, pr_number)
                if detail:
                    additions = detail.get("additions", 0)
                    deletions = detail.get("deletions", 0)
                    files_changed = detail.get("changed_files", 0)

            # Fetch review timestamps using stable API URL
            first_review = None
            review_count = 0
            reviewer_ids: set = set()
            try:
                review_url = (
                    f"https://api.github.com/repos/{self.org}/{repo}"
                    f"/pulls/{pr_number}/reviews"
                )
                reviews_resp = await client.get(
                    review_url,
                    headers=self._headers(),
                )
                if reviews_resp.status_code == 200:
                    reviews = reviews_resp.json()
                    review_count = len(reviews)
                    for r in reviews:
                        reviewer_ids.add(r.get("user", {}).get("login", ""))
                        if r.get("submitted_at") and not first_review:
                            first_review = datetime.fromisoformat(
                                r["submitted_at"].replace("Z", "+00:00")
                            )
            except Exception:
                pass

            # Fetch CI check-runs for the head SHA
            ci_passed, ci_failed = 0, 0
            head_sha = pr.get("head", {}).get("sha", "")
            if head_sha:
                ci_passed, ci_failed = await self._fetch_check_runs(
                    client,
                    repo,
                    head_sha,
                )

            return PRMetadataRecord(
                pr_id=str(pr_number),
                author_id=pr.get("user", {}).get("login", ""),
                created_at=created,
                first_review_at=first_review,
                merged_at=merged,
                closed_at=closed,
                review_count=review_count,
                reviewer_count=len(reviewer_ids),
                comments_count=pr.get("comments", 0) + pr.get("review_comments", 0),
                additions=additions,
                deletions=deletions,
                files_changed=files_changed,
                is_merged=pr.get("merged", False),
                ci_checks_passed=ci_passed,
                ci_checks_failed=ci_failed,
            )
        except Exception:
            return None

    async def _fetch_pr_detail(
        self,
        client,
        repo: str,
        pr_number: int,
    ) -> Optional[Dict]:
        """Fetch single PR for stats (additions/deletions/changed_files)."""
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{self.org}/{repo}/pulls/{pr_number}",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    async def _fetch_check_runs(
        self,
        client,
        repo: str,
        sha: str,
    ) -> tuple:
        """Fetch CI check-run counts for a commit SHA. Returns (passed, failed)."""
        try:
            resp = await client.get(
                f"https://api.github.com/repos/{self.org}/{repo}/commits/{sha}/check-runs",
                headers=self._headers(),
                params={"per_page": 100},
            )
            if resp.status_code == 200:
                runs = resp.json().get("check_runs", [])
                passed = sum(1 for r in runs if r.get("conclusion") == "success")
                failed = sum(
                    1 for r in runs if r.get("conclusion") in ("failure", "timed_out")
                )
                return passed, failed
        except Exception:
            pass
        return 0, 0

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ==================================================================
# BEHAVIORAL ANALYZER
# ==================================================================


class GitMetadataAnalyzer:
    """Extracts behavioral signals from Git/GitHub metadata.

    Never sees code content, commit messages, or diffs.
    Works only with timestamps, counts, and lifecycle durations.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def analyze(
        self,
        commits: List[GitCommitRecord],
        prs: List[PRMetadataRecord],
        days: int = 14,
    ) -> GitMetadataSignals:
        if not commits and not prs:
            return self._empty_signals()

        # Volume
        non_merge = [c for c in commits if not c.is_merge]
        avg_daily_commits = len(non_merge) / max(days, 1)
        total_lines = sum(c.additions + c.deletions for c in non_merge)
        avg_daily_lines = total_lines / max(days, 1)

        # Churn
        total_add = sum(c.additions for c in non_merge) or 1
        total_del = sum(c.deletions for c in non_merge)
        avg_add = total_add / max(len(non_merge), 1)
        avg_del = total_del / max(len(non_merge), 1)
        avg_files = sum(c.files_changed for c in non_merge) / max(len(non_merge), 1)
        churn = total_del / (total_add + total_del) if (total_add + total_del) else 0

        # Timing
        after_hours = [c for c in non_merge if c.is_after_hours]
        weekend = [c for c in non_merge if c.is_weekend]
        ah_ratio = len(after_hours) / max(len(non_merge), 1)
        wk_ratio = len(weekend) / max(len(non_merge), 1)

        hourly = self._hourly_distribution(non_merge)
        peak_hour = hourly.index(max(hourly)) if any(hourly) else 10

        # PR lifecycle
        pr_cycles = []
        review_waits = []
        for pr in prs:
            if pr.merged_at:
                cycle = (pr.merged_at - pr.created_at).total_seconds() / 3600
                pr_cycles.append(cycle)
            if pr.first_review_at:
                wait = (pr.first_review_at - pr.created_at).total_seconds() / 3600
                review_waits.append(wait)

        avg_cycle = sum(pr_cycles) / len(pr_cycles) if pr_cycles else 0
        avg_review_wait = sum(review_waits) / len(review_waits) if review_waits else 0
        sorted_waits = sorted(review_waits) if review_waits else [0]
        p90_idx = int(len(sorted_waits) * 0.9)
        p90_wait = sorted_waits[min(p90_idx, len(sorted_waits) - 1)]

        avg_reviews = sum(pr.review_count for pr in prs) / max(len(prs), 1)
        avg_reviewers = sum(pr.reviewer_count for pr in prs) / max(len(prs), 1)
        merged_count = sum(1 for pr in prs if pr.is_merged)
        merge_rate = merged_count / max(len(prs), 1)

        review_turnaround = avg_review_wait  # simplified

        # Composite scores
        intensity = self._work_intensity_score(
            avg_daily_commits, avg_daily_lines, avg_files
        )
        boundary = self._boundary_erosion_score(ah_ratio, wk_ratio)
        bottleneck = self._review_bottleneck_score(
            avg_review_wait, p90_wait, avg_reviews
        )
        quality_deg = self._quality_degradation_score(prs, days)
        burnout, label = self._burnout_risk_score(
            intensity,
            boundary,
            bottleneck,
            wk_ratio,
            avg_daily_commits,
        )

        daily = self._daily_breakdown(non_merge, prs, days)
        recs = self._generate_recommendations(
            avg_daily_commits,
            ah_ratio,
            wk_ratio,
            avg_review_wait,
            intensity,
            boundary,
            bottleneck,
        )

        return GitMetadataSignals(
            avg_daily_commits=round(avg_daily_commits, 1),
            avg_daily_lines_changed=round(avg_daily_lines, 1),
            total_commits=len(non_merge),
            total_prs=len(prs),
            avg_additions_per_commit=round(avg_add, 1),
            avg_deletions_per_commit=round(avg_del, 1),
            avg_files_per_commit=round(avg_files, 1),
            churn_ratio=round(churn, 3),
            after_hours_ratio=round(ah_ratio, 3),
            weekend_ratio=round(wk_ratio, 3),
            peak_hour=peak_hour,
            hourly_distribution=hourly,
            avg_pr_cycle_hours=round(avg_cycle, 1),
            avg_review_wait_hours=round(avg_review_wait, 1),
            p90_review_wait_hours=round(p90_wait, 1),
            avg_reviews_per_pr=round(avg_reviews, 1),
            pr_merge_rate=round(merge_rate, 3),
            avg_reviewers_per_pr=round(avg_reviewers, 1),
            review_turnaround_hours=round(review_turnaround, 1),
            work_intensity_score=round(intensity, 1),
            boundary_erosion_score=round(boundary, 1),
            review_bottleneck_score=round(bottleneck, 1),
            quality_degradation_score=round(quality_deg, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # -- Component scores --

    def _work_intensity_score(
        self,
        daily_commits: float,
        daily_lines: float,
        avg_files: float,
    ) -> float:
        """0-100: sustained high code output pressure."""
        # 5 commits/day normal, 15+ high
        commit_pressure = min(100, (daily_commits / 15) * 100)
        # 200 lines/day normal, 800+ high
        line_pressure = min(100, (daily_lines / 800) * 100)
        # Many files per commit = wide blast radius
        breadth_penalty = min(20, max(0, avg_files - 5) * 4)
        return min(100, commit_pressure * 0.45 + line_pressure * 0.40 + breadth_penalty)

    def _boundary_erosion_score(
        self,
        ah_ratio: float,
        weekend_ratio: float,
    ) -> float:
        """0-100: coding outside work hours."""
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, weekend_ratio * 400)
        return ah_component * 0.55 + wk_component * 0.45

    def _review_bottleneck_score(
        self,
        avg_wait_hours: float,
        p90_wait_hours: float,
        avg_reviews: float,
    ) -> float:
        """0-100: PRs blocked waiting for review.

        Long review waits create context-switching and frustration,
        both burnout contributors.
        """
        # 4h wait normal, 48h+ critical
        wait_pressure = min(100, (avg_wait_hours / 48) * 100)
        # P90 captures worst-case experiences
        p90_pressure = min(100, (p90_wait_hours / 72) * 100)
        # Too few reviews = rubber-stamping (different problem)
        review_deficit = min(20, max(0, (1 - avg_reviews)) * 20)
        return min(100, wait_pressure * 0.50 + p90_pressure * 0.30 + review_deficit)

    def _quality_degradation_score(
        self, prs: List[PRMetadataRecord], days: int
    ) -> float:
        """0-100: CI failure rate trending up over the window.

        Build failures per developer rising over a 4-week window is a
        lagging burnout signal — by the time code quality drops, the
        person is already deep in.
        """
        if not prs or days < 7:
            return 0.0

        prs_with_ci = [p for p in prs if (p.ci_checks_passed + p.ci_checks_failed) > 0]
        if not prs_with_ci:
            return 0.0

        total_checks = sum(p.ci_checks_passed + p.ci_checks_failed for p in prs_with_ci)
        total_failed = sum(p.ci_checks_failed for p in prs_with_ci)

        if total_checks == 0:
            return 0.0

        failure_rate = total_failed / total_checks

        # Compare first half vs second half for trend
        sorted_prs = sorted(prs_with_ci, key=lambda p: p.created_at)
        mid = len(sorted_prs) // 2
        if mid > 0:
            first_half = sorted_prs[:mid]
            second_half = sorted_prs[mid:]

            first_fails = sum(p.ci_checks_failed for p in first_half)
            first_total = sum(
                p.ci_checks_passed + p.ci_checks_failed for p in first_half
            )
            second_fails = sum(p.ci_checks_failed for p in second_half)
            second_total = sum(
                p.ci_checks_passed + p.ci_checks_failed for p in second_half
            )

            first_rate = first_fails / first_total if first_total else 0
            second_rate = second_fails / second_total if second_total else 0

            # Rising trend amplifier
            trend_amp = max(0, (second_rate - first_rate) * 100)
        else:
            trend_amp = 0.0

        # Base: >20% failure rate is concerning, >50% is critical
        base = min(100, failure_rate * 200)

        return min(100, base * 0.6 + trend_amp * 0.4)

    def _burnout_risk_score(
        self,
        intensity: float,
        boundary: float,
        bottleneck: float,
        weekend_ratio: float,
        daily_commits: float,
    ) -> tuple:
        """Composite burnout risk from Git metadata. Returns (score, label).

        Git burnout signature: high intensity + poor boundaries + review frustration.
        Weekend coding is weighted extra — it's a strong early warning signal.
        """
        base = boundary * 0.40 + intensity * 0.30 + bottleneck * 0.15

        # Interaction: high output AND after-hours = compounding
        interaction = (intensity / 100) * (boundary / 100) * 20

        # Weekend coding amplifier
        weekend_amp = min(10, max(0, (weekend_ratio - 0.10) * 100))

        # Sustained high output amplifier (>10 commits/day consistently)
        sustained_amp = min(5, max(0, (daily_commits - 10) * 1))

        score = min(100, base + interaction + weekend_amp + sustained_amp)

        if score >= 70:
            label = "Critical"
        elif score >= 45:
            label = "Elevated"
        elif score >= 25:
            label = "Monitor"
        else:
            label = "Healthy"

        return round(score, 1), label

    # -- Helpers --

    def _hourly_distribution(self, commits: List[GitCommitRecord]) -> List[int]:
        buckets = [0] * 24
        for c in commits:
            buckets[c.timestamp.hour] += 1
        return buckets

    def _daily_breakdown(
        self,
        commits: List[GitCommitRecord],
        prs: List[PRMetadataRecord],
        days: int,
    ) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[GitCommitRecord]] = defaultdict(list)
        for c in commits:
            by_day[c.timestamp.strftime("%Y-%m-%d")].append(c)

        pr_by_day: Dict[str, int] = defaultdict(int)
        for pr in prs:
            pr_by_day[pr.created_at.strftime("%Y-%m-%d")] += 1

        result = []
        for day_str in sorted(set(list(by_day.keys()) + list(pr_by_day.keys()))):
            day_commits = by_day.get(day_str, [])
            result.append(
                {
                    "date": day_str,
                    "commits": len(day_commits),
                    "additions": sum(c.additions for c in day_commits),
                    "deletions": sum(c.deletions for c in day_commits),
                    "files_changed": sum(c.files_changed for c in day_commits),
                    "after_hours_commits": sum(
                        1 for c in day_commits if c.is_after_hours
                    ),
                    "prs_opened": pr_by_day.get(day_str, 0),
                }
            )
        return result

    def _generate_recommendations(
        self,
        daily_commits: float,
        ah_ratio: float,
        wk_ratio: float,
        review_wait: float,
        intensity: float,
        boundary: float,
        bottleneck: float,
    ) -> List[str]:
        recs = []
        if daily_commits > 12:
            recs.append(
                f"Commit frequency ({daily_commits:.0f}/day) is very high. "
                "Consider whether this pace is sustainable or driven by urgency."
            )
        if ah_ratio > 0.25:
            recs.append(
                f"{ah_ratio*100:.0f}% of commits are outside work hours. "
                "Late-night coding correlates strongly with error rates and burnout."
            )
        if wk_ratio > 0.10:
            recs.append(
                f"{wk_ratio*100:.0f}% of commits are on weekends. "
                "Protect recovery time — weekend work is one of the strongest burnout predictors."
            )
        if review_wait > 24:
            recs.append(
                f"Average PR review wait is {review_wait:.0f}h. "
                "Long waits create context-switching costs. Consider review SLAs or pairing."
            )
        if bottleneck > 50:
            recs.append(
                "Review bottleneck is high. Blocked PRs create frustration loops. "
                "Consider rotating reviewers or async-first review practices."
            )
        if intensity > 60 and boundary > 40:
            recs.append(
                "High output combined with boundary erosion is a classic burnout pattern. "
                "Discuss sustainable pace with your team lead."
            )
        if not recs:
            recs.append(
                "Git patterns look healthy. Development pace and timing are sustainable."
            )
        return recs

    def _empty_signals(self) -> GitMetadataSignals:
        return GitMetadataSignals(
            avg_daily_commits=0,
            avg_daily_lines_changed=0,
            total_commits=0,
            total_prs=0,
            avg_additions_per_commit=0,
            avg_deletions_per_commit=0,
            avg_files_per_commit=0,
            churn_ratio=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            peak_hour=10,
            hourly_distribution=[0] * 24,
            avg_pr_cycle_hours=0,
            avg_review_wait_hours=0,
            p90_review_wait_hours=0,
            avg_reviews_per_pr=0,
            pr_merge_rate=0,
            avg_reviewers_per_pr=0,
            review_turnaround_hours=0,
            work_intensity_score=0,
            boundary_erosion_score=0,
            review_bottleneck_score=0,
            quality_degradation_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No Git metadata available. Connect GitHub to enable analysis."
            ],
        )


# ==================================================================
# REGISTRY
# ==================================================================


class GitMetadataRegistry:
    CONNECTOR_TYPES = {"github": GitHubMetadataConnector}

    def __init__(self):
        self._connectors: Dict[str, GitMetadataConnector] = {}

    def register(self, name: str, connector: GitMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered Git metadata connector: %s", name)

    def get(self, name: str) -> Optional[GitMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


git_metadata_registry = GitMetadataRegistry()
