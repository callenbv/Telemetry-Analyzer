# telemetry_tab.py
import json

import csv_analyzer
import Tabs.tab as tab
import theme
import tkinter as tk
from tkinter import ttk
import database
import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Try to import tkinterdnd2 for drag-and-drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("tkinterdnd2 not found. Drag-and-drop disabled. Install with: pip install tkinterdnd2")


class TelemetryTab(tab.Tab):
    def __init__(self, name):
        super().__init__(name)
        self.content = None

        self.analyzer = csv_analyzer.TelemetryAnalyzer()
        self.status_var = tk.StringVar(value="No file uploaded")
        self.analyzer.status_var = self.status_var

        # UI state
        self.mode = tk.StringVar(value="across")          # "across" or "run"
        self.analysis_type = tk.StringVar(value="Total")  # "Total" or "Over Time"
        self.selected_event = tk.StringVar(value="")
        self.selected_run = tk.StringVar(value="")
        self.bucket_ms = tk.IntVar(value=5000)

        # UI refs
        self.fileLabel = None
        self.eventCombo = None
        self.runCombo = None
        self.resultsFrame = None
        self.canvas = None
        self.figure = None

    def BuildUI(self):
        # Drag and drop area
        dropFrame = tk.Frame(self.content, bg=self.content["bg"])
        dropFrame.pack(fill="x", padx=20, pady=15)

        # Drop zone with visual styling
        drop_text = "Drop CSV Files Here"
        
        self.dropZone = tk.Label(
            dropFrame,
            text=drop_text,
            bg="#2A2A2A",
            fg=theme.ForegroundColor,
            font=("Arial", 11, "bold"),
            relief="solid",
            borderwidth=2,
            padx=40,
            pady=20
        )
        self.dropZone.pack(pady=5)
        
        # Enable drag and drop only if tkinterdnd2 is available
        if HAS_DND:
            self.dropZone.drop_target_register(DND_FILES)
            self.dropZone.dnd_bind('<<Drop>>', self.on_drop)
            
            # Add hover effects
            self.dropZone.bind("<Enter>", lambda e: self.dropZone.config(bg="#3A3A3A"))
            self.dropZone.bind("<Leave>", lambda e: self.dropZone.config(bg="#2A2A2A"))

        # Status label
        self.fileLabel = tk.Label(
            dropFrame,
            textvariable=self.status_var,
            bg=self.content["bg"],
            fg=theme.ForegroundColor
        )
        self.fileLabel.pack(side="top", pady=5)

        # Button row
        buttonFrame = tk.Frame(dropFrame, bg=self.content["bg"])
        buttonFrame.pack(anchor="center", pady=5)

        loadButton = tk.Button(
            buttonFrame,
            text="Upload Data",
            bg=theme.ButtonColor,
            fg=theme.ForegroundColor,
            command=self.analyzer.UploadCSVFile
        )
        loadButton.pack(side="left", padx=5)

        analyzeButton = tk.Button(
            buttonFrame,
            text="Add to Database",
            bg=theme.ButtonColor,
            fg=theme.ForegroundColor,
            command=self.analyzer.VerifyAndStoreCSV
        )
        analyzeButton.pack(side="left", padx=5)

        # Controls row (mode / event / run / bucket / refresh)
        controls = tk.Frame(self.content, bg=self.content["bg"])
        controls.pack(fill="x", padx=10, pady=10)

        tk.Radiobutton(
            controls,
            text="Across runs",
            variable=self.mode,
            value="across",
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            selectcolor=self.content["bg"],
            command=self.ShowDataPlots
        ).pack(side="left", padx=5)

        tk.Radiobutton(
            controls,
            text="Specific run",
            variable=self.mode,
            value="run",
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            selectcolor=self.content["bg"],
            command=self.ShowDataPlots
        ).pack(side="left", padx=5)

        tk.Label(controls, text="Event:", bg=self.content["bg"], fg=theme.ForegroundColor).pack(side="left", padx=(15, 5))
        self.eventCombo = ttk.Combobox(controls, textvariable=self.selected_event, state="readonly", width=25)
        self.eventCombo.pack(side="left")
        self.eventCombo.bind("<<ComboboxSelected>>", lambda e: self.ShowDataPlots())

        tk.Label(controls, text="Run:", bg=self.content["bg"], fg=theme.ForegroundColor).pack(side="left", padx=(15, 5))
        self.runCombo = ttk.Combobox(controls, textvariable=self.selected_run, state="readonly", width=12)
        self.runCombo.pack(side="left")
        self.runCombo.bind("<<ComboboxSelected>>", lambda e: self.ShowDataPlots())

        tk.Label(controls, text="Bucket ms:", bg=self.content["bg"], fg=theme.ForegroundColor).pack(side="left", padx=(15, 5))
        tk.Entry(controls, textvariable=self.bucket_ms, width=8).pack(side="left")

        # Analysis type dropdown (only applicable for "Specific run" mode)
        tk.Label(controls, text="View:", bg=self.content["bg"], fg=theme.ForegroundColor).pack(side="left", padx=(15, 5))
        analysisCombo = ttk.Combobox(
            controls,
            textvariable=self.analysis_type,
            state="readonly",
            width=15,
            values=["Total", "Over Time"]
        )
        analysisCombo.pack(side="left")
        analysisCombo.bind("<<ComboboxSelected>>", lambda e: self.ShowDataPlots())

        refreshBtn = tk.Button(
            controls,
            text="Refresh",
            bg=theme.ButtonColor,
            fg=theme.ForegroundColor,
            command=self.RefreshSelectorsAndPlots
        )
        refreshBtn.pack(side="right")

        # Results area (charts)
        self.resultsFrame = tk.Frame(self.content, bg=self.content["bg"])
        self.resultsFrame.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial load
        self.RefreshSelectorsAndPlots()

    # ----------------------------
    # Drag and Drop Handler
    # ----------------------------
    def on_drop(self, event):
        """Handle dropped files"""
        # Debug: print raw data
        print(f"DEBUG: Raw drop data: {repr(event.data)}")
        
        # Parse the dropped file paths
        files = self.parse_drop_files(event.data)
        
        print(f"DEBUG: Parsed files: {files}")
        
        if not files:
            self.status_var.set("No valid files dropped")
            return
        
        # Filter for CSV files only
        csv_files = [f for f in files if f.lower().endswith('.csv')]
        
        print(f"DEBUG: CSV files: {csv_files}")
        
        if not csv_files:
            self.status_var.set("No CSV files found in drop")
            return
        
        # Process all dropped CSV files
        self.status_var.set(f"Processing {len(csv_files)} file(s)...")
        self.content.update()  # Force UI update
        
        successful, failed = self.analyzer.ProcessMultipleFiles(csv_files)
        
        print(f"DEBUG: Successful: {successful}, Failed: {failed}")
        
        # Refresh the UI after adding files
        if successful > 0:
            self.RefreshSelectorsAndPlots()
    
    def parse_drop_files(self, data):
        """Parse file paths from drag-and-drop data - supports multiple files"""
        import re
        import os
        
        files = []
        
        if '{' in data:
            matches = re.findall(r'\{([^}]+)\}', data)
            files = matches
        elif '\n' in data:
            parts = data.strip().split('\n')
            files = [p.strip() for p in parts if p.strip()]
        else:
            if '.csv ' in data.lower():
                parts = re.split(r' (?=[A-Z]:/|[A-Z]:\\)', data)
                files = [p.strip() for p in parts if p.strip()]
            else:
                files = [data.strip()]
        
        # Clean up paths and verify they exist
        cleaned_files = []
        for file_path in files:
            # Remove any surrounding quotes and whitespace
            file_path = file_path.strip().strip('"').strip("'")
            
            if os.path.isfile(file_path):
                cleaned_files.append(file_path)
        
        return cleaned_files

    # ----------------------------
    # UI helpers
    # ----------------------------
    def _clear_results(self):
        if not self.resultsFrame:
            return
        for w in self.resultsFrame.winfo_children():
            w.destroy()
        self.canvas = None
        self.figure = None

    def _message(self, text: str):
        tk.Label(
            self.resultsFrame,
            text=text,
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            justify="left"
        ).pack(anchor="w", padx=5, pady=5)

    def _embed_figure(self, fig: Figure):
        self.figure = fig
        self.canvas = FigureCanvasTkAgg(fig, master=self.resultsFrame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ----------------------------
    # Data sources for selectors
    # ----------------------------
    def RefreshSelectorsAndPlots(self):
        # runs list
        try:
            runs = database.QueryRuns()
            run_ids = [str(r[0]) for r in runs]  # (run_id, created_at, file_path)
        except Exception as e:
            run_ids = []
            self._clear_results()
            self._message(f"Failed to read runs table:\n{e}")
            return

        if self.runCombo:
            self.runCombo["values"] = run_ids
        if run_ids and not self.selected_run.get():
            self.selected_run.set(run_ids[0])

        # event names list (best-effort)
        event_names = []
        try:
            if hasattr(database, "QueryEventNames"):
                event_names = list(database.QueryEventNames())
            else:
                # fallback: pull distinct event names (requires sqlite3 access inside database.py normally)
                # if you don't have QueryEventNames, add it to database.py for cleanliness.
                event_names = []
        except Exception:
            event_names = []

        if self.eventCombo:
            self.eventCombo["values"] = event_names
        if event_names and not self.selected_event.get():
            self.selected_event.set(event_names[0])

        self.ShowDataPlots()

    # ----------------------------
    # Plotting
    # ----------------------------
    def ShowDataPlots(self):
        if not self.resultsFrame:
            return

        self._clear_results()

        event_name = (self.selected_event.get() or "").strip()
        if not event_name:
            self._message("Select an event to visualize.\n(If your event dropdown is empty, add database.QueryEventNames().)")
            return

        mode = self.mode.get()
        if mode == "across":
            self._plot_across_runs(event_name)
        else:
            run_id = (self.selected_run.get() or "").strip()
            if not run_id:
                self._message("Select a run to visualize.")
                return

            try:
                bucket = int(self.bucket_ms.get())
                bucket = max(1, bucket)
            except Exception:
                bucket = 5000

            analysis_type = self.analysis_type.get()
            self._plot_run_timeline(run_id, event_name, bucket, analysis_type)

    # Plot average value of the selected event across all runs
    def _plot_across_runs(self, event_name: str):
        # Requires a helper to query events across all runs.
        # Add this to database.py:
        #   def QueryEventsAllRuns(event_name=None, time_range=None, db_path=DB_PATH): ...
        if not hasattr(database, "QueryEventsAllRuns"):
            self._message(
                "Missing database.QueryEventsAllRuns().\n\n"
                "Add it to database.py so we can query events across all runs.\n"
                "Then 'Across runs' mode will work."
            )
            return

        try:
            rows = database.QueryEventsAllRuns(event_name=event_name)
        except Exception as e:
            self._message(f"QueryEventsAllRuns failed:\n{e}")
            return

        if not rows:
            self._message("No events found for that event name.")
            return

        # expected columns: run_id, event_id, row_index, t_ms, event_name, payload_json
        df = pd.DataFrame(rows, columns=[
            "event_id",
            "run_id",
            "row_index",
            "t_ms",
            "event_name",
            "value_num",
            "value_text",
            "payload_json"
        ])

        per_run = (
            df.groupby("run_id")["value_num"]
            .sum()
            .reset_index(name="value")   # <-- forces column name to be "value"
            .sort_values("run_id")
        )
        
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.bar(per_run["run_id"].astype(str), per_run["value"])
        ax.set_title(f"{event_name} across all runs")
        ax.set_xlabel("Run ID")
        ax.set_ylabel("Value")
        ax.tick_params(axis="x", rotation=45)

        self._embed_figure(fig)

        # summary text
        mean = float(per_run["value"].mean())
        median = float(per_run["value"].median())
        total = int(per_run["value"].sum())
        self._message(f"Runs: {len(per_run)} | Total: {total} | Mean: {mean:.2f} | Median: {median:.2f}")

    # Plot frequency of the selected event over time for a specific run
    def _plot_run_timeline(self, run_id: str, event_name: str, bucket_ms: int, analysis_type: str = "Total"):
        try:
            events = database.QueryEvents(int(run_id), event_name=event_name)
        except Exception as e:
            self._message(f"QueryEvents failed:\n{e}")
            return

        if not events:
            self._message("No events found for that run/event.")
            return

        # (event_id, row_index, t_ms, event_name, value_num, value_text, payload_json)
        df = pd.DataFrame(events, columns=[
            "event_id",
            "row_index",
            "t_ms",
            "event_name",
            "value_num",
            "value_text",
            "payload_json"
        ])

        df["value_num"] = pd.to_numeric(df["value_num"], errors="coerce").fillna(0)
        df["t_ms"] = pd.to_numeric(df["t_ms"], errors="coerce")  # may become NaN if NULL

        # If no timestamps, fall back to "pseudo time" based on row_index
        use_time = df["t_ms"].notna().any()
        
        if analysis_type == "Over Time":
            # For "Over Time" mode, show cumulative value trend over time without bucketing
            if not use_time:
                self._message("Note: t_ms is missing (NULL). Using row_index as pseudo-time for this chart.")
                df_sorted = df.sort_values("row_index")
                df_sorted["cumulative_value"] = df_sorted["value_num"].cumsum()
                x = df_sorted["row_index"]
                y = df_sorted["cumulative_value"]
                x_label = "Event Index"
            else:
                df_sorted = df.dropna(subset=["t_ms"]).sort_values("t_ms")
                df_sorted["cumulative_value"] = df_sorted["value_num"].cumsum()
                # Convert to seconds for readability
                x = df_sorted["t_ms"] / 1000.0
                y = df_sorted["cumulative_value"]
                x_label = "Time (seconds)"
            
            fig = Figure(figsize=(5, 5))
            ax = fig.add_subplot(111)
            
            # Plot as line with markers
            ax.plot(x, y, marker='o', linestyle='-', linewidth=2, markersize=6, color='#2E86AB')
            ax.grid(True, alpha=0.3)
            
            ax.set_title(f"Run {run_id}: '{event_name}' - Cumulative Value Over Time", fontsize=12, pad=15)
            ax.set_xlabel(x_label, fontsize=10)
            ax.set_ylabel("Cumulative Value", fontsize=10)
            
            # Format tick labels
            ax.tick_params(axis='both', which='major', labelsize=9)
            
            self._embed_figure(fig)
            
            total = float(df["value_num"].sum())
            num_events = len(df_sorted)
            self._message(
                f"Total: {total:g} | Events: {num_events} | "
                f"Min: {float(y.min()):g} | Max: {float(y.max()):g}"
            )
            
        else:
            # "Total" mode: show just the total value as a single point
            total_value = float(df["value_num"].sum())
            num_events = len(df)
            avg_value = total_value / num_events if num_events > 0 else 0
            
            fig = Figure(figsize=(5, 5))
            ax = fig.add_subplot(111)
            
            # Plot single point at x=1
            ax.plot([1], [total_value], marker='o', linestyle='', markersize=12, color='#2E86AB')
            ax.grid(True, alpha=0.3)
            
            # Add value label on the point
            label = f'{total_value:,.0f}'
            ax.annotate(label, 
                       (1, total_value), 
                       textcoords="offset points", 
                       xytext=(0, 10), 
                       ha='center', 
                       fontsize=11,
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#2E86AB', alpha=0.8))
            
            ax.set_title(f"Run {run_id}: '{event_name}' - Total Value", fontsize=12, pad=15)
            ax.set_xlabel(f"Run {run_id}", fontsize=10)
            ax.set_ylabel("Total Value", fontsize=10)
            
            # Set axis limits
            ax.set_xlim(0.5, 1.5)
            padding = max(total_value * 0.1, 1)
            ax.set_ylim(bottom=0, top=total_value + padding)
            
            # Hide x-axis ticks since we only have one point
            ax.set_xticks([1])
            ax.set_xticklabels([f'Run {run_id}'])
            ax.tick_params(axis='both', which='major', labelsize=9)
            
            self._embed_figure(fig)
            
            self._message(f"Total: {total_value:g} | Events: {num_events} | Average per event: {avg_value:.2f}")

    # Build charts using the SQL data that we already have
    def Refresh(self):
        self.RefreshSelectorsAndPlots()