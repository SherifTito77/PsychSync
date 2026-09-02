"""Tests for Metadata Intelligence services — behavioral analysis from metadata-only signals."""

from datetime import date, datetime, time, timedelta

import pytest

from app.services.email_metadata_service import (
    EmailDirection,
    EmailMetadataAnalyzer,
    EmailMetadataRecord,
)
from app.services.slack_metadata_service import (
    SlackActivityRecord,
    SlackChannelType,
    SlackMetadataAnalyzer,
    SlackPresenceRecord,
)
from app.services.teams_metadata_service import (
    TeamsActivityRecord,
    TeamsActivityType,
    TeamsMetadataAnalyzer,
    TeamsPresenceRecord,
)
from app.services.computer_usage_metadata_service import (
    ActivityLevel,
    ComputerUsageAnalyzer,
    UsageBucket,
)
from app.services.badge_access_metadata_service import (
    BadgeAccessAnalyzer,
    BadgeSwipe,
    SwipeDirection,
)
from app.services.pto_patterns_metadata_service import (
    LeaveBalance,
    LeaveRecord,
    LeaveStatus,
    LeaveType,
    PTOPatternsAnalyzer,
)


# ── Helpers ───────────────────────────────────────────────────


def _workday_email(id_: str, hour: int = 10, **kwargs) -> EmailMetadataRecord:
    """Quick email record factory — defaults to healthy weekday, work-hours."""
    defaults = dict(
        id=id_,
        direction=EmailDirection.SENT,
        timestamp=datetime(2026, 8, 25, hour, 0),  # Monday
        recipient_count=1,
        is_internal=True,
        response_time_minutes=None,
        thread_depth=0,
        is_after_hours=False,
        is_weekend=False,
    )
    defaults.update(kwargs)
    return EmailMetadataRecord(**defaults)


def _slack_activity(ts: datetime, **kwargs) -> SlackActivityRecord:
    defaults = dict(
        user_id="u1",
        timestamp=ts,
        messages_sent=5,
        messages_received=3,
        channel_type=SlackChannelType.PUBLIC,
        channel_id="ch-general",
        threads_started=1,
        thread_replies=1,
        reactions_given=2,
        reactions_received=2,
        is_after_hours=False,
        is_weekend=False,
    )
    defaults.update(kwargs)
    return SlackActivityRecord(**defaults)


def _teams_activity(ts: datetime, atype: TeamsActivityType, **kwargs) -> TeamsActivityRecord:
    defaults = dict(
        user_id="u1",
        timestamp=ts,
        activity_type=atype,
        count=5,
        duration_minutes=0,
        is_private=False,
        channel_id="ch-1" if atype == TeamsActivityType.CHANNEL_MESSAGE else None,
        participants=4,
        is_after_hours=False,
        is_weekend=False,
    )
    defaults.update(kwargs)
    return TeamsActivityRecord(**defaults)


def _usage_bucket(ts: datetime, **kwargs) -> UsageBucket:
    defaults = dict(
        user_id="u1",
        timestamp=ts,
        keyboard_events_per_min=20.0,
        mouse_events_per_min=15.0,
        app_switches=3,
        is_idle=False,
        activity_level=ActivityLevel.MODERATE,
        is_after_hours=False,
        is_weekend=False,
    )
    defaults.update(kwargs)
    return UsageBucket(**defaults)


def _badge_swipe(ts: datetime, direction: SwipeDirection, **kwargs) -> BadgeSwipe:
    defaults = dict(
        user_id="u1",
        timestamp=ts,
        direction=direction,
        building="HQ",
        is_after_hours=False,
        is_weekend=False,
    )
    defaults.update(kwargs)
    return BadgeSwipe(**defaults)


# ═══════════════════════════════════════════════════════════════
# 1. EMAIL METADATA
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def email_analyzer():
    return EmailMetadataAnalyzer()


