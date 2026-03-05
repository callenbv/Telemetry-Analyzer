import json
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = "TelemetryData/playtest_data.db"

# Add telemetry data from the CSVData list to the SQLite database, with optional file path for reference
# The function detects event names and timestamps based on common key candidates, and stores the raw row data 
# as well as a standardized event payload for analysis
def AddToDataBase(
    CSVData,
    file_path=None,
    db_path=DB_PATH,
    event_key_candidates=("event_type", "event", "Event", "EventType", "EventName", "type"),
    time_key_candidates=("t_ms", "time_ms", "timestamp_ms", "ms", "time", "timestamp", "t"),
    value_key_candidates=("value", "Value", "amount", "Amount", "count", "Count", "num", "Num"),
):
    if not CSVData:
        print("No CSV data loaded.")
        return None

    headers = CSVData[0]
    rows = CSVData[1:]

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

        # --- Events table (standardized payload_json) ---
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id       INTEGER NOT NULL,
            row_index    INTEGER NOT NULL,
            t_ms         INTEGER,
            event_name   TEXT NOT NULL,
            value_num    REAL,
            value_text   TEXT,
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

        def find_key_ci(row_dict, candidates):
            lower_map = {k.lower(): k for k in row_dict.keys()}
            for c in candidates:
                k = lower_map.get(c.lower())
                if k and row_dict[k] not in (None, ""):
                    return k
            return None

        def parse_time_ms(v):
            if v is None:
                return None
            s = str(v).strip()
            if not s:
                return None
            try:
                if s.isdigit() or (s[0] == "-" and s[1:].isdigit()):
                    return int(s)
                f = float(s)
                if abs(f) < 10_000:   # likely seconds
                    return int(round(f * 1000.0))
                return int(round(f))  # likely ms
            except ValueError:
                return None

        def parse_number(v):
            if v is None:
                return None
            s = str(v).strip()
            if not s:
                return None
            try:
                return float(s)
            except ValueError:
                return None

        raw_batch = []
        event_batch = []

        for i, row in enumerate(rows):
            row = (row + [""] * len(headers))[:len(headers)]
            row_dict = dict(zip(headers, row))
            row_json = json.dumps(row_dict, separators=(",", ":"))
            raw_batch.append((run_id, i, row_json))

            # detect event
            event_key = find_key_ci(row_dict, event_key_candidates)
            if not event_key:
                continue

            event_name = str(row_dict[event_key]).strip()
            if not event_name:
                continue

            time_key = find_key_ci(row_dict, time_key_candidates)
            t_ms = parse_time_ms(row_dict[time_key]) if time_key else None

            # detect a "value" field (optional)
            value_key = find_key_ci(row_dict, value_key_candidates)
            value_text = str(row_dict[value_key]).strip() if value_key else None
            value_num = parse_number(value_text) if value_key else None

            # STANDARDIZED payload
            payload = {
                "value_num": value_num,     # numeric if parseable, else null
                "value_text": value_text,   # raw text if present, else null
                "fields": row_dict          # entire original row (always)
            }
            payload_json = json.dumps(payload, separators=(",", ":"))

            event_batch.append((run_id, i, t_ms, event_name, value_num, value_text, payload_json))

        cur.executemany(
            "INSERT INTO telemetry_rows (run_id, row_index, row_json) VALUES (?, ?, ?);",
            raw_batch
        )

        if event_batch:
            cur.executemany(
                "INSERT INTO events (run_id, row_index, t_ms, event_name, value_num, value_text, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?);",
                event_batch
            )

        conn.commit()
        print(f"Saved {len(rows)} rows to DB as run_id={run_id} (events: {len(event_batch)})")
        return run_id

    finally:
        conn.close()

