import csv
import database
from tkinter import filedialog
import os

# Telemetry analyzer module for processing and analyzing telemetry data from Earthward
class TelemetryAnalyzer:

    def __init__(self):
        self.FilePath = ""
        self.CSVData = []

    # Load CSV file and store its content in the CSVData attribute
    def LoadCSV(self, filePath):
        self.FilePath = filePath
        with open(filePath, mode="r", newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            self.CSVData = list(reader)
            self.status_var.set(f"Loaded file: {filePath}")

    # Verify the CSV data and store it in the database
    def VerifyAndStoreCSV(self):
        if not self.CSVData:
            print("No CSV data loaded.")
            return

        database.AddToDataBase(self.CSVData, file_path=self.FilePath)

    # Open a file dialog to select a CSV file and load it
    def UploadCSVFile(self):
        filePath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filePath:
            self.LoadCSV(filePath)

    # Load and process a single CSV file directly to database
    def LoadAndAddToDatabase(self, filePath):
        try:
            with open(filePath, mode="r", newline="", encoding="utf-8-sig") as file:
                reader = csv.reader(file)
                csv_data = list(reader)
            
            database.AddToDataBase(csv_data, file_path=filePath)
            return True
        except Exception as e:
            print(f"Error processing {filePath}: {e}")
            return False

    # Process multiple CSV files at once
    def ProcessMultipleFiles(self, file_paths):
        print(f"DEBUG ProcessMultipleFiles: Processing {len(file_paths)} files")
        print(f"DEBUG ProcessMultipleFiles: Files: {file_paths}")
        
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            print(f"DEBUG ProcessMultipleFiles: Processing {file_path}")
            if file_path.lower().endswith('.csv'):
                if self.LoadAndAddToDatabase(file_path):
                    print(f"DEBUG ProcessMultipleFiles: Successfully added {file_path}")
                    successful += 1
                else:
                    print(f"DEBUG ProcessMultipleFiles: Failed to add {file_path}")
                    failed += 1
        
        print(f"DEBUG ProcessMultipleFiles: Results - Successful: {successful}, Failed: {failed}")
        
        if successful > 0:
            self.status_var.set(f"Processed {successful} file(s) successfully" + (f", {failed} failed" if failed > 0 else ""))
        else:
            self.status_var.set(f"Failed to process files")
        
        return successful, failed