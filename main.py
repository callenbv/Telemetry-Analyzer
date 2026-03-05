import os, sys

# Simple import management to import whole folders easily
ROOT = os.path.dirname(os.path.abspath(__file__))
for folder in ("Tabs", "Configuration", "SQLHelper"):
    sys.path.insert(0, os.path.join(ROOT, folder))

import settings
import theme
import tkinter as tk
import tab_manager
import database

window = None # Global variable to hold the main window instance
tabManager = None # Create an instance of the tab manager

# Initialize the window with title and other static settings
def SetupApplication():
    global window
    window = tk.Tk()
    window.geometry(f"{settings.WindowSize[0]}x{settings.WindowSize[1]}")
    window.title(settings.Title)

    # Setup the theme for the window
    window.configure(bg=theme.BackgroundColor)

    # Build tab UI
    global tabManager
    tabManager = tab_manager.TabManager(window)
    tabManager.Initialize() # Initialize the tabs in the manager

# Main function to run the application
def Main():
    SetupApplication()
    window.mainloop()

# Define main entry point
if __name__ == "__main__":
    Main()