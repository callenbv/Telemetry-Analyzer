import csv
import database
from tkinter import filedialog

# Telemetry analyzer module for processing and analyzing telemetry data from Earthward
class TelemetryAnalyzer:

    def __init__(self):
        self.FilePath = ""
        self.CSVData = []

    def LoadCSV(self, filePath):
        self.FilePath = filePath
        with open(filePath, mode="r", newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            self.CSVData = list(reader)

    def VerifyAndStoreCSV(self):
        if not self.CSVData:
            print("No CSV data loaded.")
            return

        database.AddToDataBase(self.CSVData)

    def UploadCSVFile(self):
        filePath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filePath:
            self.LoadCSV(filePath)