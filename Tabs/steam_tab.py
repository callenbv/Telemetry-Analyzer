
# Define telemetry tab for displaying telemetry data and analysis results
import csv_analyzer
import Tabs.tab as tab
import theme
import tkinter as tk
import steam_data_analyzer

class SteamTab(tab.Tab):
    def __init__(self,name):
        super().__init__(name) # Initialize the tab with the provided name
        self.content = None # Placeholder for the content of the telemetry tab
        self.analyzer = csv_analyzer.TelemetryAnalyzer() # Create an instance of the telemetry analyzer to handle CSV processing
        
    def BuildUI(self):
        buttonFrame = tk.Frame(self.content, bg=self.content["bg"])
        buttonFrame.pack(anchor="center", pady=10)

    # Takes Steam data (wishlists, reviews, traffic) and re-calculates it for analysis
    def Refresh(self):
        pass

