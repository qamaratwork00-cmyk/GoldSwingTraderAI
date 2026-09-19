"""Live read-only MT5 recovery truth built through the existing MT5Reader boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from goldswingtraderai.app.recovery import BrokerRecoveryPosition, BrokerRecoverySnapshot
from goldswingtraderai.domain.market import OpenPositionFacts, SymbolSpec
from goldswingtraderai.market_data import MT5Reader


@dataclass(frozen=True, slots=True)
class MT5RecoveryTruth:
    """Current broker recovery snapshot plus verified symbol price geometry."""

    snapshot: BrokerRecoverySnapshot
    symbol_spec: SymbolSpec
    open_positions: tuple[OpenPositionFacts, ...] = ()

    @property
    def price_tolerance(self) -> float:
        """One verified broker tick; recovery never guesses a Gold tolerance."""

        return self.symbol_spec.tick_size


def build_mt5_recovery_truth(
    reader: MT5Reader,
    *,
    preferred_symbol: str,
    symbol_aliases: tuple[str, ...],
    captured_at_utc: datetime | None = None,
) -> MT5RecoveryTruth:
    """Read one complete current recovery snapshot from an initialized MT5Reader.

    Failure to obtain position truth raises through the read boundary. It is never
    converted into an empty exposure snapshot.
    """

    captured = captured_at_utc or datetime.now(timezone.utc)
    _require_utc(captured)

    account = reader.account_facts()
    symbol = reader.resolve_symbol(preferred_symbol, symbol_aliases)
    spec = reader.symbol_spec(symbol)
    positions = reader.open_positions(symbol)

    snapshot = BrokerRecoverySnapshot(
        account=account,
        symbol=symbol,
        positions=tuple(
            BrokerRecoveryPosition(
                ticket=position.ticket,
                symbol=position.symbol,
                direction=position.direction,
                volume=position.volume,
                stop_loss=position.stop_loss,
                take_profit=position.take_profit,
            )
            for position in positions
        ),
        captured_at_utc=captured,
        positions_complete=True,
    )
    return MT5RecoveryTruth(
        snapshot=snapshot,
        symbol_spec=spec,
        open_positions=positions,
    )


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("recovery capture time must be timezone-aware UTC")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("recovery capture time must be UTC")
