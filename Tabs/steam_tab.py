import csv
import os
import Tabs.tab as tab
import theme
import settings
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SQLHelper'))
import steam_database
import pandas as pd
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SteamTab(tab.Tab):
    def __init__(self, name):
        super().__init__(name)
        self.content = None
        
        # UI state
        self.status_var = tk.StringVar(value="Initializing...")
        
        # UI refs
        self.canvas = None
        self.figure = None
        
    def BuildUI(self):
        # Top section - Upload and controls
        topFrame = tk.Frame(self.content, bg=self.content["bg"])
        topFrame.pack(fill="x", padx=20, pady=15)
        
        # Status label
        self.statusLabel = tk.Label(
            topFrame,
            textvariable=self.status_var,
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            font=("Arial", 10)
        )
        self.statusLabel.pack(side="top", pady=5)
        
        # Info label about auto-loading
        steam_file = getattr(settings, 'SteamCSVFilename', 'Not configured')
        infoLabel = tk.Label(
            topFrame,
            text=f"💡 Auto-loading: {steam_file} (configure in settings.py)",
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            font=("Arial", 8)
        )
        infoLabel.pack(side="top", pady=2)
        
        # Button row
        buttonFrame = tk.Frame(topFrame, bg=self.content["bg"])
        buttonFrame.pack(anchor="center", pady=5)
        
        uploadBtn = tk.Button(
            buttonFrame,
            text="Upload Steam Data",
            bg=theme.ButtonColor,
            fg=theme.ForegroundColor,
            command=self.UploadSteamCSV
        )
        uploadBtn.pack(side="left", padx=5)
        
        refreshBtn = tk.Button(
            buttonFrame,
            text="Refresh Dashboard",
            bg=theme.ButtonColor,
            fg=theme.ForegroundColor,
            command=self.RefreshDashboard
        )
        refreshBtn.pack(side="left", padx=5)
        
        clearBtn = tk.Button(
            buttonFrame,
            text="Clear Data",
            bg="#8B0000",
            fg=theme.ForegroundColor,
            command=self.ClearData
        )
        clearBtn.pack(side="left", padx=5)
        
        # Dashboard area
        self.dashboardFrame = tk.Frame(self.content, bg=self.content["bg"])
        self.dashboardFrame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Auto-load CSV files on startup
        self.AutoLoadSteamData()
        
        # Initial load
        self.RefreshDashboard()
    
    def UploadSteamCSV(self):
        """Upload and import Steam data CSV"""
        file_path = filedialog.askopenfilename(
            title="Select Steam Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Read CSV
            with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
                reader = csv.reader(file)
                csv_data = list(reader)
            
            # Import to database
            count = steam_database.ImportSteamCSV(csv_data)
            
            if count > 0:
                # Mark file as imported
                file_mtime = os.path.getmtime(file_path)
                steam_database.MarkFileImported(file_path, file_mtime)
                
                self.status_var.set(f"Imported {count} records from {os.path.basename(file_path)}")
                self.RefreshDashboard()
            else:
                self.status_var.set("No valid records found in CSV")
                
        except Exception as e:
            error_msg = f"Error importing CSV: {e}"
            self.status_var.set(error_msg)
            messagebox.showerror("Import Error", error_msg)
    
    def ClearData(self):
        """Clear all Steam data after confirmation"""
        response = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to delete all Steam data?\n\nThis cannot be undone!",
            icon='warning'
        )
        
        if response:
            try:
                steam_database.ClearSteamData()
                self.status_var.set("Steam data cleared")
                self.RefreshDashboard()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear data: {e}")
    
    def AutoLoadSteamData(self):
        """Automatically load the configured Steam CSV file from RawData folder on startup"""
        try:
            # Check if a filename is configured
            if not hasattr(settings, 'SteamCSVFilename') or not settings.SteamCSVFilename:
                self.status_var.set("No Steam CSV file configured in settings.py")
                return
            
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_folder = os.path.join(project_root, "RawData")
            file_path = os.path.join(data_folder, settings.SteamCSVFilename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.status_var.set(f"Steam CSV file not found: {settings.SteamCSVFilename}")
                return
            
            # Get current modification time
            current_mtime = os.path.getmtime(file_path)
            
            # Check if file needs importing (new or modified)
            last_imported_mtime = steam_database.GetImportedFileInfo(file_path)
            
            if last_imported_mtime is None or current_mtime > last_imported_mtime:
                # File is new or has been modified - import it
                try:
                    with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
                        reader = csv.reader(file)
                        csv_data = list(reader)
                    
                    # Check if it looks like Steam data
                    if len(csv_data) >= 2:
                        headers = [h.strip().lower() for h in csv_data[0]]
                        has_date = any('date' in h or 'day' in h or 'timestamp' in h for h in headers)
                        has_metric = any('visitor' in h or 'wishlist' in h or 'purchase' in h or 'revenue' in h for h in headers)
                        
                        if has_date and has_metric:
                            # Import the file
                            count = steam_database.ImportSteamCSV(csv_data)
                            if count > 0:
                                steam_database.MarkFileImported(file_path, current_mtime)
                                self.status_var.set(f"Auto-loaded {count} records from {settings.SteamCSVFilename}")
                            else:
                                self.status_var.set(f"No valid records in {settings.SteamCSVFilename}")
                        else:
                            self.status_var.set(f"{settings.SteamCSVFilename} doesn't appear to be Steam data")
                    else:
                        self.status_var.set(f"{settings.SteamCSVFilename} is empty or invalid")
                except Exception as e:
                    self.status_var.set(f"Error loading {settings.SteamCSVFilename}: {e}")
            else:
                # File is up to date
                self.status_var.set(f"Data up to date: {settings.SteamCSVFilename}")
                
        except Exception as e:
            self.status_var.set(f"Auto-load error: {e}")
    
    def RefreshDashboard(self):
        """Refresh the entire dashboard with latest data"""
        # First, check for new files
        self.AutoLoadSteamData()
        
        # Clear existing dashboard
        for widget in self.dashboardFrame.winfo_children():
            widget.destroy()
        
        try:
            # Get data from database
            metrics = steam_database.GetAllSteamMetrics()
            
            if not metrics or len(metrics) == 0:
                self._show_message("No Steam data available.\n\nUpload a CSV file to get started!")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(metrics, columns=['date', 'visitors', 'wishlists', 'purchases', 'revenue', 'game_price'])
            
            # Calculate statistics
            stats = self._calculate_statistics(df)
            
            # Create dashboard layout
            self._build_dashboard(df, stats)
            
            self.status_var.set(f"Dashboard updated - {len(df)} data points")
            
        except Exception as e:
            self._show_message(f"Error loading dashboard:\n{e}")
    
    def _calculate_statistics(self, df):
        """Calculate all statistics and predictions"""
        stats = {}
        
        # Current totals
        # Visitors and wishlists are cumulative - get the latest value (most recent date)
        df_sorted = df.sort_values('date')
        stats['total_visitors'] = int(df_sorted['visitors'].iloc[-1])  # Latest cumulative value
        stats['total_wishlists'] = int(df_sorted['wishlists'].iloc[-1])  # Latest cumulative value
        stats['total_purchases'] = int(df['purchases'].sum())
        
        # Average price
        avg_price = df[df['game_price'] > 0]['game_price'].mean()
        stats['avg_price'] = avg_price if not pd.isna(avg_price) else 19.99
        
        # Revenue should be calculated from actual purchases, not from CSV revenue column
        # This ensures revenue = copies sold * price
        stats['total_revenue'] = float(stats['total_purchases'] * stats['avg_price'])
        
        # Conversion rates (actual from data)
        if stats['total_visitors'] > 0:
            stats['visitor_to_wishlist_rate'] = stats['total_wishlists'] / stats['total_visitors']
        else:
            stats['visitor_to_wishlist_rate'] = 0.05
        
        # Get config for reference
        config = steam_database.GetSteamConfig()
        stats['config_visitor_wishlist'] = config['visitor_to_wishlist']
        stats['config_wishlist_purchase'] = config['wishlist_to_purchase']
        
        # Calculate actual conversion rate from data
        if stats['total_wishlists'] > 0:
            stats['wishlist_to_purchase_rate'] = stats['total_purchases'] / stats['total_wishlists']
        else:
            stats['wishlist_to_purchase_rate'] = 0.10
        
        # For predictions: use actual rate if game has launched (purchases > 0),
        # otherwise use industry average from config (game hasn't launched yet)
        if stats['total_purchases'] == 0 or stats['wishlist_to_purchase_rate'] == 0:
            # Game hasn't launched yet - use industry average (default 20%)
            prediction_rate = config['wishlist_to_purchase']
        else:
            # Game has launched - use actual performance rate
            prediction_rate = stats['wishlist_to_purchase_rate']
        
        # Predictions based on current wishlists
        stats['predicted_purchases'] = int(stats['total_wishlists'] * prediction_rate)
        # Gross revenue (before Steam cut and taxes)
        gross_revenue = stats['predicted_purchases'] * stats['avg_price']
        stats['predicted_revenue'] = gross_revenue
        
        # Steam takes 30% cut, developer gets 70%
        STEAM_CUT = 0.30
        revenue_after_steam = gross_revenue * (1 - STEAM_CUT)
        
        # Calculate total taxes on the revenue you actually receive
        # Federal income tax rate (personal income tax for indie dev, ~15-20% bracket)
        FEDERAL_TAX_RATE = 0.15
        # Washington state sales tax rate (6.5% for digital goods)
        WA_TAX_RATE = 0.065
        # Total effective tax rate
        TOTAL_TAX_RATE = FEDERAL_TAX_RATE + WA_TAX_RATE
        # After Steam's cut AND all taxes
        stats['predicted_revenue_after_tax'] = revenue_after_steam * (1 - TOTAL_TAX_RATE)
        
        # Growth trends (last 4 weeks if available)
        if len(df) >= 4:
            recent = df.tail(4)
            stats['visitor_growth'] = ((recent['visitors'].iloc[-1] - recent['visitors'].iloc[0]) / recent['visitors'].iloc[0]) * 100 if recent['visitors'].iloc[0] > 0 else 0
            stats['wishlist_growth'] = ((recent['wishlists'].iloc[-1] - recent['wishlists'].iloc[0]) / recent['wishlists'].iloc[0]) * 100 if recent['wishlists'].iloc[0] > 0 else 0
        else:
            stats['visitor_growth'] = 0
            stats['wishlist_growth'] = 0
        
        return stats
    
    def _build_dashboard(self, df, stats):
        """Build the complete dashboard UI"""
        # Create scrollable frame for dashboard
        canvas = tk.Canvas(self.dashboardFrame, bg=self.content["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dashboardFrame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.content["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Key Metrics Row
        metricsFrame = tk.Frame(scrollable_frame, bg=self.content["bg"])
        metricsFrame.pack(fill="x", padx=10, pady=10)
        
        self._create_metric_card(metricsFrame, "Total Visitors", f"{stats['total_visitors']:,}", "#4A90E2", 0)
        self._create_metric_card(metricsFrame, "Wishlists", f"{stats['total_wishlists']:,}", "#7B68EE", 1)
        self._create_metric_card(metricsFrame, "Copies Sold", f"{stats['total_purchases']:,}", "#50C878", 2)
        self._create_metric_card(metricsFrame, "Revenue", f"${stats['total_revenue']:,.2f}", "#FFD700", 3)
        
        # Conversion Rates Row
        conversionFrame = tk.Frame(scrollable_frame, bg=self.content["bg"])
        conversionFrame.pack(fill="x", padx=10, pady=10)
        
        self._create_metric_card(conversionFrame, "Visitor → Wishlist", f"{stats['visitor_to_wishlist_rate']*100:.2f}%", "#FF6B6B", 0)
        self._create_metric_card(conversionFrame, "Wishlist → Purchase", f"{stats['wishlist_to_purchase_rate']*100:.2f}%", "#4ECDC4", 1)
        self._create_metric_card(conversionFrame, "Predicted Sales", f"{stats['predicted_purchases']:,}", "#95E1D3", 2)
        # Create custom revenue card with after-tax value
        self._create_revenue_card(conversionFrame, stats, "#F38181", 3)
        
        # Charts Row 1: Visitors & Wishlists over time
        charts1Frame = tk.Frame(scrollable_frame, bg=self.content["bg"])
        charts1Frame.pack(fill="x", padx=10, pady=10)
        
        self._create_time_series_chart(charts1Frame, df, "Visitors & Wishlists Over Time", 
                                       ['visitors', 'wishlists'], ['#4A90E2', '#7B68EE'], 0)
        
        # Charts Row 2: Purchases & Revenue
        charts2Frame = tk.Frame(scrollable_frame, bg=self.content["bg"])
        charts2Frame.pack(fill="x", padx=10, pady=10)
        
        self._create_dual_axis_chart(charts2Frame, df, 0)
        
        # Charts Row 3: Conversion funnel
        charts3Frame = tk.Frame(scrollable_frame, bg=self.content["bg"])
        charts3Frame.pack(fill="x", padx=10, pady=10)
        
        self._create_funnel_chart(charts3Frame, stats, 0)
    
    def _create_metric_card(self, parent, title, value, color, column):
        """Create a metric card widget"""
        card = tk.Frame(parent, bg=color, relief="raised", borderwidth=2)
        card.grid(row=0, column=column, padx=10, pady=5, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        titleLabel = tk.Label(card, text=title, bg=color, fg="white", font=("Arial", 10, "bold"))
        titleLabel.pack(pady=(10, 5))
        
        valueLabel = tk.Label(card, text=value, bg=color, fg="white", font=("Arial", 16, "bold"))
        valueLabel.pack(pady=(5, 10))
    
    def _create_revenue_card(self, parent, stats, color, column):
        """Create a revenue card with after-tax value"""
        card = tk.Frame(parent, bg=color, relief="raised", borderwidth=2)
        card.grid(row=0, column=column, padx=10, pady=5, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        titleLabel = tk.Label(card, text="Predicted Revenue", bg=color, fg="white", font=("Arial", 10, "bold"))
        titleLabel.pack(pady=(10, 5))
        
        # Main revenue value
        valueLabel = tk.Label(card, text=f"${stats['predicted_revenue']:,.2f}", bg=color, fg="white", font=("Arial", 16, "bold"))
        valueLabel.pack(pady=(5, 2))
        
        # After-tax value (smaller, below)
        afterTaxLabel = tk.Label(
            card, 
            text=f"After All Taxes: ${stats['predicted_revenue_after_tax']:,.2f}", 
            bg=color, 
            fg="white", 
            font=("Arial", 9)
        )
        afterTaxLabel.pack(pady=(2, 10))
    
    def _create_time_series_chart(self, parent, df, title, columns, colors, row):
        """Create a time series line chart"""
        fig = Figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        
        for col, color in zip(columns, colors):
            ax.plot(range(len(df)), df[col], marker='o', label=col.capitalize(), 
                   color=color, linewidth=2, markersize=6)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("Time Period", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis with dates if available
        if len(df) <= 20:
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['date'], rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xticks(range(0, len(df), max(1, len(df)//10)))
            ax.set_xticklabels([df['date'].iloc[i] for i in range(0, len(df), max(1, len(df)//10))], 
                              rotation=45, ha='right', fontsize=8)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        parent.grid_columnconfigure(0, weight=1)
    
    def _create_dual_axis_chart(self, parent, df, row):
        """Create a dual-axis chart for purchases and revenue"""
        fig = Figure(figsize=(12, 4))
        ax1 = fig.add_subplot(111)
        
        # Purchases on left axis
        color1 = '#50C878'
        ax1.set_xlabel('Time Period', fontsize=10)
        ax1.set_ylabel('Purchases (Copies Sold)', color=color1, fontsize=10)
        ax1.bar(range(len(df)), df['purchases'], color=color1, alpha=0.7, label='Purchases')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.legend(loc='upper left', fontsize=10)
        
        # Revenue on right axis
        ax2 = ax1.twinx()
        color2 = '#FFD700'
        ax2.set_ylabel('Revenue ($)', color=color2, fontsize=10)
        ax2.plot(range(len(df)), df['revenue'], color=color2, marker='D', 
                linewidth=2, markersize=6, label='Revenue')
        ax2.tick_params(axis='y', labelcolor=color2)
        ax2.legend(loc='upper right', fontsize=10)
        
        ax1.set_title("Purchases & Revenue Over Time", fontsize=14, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        if len(df) <= 20:
            ax1.set_xticks(range(len(df)))
            ax1.set_xticklabels(df['date'], rotation=45, ha='right', fontsize=8)
        else:
            ax1.set_xticks(range(0, len(df), max(1, len(df)//10)))
            ax1.set_xticklabels([df['date'].iloc[i] for i in range(0, len(df), max(1, len(df)//10))], 
                               rotation=45, ha='right', fontsize=8)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        parent.grid_columnconfigure(0, weight=1)
    
    def _create_funnel_chart(self, parent, stats, row):
        """Create a conversion funnel visualization"""
        fig = Figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        
        # Funnel data
        stages = ['Visitors', 'Wishlists', 'Purchases']
        values = [stats['total_visitors'], stats['total_wishlists'], stats['total_purchases']]
        colors = ['#4A90E2', '#7B68EE', '#50C878']
        
        # Create horizontal bar chart as funnel
        y_pos = np.arange(len(stages))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.8)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            ax.text(width / 2, bar.get_y() + bar.get_height() / 2, 
                   f'{value:,}', ha='center', va='center', 
                   color='white', fontweight='bold', fontsize=12)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(stages, fontsize=11)
        ax.set_xlabel('Count', fontsize=10)
        ax.set_title('Conversion Funnel', fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add conversion rates as annotations
        if len(values) > 1:
            conv1 = (values[1] / values[0] * 100) if values[0] > 0 else 0
            ax.text(max(values) * 0.7, 0.5, f'↓ {conv1:.1f}%', 
                   fontsize=10, ha='left', style='italic')
        if len(values) > 2:
            conv2 = (values[2] / values[1] * 100) if values[1] > 0 else 0
            ax.text(max(values) * 0.7, 1.5, f'↓ {conv2:.1f}%', 
                   fontsize=10, ha='left', style='italic')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        parent.grid_columnconfigure(0, weight=1)
    
    def _show_message(self, message):
        """Show a centered message in the dashboard area"""
        label = tk.Label(
            self.dashboardFrame,
            text=message,
            bg=self.content["bg"],
            fg=theme.ForegroundColor,
            font=("Arial", 12),
            justify="center"
        )
        label.pack(expand=True)