class TestEmailMetadata:
    def test_empty_input(self, email_analyzer):
        signals = email_analyzer.analyze([], days=14)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.avg_daily_sent == 0

    def test_healthy_pattern(self, email_analyzer):
        records = [
            _workday_email(str(i), hour=10 + (i % 4))
            for i in range(20)
        ]
        signals = email_analyzer.analyze(records, days=14)
        assert signals.burnout_risk_score < 25
        assert signals.risk_label == "Healthy"

    def test_burnout_after_hours_heavy(self, email_analyzer):
        records = [
            _workday_email(
                str(i),
                hour=23,
                is_after_hours=True,
                is_weekend=(i % 3 == 0),
                response_time_minutes=3.0,
                direction=EmailDirection.SENT if i % 2 == 0 else EmailDirection.RECEIVED,
            )
            for i in range(80)
        ]
        signals = email_analyzer.analyze(records, days=7)
        assert signals.burnout_risk_score >= 45
        assert signals.risk_label in ("Elevated", "Critical")
        assert signals.after_hours_ratio > 0.5

    def test_single_record(self, email_analyzer):
        signals = email_analyzer.analyze([_workday_email("1")], days=1)
        assert signals.risk_label in ("Healthy", "Monitor")
        assert signals.avg_daily_sent == 1.0

    def test_weekend_only_activity(self, email_analyzer):
        records = [
            _workday_email(
                str(i),
                timestamp=datetime(2026, 8, 22, 14, 0),  # Saturday
                is_weekend=True,
                is_after_hours=False,
            )
            for i in range(10)
        ]
        signals = email_analyzer.analyze(records, days=7)
        assert signals.weekend_ratio > 0.5


# ═══════════════════════════════════════════════════════════════
# 2. SLACK METADATA
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def slack_analyzer():
    return SlackMetadataAnalyzer()


class TestSlackMetadata:
    def test_empty_input(self, slack_analyzer):
        signals = slack_analyzer.analyze([], [], days=14)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.total_active_channels == 0

    def test_healthy_pattern(self, slack_analyzer):
        base = datetime(2026, 8, 25, 10, 0)
        activity = [
            _slack_activity(base + timedelta(hours=i), channel_id=f"ch-{i % 3}")
            for i in range(10)
        ]
        signals = slack_analyzer.analyze(activity, [], days=14)
        assert signals.burnout_risk_score < 25
        assert signals.risk_label == "Healthy"

    def test_burnout_high_volume_after_hours(self, slack_analyzer):
        base = datetime(2026, 8, 25, 22, 0)  # 10 PM
        activity = [
            _slack_activity(
                base + timedelta(hours=i),
                messages_sent=30,
                is_after_hours=True,
                is_weekend=(i % 4 == 0),
                channel_id=f"ch-{i}",
                app_switches=5,
            )
            for i in range(20)
        ]
        presence = [
            SlackPresenceRecord(
                user_id="u1",
                timestamp=base + timedelta(hours=i),
                status="active",
                is_after_hours=True,
                is_weekend=False,
            )
            for i in range(10)
        ]
        signals = slack_analyzer.analyze(activity, presence, days=7)
        assert signals.burnout_risk_score >= 45
        assert signals.risk_label in ("Elevated", "Critical")

    def test_isolation_risk(self, slack_analyzer):
        base = datetime(2026, 8, 25, 10, 0)
        activity = [
            _slack_activity(
                base,
                messages_sent=2,
                channel_type=SlackChannelType.DM,
                channel_id="dm-1",
                threads_started=0,
                thread_replies=0,
                reactions_given=0,
                reactions_received=0,
            )
        ]
        signals = slack_analyzer.analyze(activity, [], days=14)
        assert signals.isolation_risk_score > 0
        assert signals.dm_ratio == 1.0

    def test_single_activity_record(self, slack_analyzer):
        signals = slack_analyzer.analyze(
            [_slack_activity(datetime(2026, 8, 25, 10, 0))], [], days=1
        )
        assert signals.risk_label in ("Healthy", "Monitor")
        assert signals.total_active_channels == 1


# ═══════════════════════════════════════════════════════════════
# 3. TEAMS METADATA
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def teams_analyzer():
    return TeamsMetadataAnalyzer()


