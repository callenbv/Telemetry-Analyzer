
# Define playtest analysis tab to display results from playtest sessions
# Takes SQL stored data from telemetry tabs and displays it in a user-friendly format with charts and graphs
import csv_analyzer
import Tabs.tab as tab
import theme
import tkinter as tk

class AnalysisTab(tab.Tab):
    def __init__(self,name):
        super().__init__(name) # Initialize the tab with the provided name
        self.content = None
        
    def BuildUI(self):
        pass