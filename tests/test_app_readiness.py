from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from goldswingtraderai.app.main import run_readiness
from goldswingtraderai.config.settings import Settings
from goldswingtraderai.diagnostics.reasons import ReasonCode
from goldswingtraderai.domain.enums import AccountMode, HardDecision, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, Quote, SymbolSpec
from goldswingtraderai.domain.models import DemoGuardResult, Reason


class StubReader:
    def __init__(self, *, mode: AccountMode = AccountMode.DEMO) -> None:
        self.mode = mode
        self.initialized = False
        self.shutdown_called = False

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True
        self.initialized = False

    def account_facts(self) -> AccountFacts:
        return AccountFacts(
            login=123456,
            server="Broker-Demo",
            currency="USD",
            mode=self.mode,
            balance=100.0,
            equity=101.0,
            margin=5.0,
            margin_free=96.0,
            leverage=500,
        )

    def demo_guard(self, account: AccountFacts | None = None) -> DemoGuardResult:
        facts = account or self.account_facts()
        if facts.mode is AccountMode.DEMO:
            return DemoGuardResult(decision=HardDecision.PASS, account_mode=facts.mode)
        return DemoGuardResult(
            decision=HardDecision.BLOCK,
            account_mode=facts.mode,
            reason=Reason(
                code=ReasonCode.DEMO_GUARD_NOT_VERIFIED,
                message="not positively verified DEMO",
            ),
        )

    def resolve_symbol(self, preferred: str, aliases: tuple[str, ...]) -> str:
        return preferred

    def symbol_spec(self, symbol: str) -> SymbolSpec:
        return SymbolSpec(
            symbol=symbol,
            digits=2,
            point=0.01,
            tick_size=0.01,
            tick_value=1.0,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        )

    def quote(self, symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            bid=3650.10,
            ask=3650.30,
            time_utc=datetime.now(timezone.utc),
        )

    def completed_candles(self, symbol: str, timeframe: Timeframe, count: int) -> CandleSeries:
        period_seconds = {
            Timeframe.H4: 14_400,
            Timeframe.H1: 3_600,
            Timeframe.M15: 900,
            Timeframe.M5: 300,
        }[timeframe]
        now = datetime.now(timezone.utc)
        candles = tuple(
            Candle(
                time_utc=now - timedelta(seconds=period_seconds * index),
                open=3650.0,
                high=3652.0,
                low=3648.0,
                close=3651.0,
                tick_volume=100,
                spread_points=20,
            )
            for index in range(count, 0, -1)
        )
        return CandleSeries(timeframe=timeframe, candles=candles)


class StaleThenFreshReader(StubReader):
    """Return one closed-market-like stale quote, then a fresh quote."""

    def __init__(self) -> None:
        super().__init__()
        self.snapshot_count = 0

    def quote(self, symbol: str) -> Quote:
        self.snapshot_count += 1
        quote_time = (
            NOW - timedelta(hours=1)
            if self.snapshot_count == 1
            else NOW + timedelta(seconds=30)
        )
        return Quote(
            symbol=symbol,
            bid=3650.10,
            ask=3650.30,
            time_utc=quote_time,
        )

    def completed_candles(self, symbol: str, timeframe: Timeframe, count: int) -> CandleSeries:
        period_seconds = {
            Timeframe.H4: 14_400,
            Timeframe.H1: 3_600,
            Timeframe.M15: 900,
            Timeframe.M5: 300,
        }[timeframe]
        base = (
            NOW - timedelta(hours=1)
            if self.snapshot_count == 1
            else NOW + timedelta(seconds=30)
        )
        candles = tuple(
            Candle(
                time_utc=base - timedelta(seconds=period_seconds * index),
                open=3650.0,
                high=3652.0,
                low=3648.0,
                close=3651.0,
                tick_volume=100,
                spread_points=20,
            )
            for index in range(count, 0, -1)
        )
        return CandleSeries(timeframe=timeframe, candles=candles)


class FakeClock:
    def __init__(self) -> None:
        self.current = NOW
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += timedelta(seconds=seconds)


def _settings(*, allowed_account_login: int | None = None) -> Settings:
    return Settings(
        environment="test",
        preferred_symbol="XAUUSDm",
        symbol_aliases=("XAUUSDm", "XAUUSD"),
        manual_reset_enabled=False,
        state_dir=Path(".state"),
        log_level="INFO",
        allowed_account_login=allowed_account_login,
        allowed_server=None,
    )


NOW = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)


def test_readiness_passes_for_verified_demo_snapshot() -> None:
    reader = StubReader()

    assert run_readiness(_settings(), reader) == 0
    assert reader.shutdown_called is True


def test_readiness_rejects_configured_account_identity_mismatch() -> None:
    reader = StubReader()

    assert run_readiness(_settings(allowed_account_login=999999), reader) == 3
    assert reader.shutdown_called is True


def test_readiness_does_not_grant_permission_without_positive_demo() -> None:
    reader = StubReader(mode=AccountMode.OTHER)

    assert run_readiness(_settings(), reader) == 4
    assert reader.shutdown_called is True


def test_readiness_monitor_waits_for_fresh_data_without_entering_runtime() -> None:
    reader = StaleThenFreshReader()
    clock = FakeClock()

    assert run_readiness(
        _settings(),
        reader,
        keep_alive=True,
        sleep=clock.sleep,
        utc_now=clock.now,
    ) == 0

    assert reader.snapshot_count == 2
    assert clock.sleeps == [30.0]
    assert reader.shutdown_called is True
