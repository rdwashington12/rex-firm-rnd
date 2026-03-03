from __future__ import annotations

from datetime import datetime, timezone

from app.services.db import ControlAuditRecord, Database, FillRecord, OrderRecord, PositionRecord


class TradingRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_by_client_order_id(self, client_order_id: str) -> OrderRecord | None:
        with self.db.session() as session:
            return session.query(OrderRecord).filter(OrderRecord.client_order_id == client_order_id).first()

    def create_order(
        self,
        client_order_id: str,
        symbol: str,
        engine: str,
        strategy: str,
        payload: dict[str, object],
        qty: float = 1.0,
    ) -> OrderRecord:
        with self.db.session() as session:
            order = OrderRecord(
                client_order_id=client_order_id,
                symbol=symbol,
                engine=engine,
                strategy=strategy,
                payload=payload,
                qty=qty,
            )
            session.add(order)
            session.flush()
            session.refresh(order)
            return order

    def update_order_status(self, client_order_id: str, status: str, external_order_id: str | None = None) -> None:
        with self.db.session() as session:
            order = session.query(OrderRecord).filter(OrderRecord.client_order_id == client_order_id).first()
            if order:
                order.status = status
                order.external_order_id = external_order_id or order.external_order_id

    def upsert_position(self, symbol: str, qty: float, avg_entry_price: float, market_value: float, side: str) -> None:
        with self.db.session() as session:
            existing = session.query(PositionRecord).filter(PositionRecord.symbol == symbol).first()
            if existing:
                existing.qty = qty
                existing.avg_entry_price = avg_entry_price
                existing.market_value = market_value
                existing.side = side
                existing.updated_at = datetime.now(timezone.utc)
            else:
                session.add(
                    PositionRecord(
                        symbol=symbol,
                        qty=qty,
                        avg_entry_price=avg_entry_price,
                        market_value=market_value,
                        side=side,
                        updated_at=datetime.now(timezone.utc),
                    )
                )

    def add_fill(self, external_order_id: str, symbol: str, fill_qty: float, fill_price: float) -> None:
        with self.db.session() as session:
            session.add(
                FillRecord(
                    external_order_id=external_order_id,
                    symbol=symbol,
                    fill_qty=fill_qty,
                    fill_price=fill_price,
                )
            )

    def add_control_audit(self, actor: str, action: str, detail: dict[str, object]) -> None:
        with self.db.session() as session:
            session.add(ControlAuditRecord(actor=actor, action=action, detail=detail))

    def recent_audit(self, limit: int = 50) -> list[ControlAuditRecord]:
        with self.db.session() as session:
            return (
                session.query(ControlAuditRecord)
                .order_by(ControlAuditRecord.created_at.desc())
                .limit(limit)
                .all()
            )
