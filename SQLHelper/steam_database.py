import json
import os
import sqlite3
import csv
import pandas as pd
from datetime import datetime

STEAM_DB_PATH = "TelemetryData/steam_data.db"

def InitializeSteamDatabase(db_path=STEAM_DB_PATH):
    """Create the Steam analytics database tables"""
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        
        # Main steam metrics table - time series data
        cur.execute("""
        CREATE TABLE IF NOT EXISTS steam_metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            visitors        INTEGER DEFAULT 0,
            wishlists       INTEGER DEFAULT 0,
            purchases       INTEGER DEFAULT 0,
            revenue         REAL DEFAULT 0.0,
            game_price      REAL DEFAULT 0.0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_steam_date ON steam_metrics(date);")
        
        # Configuration table for predictions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS steam_config (
            id                      INTEGER PRIMARY KEY CHECK (id = 1),
            visitor_to_wishlist     REAL DEFAULT 0.05,
            wishlist_to_purchase    REAL DEFAULT 0.10,
            default_game_price      REAL DEFAULT 19.99,
            updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        # File tracking table - tracks which CSV files have been imported
        cur.execute("""
        CREATE TABLE IF NOT EXISTS imported_files (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path       TEXT NOT NULL UNIQUE,
            file_mtime      REAL NOT NULL,
            imported_at     TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_imported_path ON imported_files(file_path);")
        
        # Insert default config if not exists
        cur.execute("""
        INSERT OR IGNORE INTO steam_config (id, visitor_to_wishlist, wishlist_to_purchase, default_game_price)
        VALUES (1, 0.05, 0.10, 19.99);
        """)
        
        conn.commit()
    finally:
        conn.close()

def AddSteamMetrics(date, visitors=0, wishlists=0, purchases=0, revenue=0.0, game_price=0.0, db_path=STEAM_DB_PATH):
    """Add or update steam metrics for a specific date"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        
        # Check if entry for this date exists
        cur.execute("SELECT id FROM steam_metrics WHERE date = ?", (date,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing
            cur.execute("""
            UPDATE steam_metrics 
            SET visitors = ?, wishlists = ?, purchases = ?, revenue = ?, game_price = ?
            WHERE date = ?
            """, (visitors, wishlists, purchases, revenue, game_price, date))
        else:
            # Insert new
            cur.execute("""
            INSERT INTO steam_metrics (date, visitors, wishlists, purchases, revenue, game_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (date, visitors, wishlists, purchases, revenue, game_price))
        
        conn.commit()
    finally:
        conn.close()

def ImportSteamCSV(csv_data, db_path=STEAM_DB_PATH):
    """Import Steam data from CSV format
    
    Expected CSV format:
    date,visitors,wishlists,purchases,revenue,game_price
    2024-01-01,1000,50,10,199.90,19.99
    """
    if not csv_data or len(csv_data) < 2:
        return 0
    
    InitializeSteamDatabase(db_path)
    
    headers = [h.strip().lower() for h in csv_data[0]]
    rows = csv_data[1:]
    
    # Find column indices
    date_idx = next((i for i, h in enumerate(headers) if h in ['date', 'day', 'timestamp']), 0)
    visitors_idx = next((i for i, h in enumerate(headers) if 'visitor' in h), None)
    wishlists_idx = next((i for i, h in enumerate(headers) if 'wishlist' in h), None)
    purchases_idx = next((i for i, h in enumerate(headers) if 'purchase' in h or 'sale' in h or 'copies' in h), None)
    revenue_idx = next((i for i, h in enumerate(headers) if 'revenue' in h or 'income' in h), None)
    price_idx = next((i for i, h in enumerate(headers) if 'price' in h), None)
    
    count = 0
    for row in rows:
        if not row or len(row) == 0:
            continue
        
        # Pad row if needed
        row = row + [''] * (len(headers) - len(row))
        
        date = row[date_idx].strip() if date_idx < len(row) else ''
        if not date:
            continue
        
        visitors = int(row[visitors_idx]) if visitors_idx is not None and visitors_idx < len(row) and row[visitors_idx].strip() else 0
        wishlists = int(row[wishlists_idx]) if wishlists_idx is not None and wishlists_idx < len(row) and row[wishlists_idx].strip() else 0
        purchases = int(row[purchases_idx]) if purchases_idx is not None and purchases_idx < len(row) and row[purchases_idx].strip() else 0
        revenue = float(row[revenue_idx]) if revenue_idx is not None and revenue_idx < len(row) and row[revenue_idx].strip() else 0.0
        game_price = float(row[price_idx]) if price_idx is not None and price_idx < len(row) and row[price_idx].strip() else 0.0
        
        AddSteamMetrics(date, visitors, wishlists, purchases, revenue, game_price, db_path)
        count += 1
    
    return count

def GetAllSteamMetrics(db_path=STEAM_DB_PATH):
    """Get all steam metrics ordered by date"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT date, visitors, wishlists, purchases, revenue, game_price
        FROM steam_metrics
        ORDER BY date
        """)
        return cur.fetchall()
    finally:
        conn.close()

def GetSteamConfig(db_path=STEAM_DB_PATH):
    """Get conversion rate configuration"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT visitor_to_wishlist, wishlist_to_purchase, default_game_price FROM steam_config WHERE id = 1")
        result = cur.fetchone()
        if result:
            return {
                'visitor_to_wishlist': result[0],
                'wishlist_to_purchase': result[1],
                'default_game_price': result[2]
            }
        return {'visitor_to_wishlist': 0.05, 'wishlist_to_purchase': 0.10, 'default_game_price': 19.99}
    finally:
        conn.close()

def UpdateSteamConfig(visitor_to_wishlist=None, wishlist_to_purchase=None, default_game_price=None, db_path=STEAM_DB_PATH):
    """Update conversion rate configuration"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        
        updates = []
        params = []
        
        if visitor_to_wishlist is not None:
            updates.append("visitor_to_wishlist = ?")
            params.append(visitor_to_wishlist)
        if wishlist_to_purchase is not None:
            updates.append("wishlist_to_purchase = ?")
            params.append(wishlist_to_purchase)
        if default_game_price is not None:
            updates.append("default_game_price = ?")
            params.append(default_game_price)
        
        if updates:
            updates.append("updated_at = datetime('now')")
            query = f"UPDATE steam_config SET {', '.join(updates)} WHERE id = 1"
            cur.execute(query, params)
            conn.commit()
    finally:
        conn.close()

def ClearSteamData(db_path=STEAM_DB_PATH):
    """Delete all Steam metrics (keep config and imported_files tracking)"""
    InitializeSteamDatabase(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM steam_metrics")
        # Don't delete imported_files - this prevents auto-reimport after clearing
        conn.commit()
    finally:
        conn.close()

def GetImportedFileInfo(file_path, db_path=STEAM_DB_PATH):
    """Get modification time of last import for a file"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT file_mtime FROM imported_files WHERE file_path = ?", (file_path,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def MarkFileImported(file_path, file_mtime, db_path=STEAM_DB_PATH):
    """Mark a file as imported with its modification time"""
    InitializeSteamDatabase(db_path)
    
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
        INSERT OR REPLACE INTO imported_files (file_path, file_mtime)
        VALUES (?, ?)
        """, (file_path, file_mtime))
        conn.commit()
    finally:
        conn.close()

def AutoImportSteamCSVs(data_folder="RawData", db_path=STEAM_DB_PATH):
    """Automatically scan and import Steam CSV files from data folder"""
    InitializeSteamDatabase(db_path)
    
    if not os.path.exists(data_folder):
        return 0
    
    imported_count = 0
    
    # Find all CSV files that look like Steam data
    for filename in os.listdir(data_folder):
        if not filename.lower().endswith('.csv'):
            continue
        
        # Check if it's a Steam-related file (contains "steam" in name or we'll check content)
        file_path = os.path.join(data_folder, filename)
        
        # Skip if not a file
        if not os.path.isfile(file_path):
            continue
        
        # Get current modification time
        current_mtime = os.path.getmtime(file_path)
        
        # Check if file needs importing (new or modified)
        last_imported_mtime = GetImportedFileInfo(file_path, db_path)
        
        if last_imported_mtime is None or current_mtime > last_imported_mtime:
            # File is new or has been modified - import it
            try:
                with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
                    reader = csv.reader(file)
                    csv_data = list(reader)
                
                # Check if it looks like Steam data (has date and at least one metric column)
                if len(csv_data) >= 2:
                    headers = [h.strip().lower() for h in csv_data[0]]
                    has_date = any('date' in h or 'day' in h or 'timestamp' in h for h in headers)
                    has_metric = any('visitor' in h or 'wishlist' in h or 'purchase' in h or 'revenue' in h for h in headers)
                    
                    if has_date and has_metric:
                        # Import the file
                        count = ImportSteamCSV(csv_data, db_path)
                        if count > 0:
                            MarkFileImported(file_path, current_mtime, db_path)
                            imported_count += 1
            except Exception as e:
                print(f"Error auto-importing {filename}: {e}")
                continue
    
    return imported_count
