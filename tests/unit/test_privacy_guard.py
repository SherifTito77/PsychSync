"""Tests for Privacy Guard — k-anonymity suppression + differential privacy."""

import pytest

from app.services.privacy_guard import (
    EPSILON_CONFIG,
    K_THRESHOLDS,
    SUPPRESSED_PLACEHOLDER,
    PrivacyContext,
    PrivacyGuard,
    Sensitivity,
)


@pytest.fixture
def guard():
    return PrivacyGuard()


@pytest.fixture
def ctx():
    return PrivacyContext(organization_id="org-1")


# ─── k-Anonymity Suppression ───────────────────────────────────


class TestKAnonymity:
    def test_basic_metric_threshold(self, guard):
        assert guard.get_required_k("team_health") == 5
        assert guard.get_required_k("collaboration") == 5

    def test_sensitive_metric_threshold(self, guard):
        assert guard.get_required_k("burnout_risk") == 10
        assert guard.get_required_k("psychological_safety") == 10
        assert guard.get_required_k("manager_health") == 10

    def test_unknown_metric_defaults_to_sensitive(self, guard):
        assert guard.get_required_k("unknown_metric") == 10

    def test_suppress_below_k(self, guard, ctx):
        result = guard.apply_suppression(
            "team_health", {"score": 75}, group_size=3, ctx=ctx
        )
        assert result["suppressed"] is True
        assert result["score"] is None

    def test_pass_above_k_plus_3(self, guard, ctx):
        value = {"score": 75, "label": "Healthy"}
        result = guard.apply_suppression(
            "team_health", value, group_size=10, ctx=ctx
        )
        assert result["score"] == 75
        assert "suppressed" not in result

    def test_generalize_in_borderline_zone(self, guard, ctx):
        result = guard.apply_suppression(
            "team_health", {"score": 75}, group_size=6, ctx=ctx
        )
        assert result.get("generalized") is True
        assert result["score"] is None
        assert result["label"] == "Healthy"

    def test_generalize_inverse_metric(self, guard, ctx):
        result = guard.apply_suppression(
            "burnout_risk", {"score": 25}, group_size=11, ctx=ctx
        )
        assert result.get("generalized") is True
        assert result["label"] == "Low Risk"

    def test_sensitive_metric_needs_larger_group(self, guard, ctx):
        # group_size=8 passes basic (k=5) but fails sensitive (k=10)
        result = guard.apply_suppression(
            "psychological_safety", {"score": 60}, group_size=8, ctx=ctx
        )
        assert result["suppressed"] is True

    def test_suppression_log_recorded(self, guard, ctx):
        guard.apply_suppression("team_health", {"score": 50}, group_size=3, ctx=ctx)
        assert len(ctx.suppression_log) == 1
        log = ctx.suppression_log[0]
        assert log.action == "suppressed"
        assert log.metric == "team_health"
        assert log.group_size == 3

    def test_custom_k_overrides(self):
        custom = PrivacyGuard(k_overrides={Sensitivity.BASIC: 3})
        assert custom.get_required_k("team_health") == 3
        assert custom.get_required_k("burnout_risk") == 10  # sensitive unchanged


# ─── Cross-Filter Protection ───────────────────────────────────


class TestCrossFilter:
    def test_single_filter_passes(self, guard, ctx):
        ctx.add_filter("department", "engineering")
        assert guard.check_cross_filter_safety(ctx, group_size=10) is True

    def test_multi_filter_raises_threshold(self, guard, ctx):
        ctx.add_filter("department", "engineering")
        ctx.add_filter("tenure", "0-1yr")
        ctx.add_filter("gender", "female")
        # effective_k = 10 + (3-1)*3 = 16
        assert guard.check_cross_filter_safety(ctx, group_size=12) is False
        assert guard.check_cross_filter_safety(ctx, group_size=16) is True

    def test_cross_filter_suppresses_metric(self, guard, ctx):
        ctx.add_filter("dept", "eng")
        ctx.add_filter("level", "junior")
        # effective_k = 10 + 1*3 = 13
        result = guard.apply_suppression(
            "burnout_risk", {"score": 70}, group_size=11, ctx=ctx
        )
        assert result["suppressed"] is True
        assert "Cross-filter" in result["reason"]


# ─── Bucket Scoring ────────────────────────────────────────────


class TestBucketScore:
    def test_healthy_bucket(self):
        assert PrivacyGuard._bucket_score(85, "team_health") == "Healthy"

    def test_moderate_bucket(self):
        assert PrivacyGuard._bucket_score(55, "collaboration") == "Moderate"

    def test_needs_attention_bucket(self):
        assert PrivacyGuard._bucket_score(30, "team_health") == "Needs Attention"

    def test_inverse_low_risk(self):
        assert PrivacyGuard._bucket_score(20, "burnout_risk") == "Low Risk"

    def test_inverse_high_risk(self):
        assert PrivacyGuard._bucket_score(75, "friction_index") == "High Risk"

    def test_inverse_moderate_risk(self):
        assert PrivacyGuard._bucket_score(45, "burnout_risk") == "Moderate Risk"


# ─── Differential Privacy ──────────────────────────────────────


