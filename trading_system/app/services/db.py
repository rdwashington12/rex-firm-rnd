from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import JSON, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class OrderRecord(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_order_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    external_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    engine: Mapped[str] = mapped_column(String(64), index=True)
    strategy: Mapped[str] = mapped_column(String(64))
    side: Mapped[str] = mapped_column(String(16), default="buy")
    status: Mapped[str] = mapped_column(String(32), default="new")
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class FillRecord(Base):
    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_order_id: Mapped[str] = mapped_column(String(128), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    fill_qty: Mapped[float] = mapped_column(Float)
    fill_price: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PositionRecord(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    qty: Mapped[float] = mapped_column(Float)
    avg_entry_price: Mapped[float] = mapped_column(Float)
    market_value: Mapped[float] = mapped_column(Float)
    side: Mapped[str] = mapped_column(String(16), default="long")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ControlAuditRecord(Base):
    __tablename__ = "control_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(128), default="dashboard")
    action: Mapped[str] = mapped_column(String(64), default="control_update")
    detail: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class MigrationRecord(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Database:
    def __init__(self, dsn: str) -> None:
        engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
        if dsn.startswith("sqlite"):
            if dsn.startswith("sqlite:////"):
                db_file = Path(dsn.replace("sqlite:////", "/", 1))
                db_file.parent.mkdir(parents=True, exist_ok=True)
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        self.engine = create_engine(dsn, **engine_kwargs)
        self._session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def migrate(self) -> None:
        Base.metadata.create_all(self.engine)
        with self.session() as session:
            exists = session.get(MigrationRecord, "0001_baseline")
            if not exists:
                session.add(MigrationRecord(version="0001_baseline", description="Initial trading schema"))
