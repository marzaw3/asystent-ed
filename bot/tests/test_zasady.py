from datetime import datetime, timedelta

import pytest

from zasady import LimitSettings, Limits, should_handle

ASK = 111
LEVEL_1 = 222
OTHER = 999
CHANNELS = {ASK, LEVEL_1}

NOON = datetime(2026, 10, 27, 12, 0, 0)


# --- should_handle ------------------------------------------------------------

def test_good_channel_is_handled():
    assert should_handle(False, ASK, "Co to jest bezwładność?", CHANNELS)
    assert should_handle(False, LEVEL_1, "Co to jest bezwładność?", CHANNELS)


def test_other_channel_is_skipped():
    assert not should_handle(False, OTHER, "Co to jest bezwładność?", CHANNELS)


def test_bot_author_is_skipped():
    assert not should_handle(True, ASK, "Co to jest bezwładność?", CHANNELS)


@pytest.mark.parametrize("content", ["", "ok", "  a  ", "x" * 501])
def test_too_short_or_too_long_is_skipped(content):
    assert not should_handle(False, ASK, content, CHANNELS)


@pytest.mark.parametrize("content", ["abc", "x" * 500])
def test_length_limits_are_inclusive(content):
    assert should_handle(False, ASK, content, CHANNELS)


# --- Limits -------------------------------------------------------------------

def make_limits(cooldown=30, per_player=20, per_bot=200):
    saved = []
    limits = Limits(LimitSettings(cooldown, per_player, per_bot), {}, lambda state: saved.append(dict(state)))
    return limits, saved


def test_first_question_is_allowed_and_saved():
    limits, saved = make_limits()
    assert limits.check_and_count(1, NOON).allowed
    assert saved, "stan powinien zostać zapisany"
    assert limits.state["gracze"]["1"]["pytania"] == 1
    assert limits.state["bot"] == 1


def test_second_question_before_cooldown_is_refused():
    limits, _ = make_limits(cooldown=30)
    limits.check_and_count(1, NOON)
    decision = limits.check_and_count(1, NOON + timedelta(seconds=10))
    assert not decision.allowed
    assert "20 s" in decision.message


def test_question_after_cooldown_is_allowed():
    limits, _ = make_limits(cooldown=30)
    limits.check_and_count(1, NOON)
    assert limits.check_and_count(1, NOON + timedelta(seconds=30)).allowed


def test_cooldown_is_per_player():
    limits, _ = make_limits(cooldown=30)
    limits.check_and_count(1, NOON)
    assert limits.check_and_count(2, NOON + timedelta(seconds=1)).allowed


def test_over_daily_player_limit_is_refused():
    limits, _ = make_limits(cooldown=0, per_player=3)
    for i in range(3):
        assert limits.check_and_count(1, NOON + timedelta(minutes=i)).allowed
    decision = limits.check_and_count(1, NOON + timedelta(minutes=10))
    assert not decision.allowed
    assert "jutro" in decision.message


def test_over_daily_bot_limit_is_refused():
    limits, _ = make_limits(cooldown=0, per_bot=2)
    assert limits.check_and_count(1, NOON).allowed
    assert limits.check_and_count(2, NOON).allowed
    decision = limits.check_and_count(3, NOON)
    assert not decision.allowed
    assert "jutro" in decision.message


def test_refused_question_is_not_counted():
    limits, _ = make_limits(cooldown=30)
    limits.check_and_count(1, NOON)
    limits.check_and_count(1, NOON + timedelta(seconds=5))
    assert limits.state["gracze"]["1"]["pytania"] == 1
    assert limits.state["bot"] == 1


def test_counters_reset_at_midnight():
    limits, _ = make_limits(cooldown=0, per_player=1, per_bot=1)
    late = datetime(2026, 10, 27, 23, 59, 0)
    assert limits.check_and_count(1, late).allowed
    assert not limits.check_and_count(1, late + timedelta(seconds=30)).allowed
    assert limits.check_and_count(1, datetime(2026, 10, 28, 0, 0, 30)).allowed


def test_state_has_only_ids_and_numbers():
    limits, _ = make_limits()
    limits.check_and_count(123456789, NOON)
    assert set(limits.state) == {"dzien", "bot", "gracze"}
    assert set(limits.state["gracze"]["123456789"]) == {"pytania", "ostatnie"}


def test_broken_state_starts_fresh():
    limits = Limits(LimitSettings(30, 20, 200), {"dzien": NOON.date().isoformat()}, lambda state: None)
    assert limits.check_and_count(1, NOON).allowed


def test_settings_from_dict():
    settings = LimitSettings.from_dict(
        {"przerwa_sekund_na_gracza": 30, "limit_dzienny_na_gracza": 20, "limit_dzienny_bota": 200}
    )
    assert settings == LimitSettings(30, 20, 200)


@pytest.mark.parametrize("bad", [{}, {"przerwa_sekund_na_gracza": "30", "limit_dzienny_na_gracza": 20, "limit_dzienny_bota": 200}])
def test_settings_from_dict_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        LimitSettings.from_dict(bad)