class TestTeamsMetadata:
    def test_empty_input(self, teams_analyzer):
        signals = teams_analyzer.analyze([], [], days=14)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.avg_daily_chats_sent == 0

    def test_healthy_pattern(self, teams_analyzer):
        base = datetime(2026, 8, 25, 10, 0)
        activity = [
            _teams_activity(base + timedelta(hours=i), TeamsActivityType.CHAT, count=3)
            for i in range(5)
        ]
        signals = teams_analyzer.analyze(activity, [], days=14)
        assert signals.burnout_risk_score < 25
        assert signals.risk_label == "Healthy"

    def test_burnout_meeting_overload(self, teams_analyzer):
        base = datetime(2026, 8, 25, 8, 0)
        activity = []
        for i in range(14):
            day = base + timedelta(days=i)
            # 8 meetings/day, 60 min each
            for h in range(8):
                activity.append(_teams_activity(
                    day + timedelta(hours=h),
                    TeamsActivityType.MEETING,
                    count=1,
                    duration_minutes=60,
                    is_after_hours=(h >= 10),
                    is_weekend=(day.weekday() >= 5),
                ))
        signals = teams_analyzer.analyze(activity, [], days=14)
        assert signals.burnout_risk_score >= 45
        assert signals.risk_label in ("Elevated", "Critical")
        assert signals.meeting_hours_per_week > 15

    def test_dnd_protective_factor(self, teams_analyzer):
        base = datetime(2026, 8, 25, 10, 0)
        activity = [
            _teams_activity(base, TeamsActivityType.CHAT, count=20)
        ]
        dnd_presence = [
            TeamsPresenceRecord(
                user_id="u1",
                timestamp=base + timedelta(hours=i),
                availability="DoNotDisturb",
                activity="Focusing",
            )
            for i in range(8)
        ]
        no_dnd_presence = [
            TeamsPresenceRecord(
                user_id="u1",
                timestamp=base + timedelta(hours=i),
                availability="Available",
                activity="InAMeeting",
            )
            for i in range(8)
        ]
        signals_dnd = teams_analyzer.analyze(activity, dnd_presence, days=14)
        signals_no_dnd = teams_analyzer.analyze(activity, no_dnd_presence, days=14)
        assert signals_dnd.dnd_usage_ratio > signals_no_dnd.dnd_usage_ratio


# ═══════════════════════════════════════════════════════════════
# 4. COMPUTER USAGE
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def computer_analyzer():
    return ComputerUsageAnalyzer()


class TestComputerUsage:
    def test_empty_input(self, computer_analyzer):
        signals = computer_analyzer.analyze([], days=14)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.avg_daily_active_hours == 0

    def test_healthy_pattern(self, computer_analyzer):
        base = datetime(2026, 8, 25, 9, 0)
        buckets = [
            _usage_bucket(base + timedelta(minutes=5 * i))
            for i in range(96)  # 8 hours of 5-min buckets
        ]
        signals = computer_analyzer.analyze(buckets, days=14)
        assert signals.burnout_risk_score < 25
        assert signals.risk_label == "Healthy"

    def test_burnout_no_breaks_long_sessions(self, computer_analyzer):
        base = datetime(2026, 8, 25, 6, 0)
        buckets = []
        for day in range(7):
            day_start = base + timedelta(days=day)
            # 14h continuous with high intensity, no idle gaps
            for i in range(168):  # 14h * 12 buckets/h
                ts = day_start + timedelta(minutes=5 * i)
                buckets.append(_usage_bucket(
                    ts,
                    keyboard_events_per_min=60.0,
                    mouse_events_per_min=40.0,
                    app_switches=8,
                    activity_level=ActivityLevel.HIGH,
                    is_after_hours=(ts.hour < 9 or ts.hour >= 18),
                    is_weekend=(ts.weekday() >= 5),
                ))
        signals = computer_analyzer.analyze(buckets, days=7)
        assert signals.burnout_risk_score >= 45
        assert signals.risk_label in ("Elevated", "Critical")
        assert signals.sessions_over_3h > 0

    def test_all_idle_buckets(self, computer_analyzer):
        base = datetime(2026, 8, 25, 10, 0)
        buckets = [
            _usage_bucket(
                base + timedelta(minutes=5 * i),
                keyboard_events_per_min=0,
                mouse_events_per_min=0,
                app_switches=0,
                is_idle=True,
                activity_level=ActivityLevel.IDLE,
            )
            for i in range(20)
        ]
        signals = computer_analyzer.analyze(buckets, days=1)
        assert signals.avg_daily_active_hours == 0
        assert signals.burnout_risk_score < 25

    def test_single_bucket(self, computer_analyzer):
        signals = computer_analyzer.analyze(
            [_usage_bucket(datetime(2026, 8, 25, 10, 0))], days=1
        )
        assert signals.risk_label in ("Healthy", "Monitor")
        assert signals.total_active_days == 1


