# Define a tab class for organizing different sections of the application
class Tab:
    def __init__(self, name):
        self.name = name
        self.content = None

    # Function to build the UI elements of the tab. To be overridden by subclasses for specific tab content
    def BuildUI(self):
        pass

    # Hide tab
    def Hide(self):
        if self.content:
            self.content.pack_forget()

    # Show tab
    def Show(self):
        if self.content:
            self.content.pack(fill='both', expand=True)
