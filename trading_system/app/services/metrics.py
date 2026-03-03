from prometheus_client import Counter, Gauge

TRADE_DECISIONS = Counter(
    "trade_decisions_total",
    "Count of trade approvals and rejections",
    labelnames=("engine", "approved"),
)

ENGINE_ENABLED = Gauge(
    "engine_enabled",
    "Whether engine is enabled in dashboard controls",
    labelnames=("engine",),
)

KILL_SWITCH = Gauge("kill_switch_enabled", "Kill switch status")
RISK_MODE = Gauge("risk_mode", "Risk mode as numeric value")
