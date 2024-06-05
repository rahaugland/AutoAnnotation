import tkinter as tk
from tkinter import filedialog
from tkinter import ttk


class InputFormVideo(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("Input Form")

        # Labels and entry fields for each input
        self.entries = {}
        fields = ["Video Path","Model Path", "JSON Path" ,"Save Directory for Images", "Project", "Sub Project", "Focus Point", "Auto Crop", "FPS"]
        default_values = ["","","","", "AutoAnnotation", "auto_labels", "[500, 500]","", "", "False", "1"]  # Default values for each field

        for row, (field, default_value) in enumerate(zip(fields, default_values)):
            label = tk.Label(self, text=f"{field}:")
            label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(self)
            entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            entry.insert(tk.END, default_value)  # Insert default value into entry field
            self.entries[field] = entry


        # Button to prompt for video path
        video_path_button = tk.Button(self, text="Select MP4 file", command=self.select_mp4_file)
        video_path_button.grid(row=0, column=2, padx=5, pady=5)
        model_path_button = tk.Button(self, text="Select Model file", command=self.select_model_file)
        model_path_button.grid(row=1, column=2, padx=5, pady=5)
        json_path_button = tk.Button(self, text="Select JSON file", command=self.select_json_file)
        json_path_button.grid(row=2, column=2, padx=5, pady=5)

        # Button to submit the form
        submit_button = tk.Button(self, text="Submit", command=self.submit_form)
        submit_button.grid(row=len(fields), column=0, columnspan=3, pady=10)
    
    def select_json_file(self):
        file_path = filedialog.askopenfilename(
            initialdir="/",  # You can specify the initial directory to open
            title="Select json file",
            filetypes=(("json files", "*.json"), ("All files", "*.*"))  # Filter for MP4 files
        )
        if file_path:
            self.entries["JSON Path"].delete(0, tk.END)  # Clear the entry field
            self.entries["JSON Path"].insert(0, file_path)  # Insert selected file path

    def select_model_file(self):
        file_path = filedialog.askopenfilename(
            initialdir="/",  # You can specify the initial directory to open
            title="Select Model file",
            filetypes=(("pt files", "*.pt"), ("tflite files", "*.tflite"), ("All files", "*.*"))
        )
        if file_path:
            self.entries["Model Path"].delete(0, tk.END)  # Clear the entry field
            self.entries["Model Path"].insert(0, file_path)  # Insert selected file path


    def select_mp4_file(self):
        file_path = filedialog.askopenfilename(
            initialdir="/",  # You can specify the initial directory to open
            title="Select MP4 file",
            filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*"))  # Filter for MP4 files
        )
        if file_path:
            self.entries["Video Path"].delete(0, tk.END)  # Clear the entry field
            self.entries["Video Path"].insert(0, file_path)  # Insert selected file path

    def submit_form(self):
        # Get input values from entry fields
        inputs = {field: entry.get() for field, entry in self.entries.items()}
        inputs["Focus Point"] = tuple(map(int, inputs["Focus Point"].strip("[]").split(',')))
        # Close the dialog and return the input values
        self.destroy()
        self.parent.process_inputs(inputs, "video")


class InputFormImageFolder(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.title("Input Form")

        # Labels and entry fields for each input
        self.entries = {}
        fields = ["Folder Path", "Do inference?","Save Directory for Images","Project", "Sub Project", "Focus Point", "FPS", "Auto Crop"]
        default_values = ["", "Yes","", "AutoAnnotation", "auto_labels", "[500, 500]", "1", "No"]  # Default values for each field

        for row, (field, default_value) in enumerate(zip(fields, default_values)):
            label = tk.Label(self, text=f"{field}:")
            label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
            if field == "Do inference?" or field =="Auto Crop":
                options = ["Yes", "No"]
                default_index = 0 if default_value == "True" else 1
                dropdown = ttk.Combobox(self, values=options, state="readonly")
                dropdown.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
                dropdown.current(default_index)
                dropdown.bind("<<ComboboxSelected>>", self.select_do_inference)
                self.entries[field] = dropdown
            else:
                entry = tk.Entry(self)
                entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
                entry.insert(tk.END, default_value)  # Insert default value into entry field
                self.entries[field] = entry


        # Button to prompt for video path
        folder_path_button = tk.Button(self, text="Select image Folder file", command=self.select_folder)
        folder_path_button.grid(row=0, column=2, padx=5, pady=5)

        # Button to submit the form
        submit_button = tk.Button(self, text="Submit", command=self.submit_form)
        submit_button.grid(row=len(fields), column=0, columnspan=3, pady=10)


    def select_do_inference(self, *args):
        value = self.entries["Do inference?"].get()
        if value == "Yes":
            self.entries["Project"].config(state="normal")
            self.entries["Sub Project"].config(state="normal")
            self.entries["Focus Point"].config(state="normal")
            self.entries["FPS"].config(state="normal")
            self.entries["Auto Crop"].config(state="normal")
        else:
            self.entries["Project"].config(state="disabled")
            self.entries["Sub Project"].config(state="disabled")
            self.entries["Focus Point"].config(state="disabled")
            self.entries["FPS"].config(state="disabled")
            self.entries["Auto Crop"].config(state="disabled")



    def select_folder(self):
        folder_path = filedialog.askdirectory(
            initialdir="/",  # You can specify the initial directory to open
            title="Select Folder"  # Change the title to indicate selecting a folder
        )
        if folder_path:
            self.entries["Folder Path"].delete(0, tk.END)  # Clear the entry field
            self.entries["Folder Path"].insert(0, folder_path)  # Insert selected folder path

    def submit_form(self):
        # Get input values from entry fields
        inputs = {field: entry.get() for field, entry in self.entries.items()}
        do_infernece = self.entries["Do inference?"].get()
        if do_infernece == "Yes":
            inputs["Focus Point"] = tuple(map(int, inputs["Focus Point"].strip("[]").split(',')))
            # Close the dialog and return the input values
            self.destroy()
            self.parent.process_inputs(inputs, "img_folder")
        else:
            pass



class submitDataForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent

        self.title("Form App")

        self.name_prefix_label = tk.Label(self, text="Name Prefix:")
        self.name_prefix_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.name_prefix_entry = tk.Entry(self, width=20)
        self.name_prefix_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_prefix_entry.bind("<KeyRelease>", self.update_name_preview)

        self.start_index_label = tk.Label(self, text="Start Index:")
        self.start_index_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.start_index_entry = tk.Entry(self, width=20)
        self.start_index_entry.grid(row=1, column=1, padx=5, pady=5)
        self.start_index_entry.bind("<KeyRelease>", self.update_name_preview)

        self.save_path_label = tk.Label(self, text="Save images to folder:")
        self.save_path_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

        self.save_path_entry = tk.Entry(self, width=20)
        self.save_path_entry.grid(row=2, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(self, text="Browse", command=self.browse_save_path_label)
        self.browse_button.grid(row=2, column=2, padx=5, pady=5)

        self.save_path_label = tk.Label(self, text="Save labels to folder:")
        self.save_path_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

        self.save_path_image_entry = tk.Entry(self, width=20)
        self.save_path_image_entry.grid(row=3, column=1, padx=5, pady=5)

        self.browse_button_image = tk.Button(self, text="Browse", command=self.browse_save_path_image)
        self.browse_button_image.grid(row=3, column=2, padx=5, pady=5)
        
        self.save_path_image = tk.Label(self, text="Save images to folder:")
        self.save_path_image.grid(row=3, column=0, padx=5, pady=5, sticky="e")

        self.name_preview_label = tk.Label(self, text="Name Preview: ", font=('Helvetica', 10, 'bold'))
        self.name_preview_label.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.submit_button = tk.Button(self, text="Submit", command=self.submit_form)
        self.submit_button.grid(row=5, column=1, padx=5, pady=5)

    def browse_save_path_label(self):
        save_path = filedialog.askdirectory()
        if save_path:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, save_path)
    
    def browse_save_path_image(self):
        save_path = filedialog.askdirectory()
        if save_path:
            self.save_path_image_entry.delete(0, tk.END)
            self.save_path_image_entry.insert(0, save_path)

    def update_name_preview(self, event=None):
        name_prefix = self.name_prefix_entry.get()
        start_index = self.start_index_entry.get()

        if start_index.isdigit():
            self.name_preview_label.config(text=f"Name Preview: {name_prefix}_{start_index}")
        else:
            self.name_preview_label.config(text="Name Preview: Invalid Start Index")

    def submit_form(self):
        name_prefix = self.name_prefix_entry.get()
        start_index = self.start_index_entry.get()
        save_path_label = self.save_path_entry.get()
        save_path_image = self.save_path_image_entry.get()
        self.parent.process_new_data(save_path_image,save_path_label, name_prefix, start_index)
        