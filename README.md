# ABOUT EWAnalyzer

EWAnalyzer is a tool used to anaylze telemetry and data pertaining to Earthward.
Built in Python 3.10 using Tkinter for window rendering and data analysis.

EWAnalyzer also takes existing data to predict trends, revenue, and other analytics.

## USE CASES

- Playtest data telemetry
- Steam wishlist -> profit analysis
- Steam traffic + prediction based on trends
- Playtest signups

### TELEMETRY ANALYSIS

Earthward playtest data is stored as CSV files, which can be dropped in and analyzed. Once analyzed,
run data is stored in an SQL database. This allows us to easily collect and anaylyze playtest metrics to iterate on
existing gameplay mechanics, and find common trends among players.

### STEAM ANALYSIS

Steam analysis lets us predict revenue and future trends (traffic, copies sold) based on the number of wishlists and traffic.
We calculate the percentage of wishlist/purchase ratios, and average visitor/wishlist ratio. These numbers help us determine the performance
of our game at all stages.