# ═══════════════════════════════════════════════════════════════
# 5. BADGE ACCESS
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def badge_analyzer():
    return BadgeAccessAnalyzer()


class TestBadgeAccess:
    def test_empty_input(self, badge_analyzer):
        signals = badge_analyzer.analyze([], days=30)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.total_office_days == 0

    def test_healthy_pattern(self, badge_analyzer):
        swipes = []
        for day_offset in range(10):
            day = datetime(2026, 8, 11, 0, 0) + timedelta(days=day_offset)
            if day.weekday() >= 5:
                continue
            swipes.append(_badge_swipe(day.replace(hour=9, minute=0), SwipeDirection.ENTRY))
            swipes.append(_badge_swipe(day.replace(hour=17, minute=30), SwipeDirection.EXIT))
        signals = badge_analyzer.analyze(swipes, days=14)
        assert signals.burnout_risk_score < 25
        assert signals.risk_label == "Healthy"
        assert signals.avg_office_hours <= 9.0

    def test_burnout_long_days_weekends(self, badge_analyzer):
        swipes = []
        for day_offset in range(14):
            day = datetime(2026, 8, 11, 0, 0) + timedelta(days=day_offset)
            is_wknd = day.weekday() >= 5
            swipes.append(_badge_swipe(
                day.replace(hour=6, minute=0), SwipeDirection.ENTRY,
                is_after_hours=True, is_weekend=is_wknd,
            ))
            swipes.append(_badge_swipe(
                day.replace(hour=22, minute=0), SwipeDirection.EXIT,
                is_after_hours=True, is_weekend=is_wknd,
            ))
        signals = badge_analyzer.analyze(swipes, days=14)
        assert signals.burnout_risk_score >= 45
        assert signals.risk_label in ("Elevated", "Critical")
        assert signals.long_day_count > 0
        assert signals.weekend_days_present > 0

    def test_single_day_entry_exit(self, badge_analyzer):
        swipes = [
            _badge_swipe(datetime(2026, 8, 25, 9, 0), SwipeDirection.ENTRY),
            _badge_swipe(datetime(2026, 8, 25, 17, 0), SwipeDirection.EXIT),
        ]
        signals = badge_analyzer.analyze(swipes, days=1)
        assert signals.total_office_days == 1
        assert signals.avg_office_hours == 8.0

    def test_hours_trend_insufficient_data(self, badge_analyzer):
        swipes = [
            _badge_swipe(datetime(2026, 8, 25, 9, 0), SwipeDirection.ENTRY),
            _badge_swipe(datetime(2026, 8, 25, 17, 0), SwipeDirection.EXIT),
        ]
        signals = badge_analyzer.analyze(swipes, days=30)
        assert signals.hours_trend == "insufficient_data"


# ═══════════════════════════════════════════════════════════════
# 6. PTO PATTERNS
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def pto_analyzer():
    return PTOPatternsAnalyzer()


