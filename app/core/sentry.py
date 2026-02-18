import os
import sentry_sdk

def setup_sentry():
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("ENV", "prod"),
        traces_sample_rate=0.1,
    )
