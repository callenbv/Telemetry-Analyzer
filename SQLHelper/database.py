import json
import os
import sqlite3

DB_PATH = "TelemetryData/playtest_data.db"

def AddToDataBase(
    CSVData,
    file_path=None,
    db_path=DB_PATH,
    event_key_candidates=("event_type", "event", "Event", "EventType", "EventName", "type"),
    time_key_candidates=("t_ms", "time_ms", "timestamp_ms", "ms", "time", "timestamp", "t"),
):
    """
    Imports a CSV (as list-of-lists) into SQLite.

    Always writes:
      - runs (one row per import)
      - telemetry_rows (raw rows as JSON dict keyed by headers)

    Additionally writes (best-effort):
      - events (if an event-type column is detected per row)

    Notes:
      - Keeps schema flexible by storing payload_json.
      - Normalizes events to: (run_id, t_ms, event_name, payload_json)
      - Leaves file_path nullable (you can pass it or ignore it).
    """
    if not CSVData:
        print("No CSV data loaded.")
        return None

    headers = CSVData[0]
    rows = CSVData[1:]

    # Ensure output folder exists
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # --- Core tables ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            file_path    TEXT,
            headers_json TEXT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_rows (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id    INTEGER NOT NULL,
            row_index INTEGER NOT NULL,
            row_json  TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        );
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_rows_run ON telemetry_rows(run_id);")

        # --- Optional normalized events table ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id       INTEGER NOT NULL,
            row_index    INTEGER NOT NULL,
            t_ms         INTEGER,
            event_name   TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES runs(run_id)
        );
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_run_time ON events(run_id, t_ms);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON events(event_name);")

        # Insert run
        cur.execute(
            "INSERT INTO runs (file_path, headers_json) VALUES (?, ?);",
            (file_path, json.dumps(headers))
        )
        run_id = cur.lastrowid

        # Helper: find a usable key that exists in the row dict (case-sensitive)
        def find_key(row_dict, candidates):
            for k in candidates:
                if k in row_dict and row_dict[k] not in (None, ""):
                    return k
            return None

        # Best-effort parsing of time into milliseconds
        def parse_time_ms(v):
            if v is None:
                return None
            s = str(v).strip()
            if not s:
                return None
            # If it's a plain integer string: assume it's already ms
            try:
                if s.isdigit() or (s[0] == "-" and s[1:].isdigit()):
                    return int(s)
                # Otherwise try float:
                f = float(s)
                # Heuristic: if it's small, treat as seconds -> ms; if huge, might already be ms
                # You can tune this later.
                if abs(f) < 10_000:  # likely seconds
                    return int(round(f * 1000.0))
                return int(round(f))
            except ValueError:
                return None

        # Insert raw rows and derived events in batches
        raw_batch = []
        event_batch = []

        for i, row in enumerate(rows):
            # Pad/trim to header length
            row = (row + [""] * len(headers))[:len(headers)]
            row_dict = dict(zip(headers, row))
            row_json = json.dumps(row_dict)

            raw_batch.append((run_id, i, row_json))

            # Try to detect an event row
            event_key = find_key(row_dict, event_key_candidates)
            if event_key:
                event_name = str(row_dict[event_key]).strip()
                if event_name:
                    time_key = find_key(row_dict, time_key_candidates)
                    t_ms = parse_time_ms(row_dict[time_key]) if time_key else None

                    # Store the whole row as payload (or you can remove event/time keys if you want)
                    event_batch.append((run_id, i, t_ms, event_name, row_json))

        cur.executemany(
            "INSERT INTO telemetry_rows (run_id, row_index, row_json) VALUES (?, ?, ?);",
            raw_batch
        )

        if event_batch:
            cur.executemany(
                "INSERT INTO events (run_id, row_index, t_ms, event_name, payload_json) VALUES (?, ?, ?, ?, ?);",
                event_batch
            )

        conn.commit()
        print(f"Saved {len(rows)} rows to DB as run_id={run_id} (events: {len(event_batch)})")
        return run_id

    finally:
        conn.close()