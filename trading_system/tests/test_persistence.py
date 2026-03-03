from app.services.db import Database
from app.services.persistence import TradingRepository


def test_control_audit_roundtrip() -> None:
    db = Database("sqlite+pysqlite:///:memory:")
    db.migrate()
    repo = TradingRepository(db)

    repo.add_control_audit("tester", "control_update", {"kill_switch": True})
    records = repo.recent_audit(limit=5)

    assert len(records) == 1
    assert records[0].actor == "tester"
