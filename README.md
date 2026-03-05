# ABOUT EWAnalyzer

EWAnalyzer is a tool used to anaylze telemetry and data pertaining to Earthward.
Built in Python 3.10 using Tkinter for window rendering and data analysis.

EWAnalyzer also takes existing data to predict trends, revenue, and other analytics.

## INSTALLATION

To install all required dependencies (including drag-and-drop support):

```bash
pip install -r requirements.txt
```

Or on Windows, simply run: `install_dependencies.bat`

### Required Packages

- `pandas` - Data analysis
- `matplotlib` - Charting and visualization
- `tkinterdnd2` - Drag-and-drop support (optional but recommended)

## USE CASES

- Playtest data telemetry
- Steam wishlist -> profit analysis
- Steam traffic + prediction based on trends
- Playtest signups

### TELEMETRY ANALYSIS

Earthward playtest data is stored as CSV files, which can be dropped in and analyzed. Once analyzed,
run data is stored in an SQL database. This allows us to easily collect and anaylyze playtest metrics to iterate on
existing gameplay mechanics, and find common trends among players.

#### Analysis Modes

Telemetry can be presented in many ways:

- **Across runs**: See event totals across all runs (e.g., average deaths across all runs)
- **Specific run**: Analyze a specific run with two visualization options:
  - **Total**: View total event values per time bucket
  - **Change**: View cumulative value change over time (trend line)

### STEAM ANALYSIS

Steam analysis lets us predict revenue and future trends (traffic, copies sold) based on the number of wishlists and traffic.
We calculate the percentage of wishlist/purchase ratios, and average visitor/wishlist ratio. These numbers help us determine the performance
of our game at all stages.
