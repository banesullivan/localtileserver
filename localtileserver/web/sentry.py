"""
Optional Sentry SDK integration for error tracking.
"""

import os

sentry_dsn = os.environ.get("SENTRY_DSN", "")

if sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=sentry_dsn,
        # Errors only — no performance transactions. Raise traces_sample_rate
        # (0.0 - 1.0) to sample transactions if you want performance data back.
        traces_sample_rate=0.0,
    )