# Query events for a given run_id with optional filters for event name and time range (in ms)
# Returns a list of tuples: (event_id, row_index, t_ms, event_name, payload_json)
def QueryEvents(run_id, event_name=None, time_range=None, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        query = "SELECT event_id, row_index, t_ms, event_name, value_num, value_text, payload_json FROM events WHERE run_id = ?"
        params = [run_id]

        if event_name:
            query += " AND event_name = ?"
            params.append(event_name)

        if time_range and len(time_range) == 2:
            query += " AND t_ms BETWEEN ? AND ?"
            params.extend(time_range)

        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

# Select an event to see its frequency across a range of samples (e.g, average deaths of across all runs)
# Specific run data lets you analyze a specific run
def QueryRuns(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT run_id, created_at, file_path FROM runs ORDER BY created_at DESC;")
        return cur.fetchall()
    finally:
        conn.close()

# Query all events across either all runs or a subset of runs
def QueryEventsAllRuns(event_name=None, time_range=None, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        query = "SELECT event_id, run_id, row_index, t_ms, event_name, value_num, value_text, payload_json FROM events WHERE 1=1"
        params = []

        if event_name:
            query += " AND event_name = ?"
            params.append(event_name)

        if time_range and len(time_range) == 2:
            query += " AND t_ms BETWEEN ? AND ?"
            params.extend(time_range)

        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

# Build charts using pandas and matplotlib based on queried event data, with options for filtering and aggregation
def AnalyzeEventData(run_id, event_name=None, time_range=None, db_path=DB_PATH):
    events = QueryEvents(run_id, event_name, time_range, db_path)
    if not events:
        print("No events found for the given criteria.")
        return None

    # Convert to DataFrame for analysis
    df = pd.DataFrame(events, columns=["event_id", "row_index", "t_ms", "event_name", "value_num", "value_text", "payload_json"])
    df["payload"] = df["payload_json"].apply(json.loads)

    # We can select an event, and see how it compares across runs (e.g, average deaths of across all runs)
    # Specific run data lets you analyze a specific run
    return df

# For more complex analysis, we can query all events across either all runs or a subset of runs, and then use pandas to group and analyze the data
def EventsToDF(rows, include_run_id=False):
    if not rows:
        return pd.DataFrame()

    columns = ["event_id", "row_index", "t_ms", "event_name", "value_num", "value_text", "payload_json"]
    if include_run_id:
        columns.insert(1, "run_id")

    df = pd.DataFrame(rows, columns=columns)
    df["payload"] = df["payload_json"].apply(json.loads)
    return df

# Aggregate an event across all runs, e.g, average deaths of across all runs, and return a DataFrame with the results
def AggregateEventAcrossRuns(event_name, time_range=None, db_path=DB_PATH):
    events = QueryEventsAllRuns(event_name, time_range, db_path)
    if not events:
        print("No events found for the given criteria.")
        return None

    df = EventsToDF(events, include_run_id=True)

    # Example aggregation: average value_num by run_id
    agg_df = df.groupby("run_id")["payload"].apply(lambda x: pd.Series({
        "avg_value_num": pd.to_numeric(x.apply(lambda p: p.get("value_num")), errors="coerce").mean(),
        "count": len(x)
    })).reset_index()

    return agg_df

# Get a list of all distinct event names in the database for filtering and selection in the UI
def QueryEventNames(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT event_name
            FROM events
            ORDER BY event_name
        """)
        rows = cur.fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()

# Helper function to safely parse the payload JSON and extract a numeric value for analysis, with fallbacks for different formats
def safe_payload(s):
    if s is None:
        return {}
    if isinstance(s, dict):
        return s
    if isinstance(s, (int, float)):
        # if someone stored raw numeric, treat it as value
        return {"value": s}
    if isinstance(s, str):
        s = s.strip()
        if not s:
            return {}
        # if stored as "5" (not JSON object)
        if s.isdigit():
            return {"value": int(s)}
        try:
            obj = json.loads(s)
            # if json.loads returns a number, list, etc.
            if isinstance(obj, dict):
                return obj
            if isinstance(obj, (int, float)):
                return {"value": obj}
            return {}
        except Exception:
            return {}
    return {}

# We have valid data from pandas, now create the data charts
def VisualizeDataAcrossRuns(per_run,event_name,show_top_n=25):
    sorted_df = per_run.sort_values("avg_value_num", ascending=False).head(show_top_n)
    plt.figure(figsize=(10, 6))
    plt.bar(sorted_df["run_id"].astype(str), sorted_df["avg_value_num"], color="skyblue")
    plt.xlabel("Run ID")
    plt.ylabel(f"Average {event_name} Value")
    plt.title(f"Average {event_name} Value Across Runs (Top {show_top_n})")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()