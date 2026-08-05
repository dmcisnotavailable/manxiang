import pytest

from manxiang.intervention import InterventionPolicy


def test_strict_mode_refuses_low_relevance_detour():
    policy = InterventionPolicy()

    decision = policy.decide(
        mode="strict_mentor",
        detour_title="语音克隆技术史",
        relevance_score=0.1,
    )

    assert decision.level == "refuse"
    assert decision.should_park is True
    assert "不会继续展开" in decision.message


def test_gentle_mode_timeboxes_medium_relevance_detour():
    policy = InterventionPolicy()

    decision = policy.decide(
        mode="gentle_editor",
        detour_title="长期记忆产品机制",
        relevance_score=0.45,
    )

    assert decision.level == "limit"
    assert decision.timebox_minutes == 5
    assert decision.should_park is False


def test_research_buddy_reminds_with_timebox_for_relevant_detour():
    policy = InterventionPolicy()

    decision = policy.decide(
        mode="research_buddy",
        detour_title="产品记忆机制",
        relevance_score=0.6,
    )

    assert decision.level == "remind"
    assert decision.timebox_minutes == 15
    assert decision.should_park is False


def test_unknown_mode_raises_value_error():
    policy = InterventionPolicy()

    with pytest.raises(ValueError, match="Unknown agent mode"):
        policy.decide(
            mode="typo_mode",
            detour_title="拼写错误模式",
            relevance_score=0.6,
        )


def test_threshold_boundaries_use_limit_or_remind():
    policy = InterventionPolicy()

    strict_decision = policy.decide(
        mode="strict_mentor",
        detour_title="严格边界",
        relevance_score=0.3,
    )
    gentle_decision = policy.decide(
        mode="gentle_editor",
        detour_title="温和边界",
        relevance_score=0.2,
    )
    buddy_decision = policy.decide(
        mode="research_buddy",
        detour_title="伙伴边界",
        relevance_score=0.15,
    )

    assert strict_decision.level == "limit"
    assert gentle_decision.level == "limit"
    assert buddy_decision.level == "remind"
    assert buddy_decision.timebox_minutes == 15
