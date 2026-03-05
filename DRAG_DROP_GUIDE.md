# Drag & Drop Feature Guide

## Quick Start

### Step 1: Install Dependencies
Run the installation script to enable drag-and-drop:

**Windows:**
```bash
install_dependencies.bat
```

**Mac/Linux:**
```bash
pip install -r requirements.txt
```

### Step 2: Launch the Application
```bash
python main.py
```

### Step 3: Use Drag & Drop
1. Open the **Telemetry** tab
2. Drag one or more CSV files from your file explorer
3. Drop them onto the gray drop zone that says "⬇ Drag & Drop CSV Files Here ⬇"
4. Files will automatically be uploaded and added to the database
5. The UI will refresh to show your new data

## Features

### Multiple File Upload
- Drop multiple CSV files at once
- All valid CSV files will be processed
- Status updates show progress and results

### Automatic Processing
- Files are automatically loaded AND added to database
- No need to click "Upload Data" then "Add to Database"
- One-step process from drag to database

### Fallback Options
If drag-and-drop doesn't work or tkinterdnd2 isn't installed:
- Use the "Upload Data" button to browse for files
- Then click "Add to Database" to process

## Troubleshooting

### Drag-and-drop not working?
1. Make sure you ran `install_dependencies.bat` or `pip install tkinterdnd2`
2. Restart the application after installing dependencies
3. If still not working, use the Upload Data button instead

### No files processing?
- Check that your files are `.csv` format
- Verify CSV files have proper headers (event_type, value, t_ms)
- Check the console for error messages

## CSV Format

Your CSV files should have these columns (case-insensitive):
- **event_type** (or event, Event, EventType, EventName, type)
- **value** (or Value, amount, Amount, count, Count, num, Num)
- **t_ms** (or time_ms, timestamp_ms, ms, time, timestamp, t)

Example:
```csv
event_type,value,t_ms
DamageDealt,35,1000
EnemyKilled,1,2500
CollectCoin,10,3000
```

See the `RawData/` folder for sample CSV files!
