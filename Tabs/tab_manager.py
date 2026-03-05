from telemetry_tab import TelemetryTab
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
        self.tabs.append(tab)

    # Method to build the UI for the tabs
    def BuildUI(self):
        for tab in self.tabs:
            # Build the buttons for the tab bar
            button = tk.Button(self.tabBar, text=tab.name, command=lambda t=tab: self.ShowTab(t.name))
            button.pack(side='left', padx=5, pady=5)

            # Build the tab itself
            tab.BuildUI()

    # Show the specified tab by name
    def ShowTab(self, tabName):
        for tab in self.tabs:
            if tab.name == tabName:
                tab.Show()
            else:
                tab.Hide()

    # Add our base tabs to the manager
    def Initialize(self):
        self.AddTab(TelemetryTab("Telemetry"))
        self.BuildUI()