class TestPTOPatterns:
    def test_empty_input(self, pto_analyzer):
        signals = pto_analyzer.analyze([], None, lookback_days=365)
        assert signals.burnout_risk_score == 0
        assert signals.risk_label == "No Data"
        assert signals.vacation_days_taken == 0

    def test_healthy_pto_usage(self, pto_analyzer):
        today = date.today()
        records = [
            LeaveRecord(
                user_id="u1",
                leave_type=LeaveType.VACATION,
                status=LeaveStatus.TAKEN,
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=25),
                business_days=5,
                booked_on=today - timedelta(days=60),
                cancelled_on=None,
            ),
            LeaveRecord(
                user_id="u1",
                leave_type=LeaveType.VACATION,
                status=LeaveStatus.TAKEN,
                start_date=today - timedelta(days=90),
                end_date=today - timedelta(days=86),
                business_days=4,
                booked_on=today - timedelta(days=120),
                cancelled_on=None,
            ),
        ]
        balance = LeaveBalance(
            user_id="u1",
            as_of=today,
            vacation_total=20,
            vacation_used=9,
            vacation_remaining=11,
            sick_total=10,
            sick_used=1,
            sick_remaining=9,
            utilization_pct=45.0,
        )
        signals = pto_analyzer.analyze(records, balance, lookback_days=365)
        assert signals.burnout_risk_score < 45
        assert signals.risk_label in ("Healthy", "Monitor")
        assert signals.vacation_days_taken == 9

    def test_burnout_no_vacation_high_cancellation(self, pto_analyzer):
        today = date.today()
        records = [
            LeaveRecord(
                user_id="u1",
                leave_type=LeaveType.VACATION,
                status=LeaveStatus.CANCELLED,
                start_date=today - timedelta(days=60),
                end_date=today - timedelta(days=55),
                business_days=5,
                booked_on=today - timedelta(days=90),
                cancelled_on=today - timedelta(days=65),
            ),
            LeaveRecord(
                user_id="u1",
                leave_type=LeaveType.VACATION,
                status=LeaveStatus.CANCELLED,
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=26),
                business_days=4,
                booked_on=today - timedelta(days=45),
                cancelled_on=today - timedelta(days=35),
            ),
            # Frequent Monday sick days (disengagement signal)
            *[
                LeaveRecord(
                    user_id="u1",
                    leave_type=LeaveType.SICK,
                    status=LeaveStatus.TAKEN,
                    start_date=today - timedelta(days=7 * w),
                    end_date=today - timedelta(days=7 * w),
                    business_days=1,
                    booked_on=None,
                    cancelled_on=None,
                )
                for w in range(1, 5)
                if (today - timedelta(days=7 * w)).weekday() == 0
            ],
        ]
        balance = LeaveBalance(
            user_id="u1",
            as_of=today,
            vacation_total=20,
            vacation_used=0,
            vacation_remaining=20,
            sick_total=10,
            sick_used=4,
            sick_remaining=6,
            utilization_pct=0.0,
        )
        signals = pto_analyzer.analyze(records, balance, lookback_days=365)
        assert signals.cancellation_rate > 0
        assert signals.vacation_avoidance_score > 0
        assert signals.burnout_risk_score >= 25

    def test_balance_only_no_records(self, pto_analyzer):
        today = date.today()
        balance = LeaveBalance(
            user_id="u1",
            as_of=today,
            vacation_total=20,
            vacation_used=0,
            vacation_remaining=20,
            sick_total=10,
            sick_used=0,
            sick_remaining=10,
            utilization_pct=0.0,
        )
        signals = pto_analyzer.analyze([], balance, lookback_days=365)
        assert signals.risk_label != "No Data"
        assert signals.vacation_days_remaining == 20

    def test_single_short_vacation(self, pto_analyzer):
        today = date.today()
        records = [
            LeaveRecord(
                user_id="u1",
                leave_type=LeaveType.VACATION,
                status=LeaveStatus.TAKEN,
                start_date=today - timedelta(days=10),
                end_date=today - timedelta(days=10),
                business_days=1,
                booked_on=today - timedelta(days=20),
                cancelled_on=None,
            ),
        ]
        signals = pto_analyzer.analyze(records, None, lookback_days=365)
        assert signals.vacation_days_taken == 1
        # 1-day vacation doesn't count as "real vacation" (>= 3 days)
        assert signals.days_since_last_vacation == 365
