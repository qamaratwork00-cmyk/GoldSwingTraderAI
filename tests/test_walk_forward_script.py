from datetime import datetime, timedelta, timezone

from goldswingtraderai.domain.enums import AccountMode, Timeframe
from goldswingtraderai.domain.market import AccountFacts, Candle, CandleSeries, SymbolSpec
from goldswingtraderai.research.datasets import export_replay_dataset_bundle
from goldswingtraderai.research.packages import import_research_evidence_package
from goldswingtraderai.research.replay import ReplayDataset
from scripts.run_walk_forward import main


END = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
_PERIODS = {
    Timeframe.H4: timedelta(hours=4),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.M5: timedelta(minutes=5),
}


def _series(timeframe: Timeframe, count: int) -> CandleSeries:
    period = _PERIODS[timeframe]
    start = END - period * count
    candles = []
    for index in range(count):
        wave = (index % 12) - 6
        close = 2300.0 + index * 0.35 + wave * 0.18
        open_price = close - (0.22 if index % 3 else -0.12)
        candles.append(
            Candle(
                time_utc=start + period * index,
                open=open_price,
                high=max(open_price, close) + 0.55,
                low=min(open_price, close) - 0.55,
                close=close,
                tick_volume=200 + (index % 17) * 9,
            )
        )
    return CandleSeries(timeframe=timeframe, candles=tuple(candles))


def _dataset() -> ReplayDataset:
    return ReplayDataset(
        account=AccountFacts(
            login=123456,
            server="Demo-Server",
            currency="USD",
            mode=AccountMode.DEMO,
            balance=100.0,
            equity=100.0,
            margin=0.0,
            margin_free=100.0,
            leverage=500,
        ),
        symbol_spec=SymbolSpec(
            symbol="XAUUSDm",
            digits=3,
            point=0.001,
            tick_size=0.001,
            tick_value=0.01,
            contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            stops_level_points=0,
            freeze_level_points=0,
        ),
        series=(
            _series(Timeframe.H4, 70),
            _series(Timeframe.H1, 90),
            _series(Timeframe.M15, 120),
            _series(Timeframe.M5, 150),
        ),
        spread_price=0.20,
    )


def test_walk_forward_cli_exports_verified_immutable_evidence(tmp_path) -> None:
    bundle = export_replay_dataset_bundle(
        _dataset(),
        tmp_path / "dataset",
        source_label="synthetic-fixture",
        source_version="2026-06-v1",
    )

    exit_code = main(
        [
            str(bundle.path),
            str(tmp_path / "evidence"),
            "--development-events",
            "8",
            "--validation-events",
            "4",
            "--max-windows",
            "1",
            "--horizon-m5-bars",
            "8",
            "--minimum-bars",
            "H4=50",
            "--minimum-bars",
            "H1=55",
            "--minimum-bars",
            "M15=60",
            "--minimum-bars",
            "M5=70",
            "--start-utc",
            (END - timedelta(hours=2)).isoformat(),
            "--end-utc",
            END.isoformat(),
            "--without-stress",
            "--code-revision",
            "test-revision",
            "--policy-version",
            "policy-v1",
            "--generated-at-utc",
            "2026-09-18T17:00:00Z",
        ]
    )

    assert exit_code == 0
    imported = import_research_evidence_package(
        tmp_path / "evidence",
        dataset_bundle=bundle.path,
    )
    report = imported.evidence_payload["results"]["walk_forward_report"]
    assert report["mode"] == "FIXED_POLICY_WALK_FORWARD"
    assert len(report["evaluations"]) == 1
    assert imported.evidence_payload["limitations"]
