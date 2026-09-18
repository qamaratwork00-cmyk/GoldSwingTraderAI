from goldswingtraderai.risk import AccountProfile, resolve_account_profile


def test_any_positive_equity_below_300_is_small_profile() -> None:
    for equity in (0.01, 1.0, 30.0, 99.99, 100.0, 299.99):
        assert resolve_account_profile(equity) is AccountProfile.SMALL


def test_profile_boundaries_above_small_are_unchanged() -> None:
    assert resolve_account_profile(300.0) is AccountProfile.MEDIUM
    assert resolve_account_profile(999.99) is AccountProfile.MEDIUM
    assert resolve_account_profile(1000.0) is AccountProfile.NORMAL


def test_non_positive_equity_has_no_trading_profile() -> None:
    assert resolve_account_profile(0.0) is None
    assert resolve_account_profile(-1.0) is None
