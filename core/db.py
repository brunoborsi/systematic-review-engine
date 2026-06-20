"""Persistenza su PostgreSQL: salva/carica i 'run' della pipeline.

Un 'run' è una sessione di lavoro (protocollo + risultati di ricerca, screening,
estrazione, calcolo, scrittura) salvata come JSON. Così il lavoro sopravvive
alla sessione del browser e la dashboard mostra dati reali.
"""
from __future__ import annotations

import os

import psycopg2
from psycopg2.extras import Json, RealDictCursor


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id      serial PRIMARY KEY,
                name    text UNIQUE NOT NULL,
                created timestamptz DEFAULT now(),
                updated timestamptz DEFAULT now(),
                status  text,
                data    jsonb NOT NULL
            )
            """
        )
        conn.commit()


def save_run(name: str, data: dict, status: str = "") -> int:
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO runs (name, status, data) VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
                SET data = EXCLUDED.data, status = EXCLUDED.status, updated = now()
            RETURNING id
            """,
            (name, status, Json(data)),
        )
        rid = cur.fetchone()[0]
        conn.commit()
        return rid


def list_runs() -> list[dict]:
    init_db()
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, name, created, updated, status FROM runs ORDER BY updated DESC")
        return list(cur.fetchall())


def load_run(run_id: int) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT data FROM runs WHERE id = %s", (run_id,))
        row = cur.fetchone()
        return row[0] if row else None


def delete_run(run_id: int) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM runs WHERE id = %s", (run_id,))
        conn.commit()