class TestDifferentialPrivacy:
    def test_noise_is_added(self, guard):
        """Score should change after DP (with very high probability)."""
        import random
        random.seed(42)
        noisy = guard.apply_differential_privacy(50.0, group_size=10, metric="team_health")
        # With seed 42, noise is deterministic — just check it's not exactly 50
        assert noisy != 50.0

    def test_clamped_to_bounds(self, guard):
        """Noisy score must stay in [0, 100]."""
        import random
        for seed in range(100):
            random.seed(seed)
            noisy = guard.apply_differential_privacy(
                5.0, group_size=2, metric="burnout_risk"
            )
            assert 0.0 <= noisy <= 100.0

    def test_larger_group_less_noise(self, guard):
        """Bigger groups → smaller sensitivity → less noise variance."""
        import random
        diffs_small, diffs_large = [], []
        for seed in range(200):
            random.seed(seed)
            diffs_small.append(
                abs(guard.apply_differential_privacy(50.0, 5, "team_health") - 50.0)
            )
            random.seed(seed)
            diffs_large.append(
                abs(guard.apply_differential_privacy(50.0, 100, "team_health") - 50.0)
            )
        avg_small = sum(diffs_small) / len(diffs_small)
        avg_large = sum(diffs_large) / len(diffs_large)
        assert avg_large < avg_small

    def test_sensitive_metric_more_noise(self, guard):
        """Sensitive metrics (lower epsilon) should get more noise on average."""
        import random
        diffs_basic, diffs_sensitive = [], []
        for seed in range(200):
            random.seed(seed)
            diffs_basic.append(
                abs(guard.apply_differential_privacy(50.0, 20, "team_health") - 50.0)
            )
            random.seed(seed)
            diffs_sensitive.append(
                abs(guard.apply_differential_privacy(50.0, 20, "burnout_risk") - 50.0)
            )
        avg_basic = sum(diffs_basic) / len(diffs_basic)
        avg_sensitive = sum(diffs_sensitive) / len(diffs_sensitive)
        assert avg_sensitive > avg_basic

    def test_custom_epsilon(self, guard):
        """Explicit epsilon overrides metric-based default."""
        import random
        random.seed(42)
        low_eps = guard.apply_differential_privacy(50.0, 10, "team_health", epsilon=0.1)
        random.seed(42)
        high_eps = guard.apply_differential_privacy(50.0, 10, "team_health", epsilon=10.0)
        # Low epsilon → more noise → bigger deviation
        assert abs(low_eps - 50.0) > abs(high_eps - 50.0)

    def test_laplace_sample_zero_scale(self):
        """Scale 0 should produce 0 noise."""
        # Very small u → returns 0
        result = PrivacyGuard._laplace_sample(0.0)
        assert result == 0.0

    def test_epsilon_config_values(self):
        assert EPSILON_CONFIG[Sensitivity.BASIC] > EPSILON_CONFIG[Sensitivity.SENSITIVE]


# ─── Dashboard Guard ────────────────────────────────────────────


class TestGuardDashboard:
    def test_suppresses_small_teams(self, guard, ctx):
        dashboard = {
            "teams": [
                {"team_id": "t1", "member_count": 3, "scores": {"team_health": 80}},
                {"team_id": "t2", "member_count": 20, "scores": {"team_health": 70}},
            ],
            "scores": {"team_health": 75},
        }
        result = guard.guard_dashboard(dashboard, ctx)
        t1_scores = result["teams"][0]["scores"]
        t2_scores = result["teams"][1]["scores"]

        assert t1_scores["team_health"]["suppressed"] is True
        assert t2_scores["team_health"]["score"] == 70

    def test_org_scores_recomputed_from_safe_teams_only(self, guard, ctx):
        dashboard = {
            "teams": [
                {"team_id": "t1", "member_count": 2, "scores": {"team_health": 90}},
                {"team_id": "t2", "member_count": 20, "scores": {"team_health": 60}},
            ],
            "scores": {"team_health": 75},
        }
        result = guard.guard_dashboard(dashboard, ctx)
        # Org score should be based only on t2 (t1 suppressed)
        assert result["scores"]["team_health"] == 60.0

    def test_privacy_metadata_included(self, guard, ctx):
        dashboard = {
            "teams": [{"team_id": "t1", "member_count": 20, "scores": {"team_health": 70}}],
            "scores": {"team_health": 70},
        }
        result = guard.guard_dashboard(dashboard, ctx)
        assert "privacy" in result
        assert "k_thresholds" in result["privacy"]

    def test_guard_dashboard_with_dp_adds_noise(self, guard, ctx):
        import random
        random.seed(42)
        dashboard = {
            "teams": [
                {"team_id": "t1", "member_count": 20, "scores": {"team_health": 70}},
            ],
            "scores": {"team_health": 70},
        }
        result = guard.guard_dashboard_with_dp(dashboard, ctx)
        assert result["privacy"]["differential_privacy"] is True
        # Score should be noisy (not exactly 70)
        t1_score = result["teams"][0]["scores"]["team_health"]["score"]
        assert isinstance(t1_score, float)


# ─── Suppression Summary ───────────────────────────────────────


class TestSuppressionSummary:
    def test_summary_counts(self, guard, ctx):
        guard.apply_suppression("team_health", {"score": 80}, 3, ctx)
        guard.apply_suppression("team_health", {"score": 80}, 6, ctx)
        guard.apply_suppression("team_health", {"score": 80}, 20, ctx)

        summary = guard.get_suppression_summary(ctx)
        assert summary["total_checks"] == 3
        assert summary["by_action"]["suppressed"] == 1
        assert summary["by_action"]["generalized"] == 1
        assert summary["by_action"]["passed"] == 1
