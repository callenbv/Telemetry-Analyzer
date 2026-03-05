
# Define telemetry tab for displaying telemetry data and analysis results
import csv_analyzer
import Tabs.tab as tab
import theme
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

class TelemetryTab(tab.Tab):
    def __init__(self,name):
        super().__init__(name) # Initialize the tab with the provided name
        self.content = None # Placeholder for the content of the telemetry tab
        self.analyzer = csv_analyzer.TelemetryAnalyzer() # Create an instance of the telemetry analyzer to handle CSV processing
        
    def BuildUI(self):
        # Create a drag-drop area for loading CSV files
        dropArea = tk.Label(text="Drag and drop your telemetry CSV file here", bg=theme.ButtonColor, fg=theme.ForegroundColor, width=40, height=10)
        dropArea.pack(pady=20)
        
        # Create a button to load CSV file
        loadButton = tk.Button(text="Upload Data", bg=theme.ButtonColor, fg=theme.ForegroundColor, command=lambda: self.analyzer.UploadCSVFile())
        loadButton.pack(pady=10)

        # Create an analyze button to process the loaded CSV file
        analyzeButton = tk.Button(text="Add to Database", bg=theme.ButtonColor, fg=theme.ForegroundColor, command=lambda: self.analyzer.VerifyAndStoreCSV())
        analyzeButton.pack(pady=10)
