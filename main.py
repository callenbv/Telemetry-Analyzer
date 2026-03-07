import os, sys

# Set TCL_LIBRARY and TK_LIBRARY environment variables BEFORE any tkinter imports
if getattr(sys, 'frozen', False):
    # Running as bundled exe - Tcl/Tk are in _MEIPASS/_tcl_data and _MEIPASS/_tk_data
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    
    # PyInstaller's tkinter hook puts data in _tcl_data/tcl8.6 and _tk_data/tk8.6
    tcl_dir = os.path.join(base_path, "_tcl_data", "tcl8.6")
    tk_dir = os.path.join(base_path, "_tk_data", "tk8.6")
    
    # Fallback: also check the old location
    if not os.path.exists(tcl_dir):
        tcl_dir = os.path.join(base_path, "tcl", "tcl8.6")
    if not os.path.exists(tk_dir):
        tk_dir = os.path.join(base_path, "tcl", "tk8.6")
else:
    # Running as script - use base Python installation
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        python_dir = sys.base_prefix
    else:
        python_dir = os.path.dirname(sys.executable)
    
    tcl_dir = os.path.join(python_dir, "tcl", "tcl8.6")
    tk_dir = os.path.join(python_dir, "tcl", "tk8.6")

# Use absolute paths and ensure they exist
if os.path.exists(tcl_dir):
    tcl_abs = os.path.abspath(tcl_dir)
    os.environ["TCL_LIBRARY"] = tcl_abs
if os.path.exists(tk_dir):
    tk_abs = os.path.abspath(tk_dir)
    os.environ["TK_LIBRARY"] = tk_abs

ROOT = os.path.dirname(os.path.abspath(__file__))
for folder in ("Tabs", "Configuration", "SQLHelper"):
    sys.path.insert(0, os.path.join(ROOT, folder))

from Configuration import settings, theme
from Tabs import tab_manager
import tkinter as tk
from tkinterdnd2 import TkinterDnD

HAS_DND = True

window = None # Global variable to hold the main window instance
tabManager = None # Create an instance of the tab manager

# Initialize the window with title and other static settings
def SetupApplication():
    global window
    window = TkinterDnD.Tk()
    
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