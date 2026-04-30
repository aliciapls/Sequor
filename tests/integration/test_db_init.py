"""Integration test: verify all database tables create and drop cleanly."""

import pytest


@pytest.mark.asyncio
async def test_init_db_creates_all_tables():
    from sequor.db.database import close_engine, drop_all, get_engine, init_db

    engine = get_engine()
    try:
        await init_db()

        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )

        expected = [
            "tenants", "accounts", "backup_contacts", "contacts",
            "channel_consents", "messages", "classifications",
            "rag_retrievals", "documents", "document_chunks",
            "learned_answers", "responses", "escalations",
            "audit_entries", "routing_outcomes",
        ]
        for table in expected:
            assert table in tables, f"Table {table!r} not found in database"

    finally:
        await drop_all()
        await close_engine()


@pytest.mark.asyncio
async def test_drop_all_removes_tables():
    from sequor.db.database import close_engine, drop_all, get_engine, init_db

    engine = get_engine()
    try:
        await init_db()
        await drop_all()

        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )

        for table in [
            "tenants", "accounts", "messages", "escalations",
        ]:
            assert table not in tables, f"Table {table!r} still exists after drop_all"

    finally:
        await close_engine()
