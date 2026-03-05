from telemetry_tab import TelemetryTab
from steam_tab import SteamTab
from playtest_analysis import AnalysisTab
import tkinter as tk

# Define a tab manager for managing multiple tabs in the application
class TabManager:
    def __init__(self,root):
        self.tabs = [] # List to hold the tabs in the application
        self.active = True
        self.root = root

        self.tabBar = tk.Frame(root, bg=root["bg"])
        self.tabBar.pack(side='top', fill='x')
        self.contentRoot = tk.Frame(root, bg=root["bg"])
        self.contentRoot.pack(side='top', fill='both', expand=True)

    # Method to add a new tab to the manager
    def AddTab(self, tab):
        tab.content = tk.Frame(self.contentRoot, bg=self.root["bg"])
        tab.content.pack(fill='both', expand=True)
        tab.Hide()
        self.tabs.append(tab)

    # Method to build the UI for the tabs
    def BuildUI(self):
        for tab in self.tabs:
            # Build the buttons for the tab bar
            button = tk.Button(self.tabBar, text=tab.name, command=lambda t=tab: self.ShowTab(t))
            button.pack(side='left')

            # Build the tab itself
            tab.BuildUI()

    # Show the specified tab by name
    def ShowTab(self, tab):
        for t in self.tabs:
            if t == tab:
                t.Show()
            else:
                t.Hide()

    # Add our base tabs to the manager
    def Initialize(self):
        self.AddTab(TelemetryTab("Telemetry"))
        self.AddTab(SteamTab("Steam Analysis"))
        self.AddTab(AnalysisTab("Playtest Analysis"))
        self.ShowTab(self.tabs[0])
        self.BuildUI()