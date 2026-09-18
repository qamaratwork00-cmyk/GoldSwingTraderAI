"""GoldSwingTraderAI application bootstrap.

Phase 1 deliberately performs no MT5 broker writes. It proves configuration,
package wiring and secret-safe diagnostics only.
"""

from __future__ import annotations

import logging

from goldswingtraderai import __version__
from goldswingtraderai.config import ConfigError, Settings
from goldswingtraderai.diagnostics.logging import configure_logging

_LOG = logging.getLogger("goldswingtraderai.app")


def main() -> int:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        configure_logging("ERROR")
        _LOG.error(
            "configuration rejected",
            extra={"event": "CONFIG_INVALID", "context": {"error": str(exc)}},
        )
        return 2

    configure_logging(settings.logging_level)
    _LOG.info(
        "GoldSwingTraderAI foundation initialized",
        extra={
            "event": "FOUNDATION_READY",
            "context": {
                "version": __version__,
                **settings.safe_summary(),
                "broker_write_implemented": False,
            },
        },
    )
    _LOG.info(
        "MT5 trading is intentionally not implemented in Phase 1",
        extra={"event": "PHASE_1_NO_BROKER_WRITES"},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
