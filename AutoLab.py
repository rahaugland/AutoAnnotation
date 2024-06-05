from datetime import datetime
import json
import shutil
from tkinter import Tk, Label, Button
from PIL import Image, ImageTk
import glob
import os
from video_processor import get_position_at_seconds, read_json, seperate_latitude_longitude_timestamps, transform_from_nmea_coordinates_to_degrees
from boundigbox import BoundingBoxApp
from InputFrom import submitDataForm

class AutoAnnotationApp:
    def __init__(self, root, json_path, data_path, folder_save_path, width, height,start_index, naming_prefix,index_length, file_extension="*.jpg"):
        self.root = root
        self.json_path = json_path, 
        self.data_path =data_path
        self.folder_save_path = folder_save_path
        self.nameing_prefix = naming_prefix
        self.width = width
        self.start_index = start_index
        self.height = height
        self.file_extension = file_extension
        self.current_index = 0
        self.current_file = ""
        self.all_images = self.get_images_from_folder()
        self.index_length = index_length
        self.root.title("AUTOLAB")
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.bind("<Configure>", self.on_window_resize)

        self.image_inspector_window = None
        

        self.label_img_name = Label(root, text="")
        self.label_img_name.grid(row=1, column=0, columnspan=2, pady=10)

        self.prev_button = Button(root, text="Previous", command=self.prev_image)
        self.prev_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.next_button = Button(root, text="Next", command=self.next_image)
        self.next_button.grid(row=2, column=1, padx=10, pady=10)

        self.submit_button = Button(root, text="Add images to dataset", command=self.submit)
        self.submit_button.grid(row=3, column=0,columnspan=2, padx=10, pady=10)

        self.update_image_label()

    def submit(self):
        submitForm = submitDataForm(self)

    def process_file(self, filename, latdir, longdir,lat_at_sec_in_deg, long_at_sec_in_deg):
        detections = []
        class_mapping = {
        0: 'D00',
        1: 'D10',
        2: 'D20',
        3: 'D40'
    }
        try:
            with open(filename, 'r') as file:
                for line in file:
                    # Split the line into fields
                    fields = line.split()
                    detection = {
                        "crackType": class_mapping[int(fields[0])],
                        "latitude": lat_at_sec_in_deg,
                        "longitude": long_at_sec_in_deg,
                        "lat_dir": latdir,
                        "long_dir": longdir
                        }
                    detections.append(detection)
                    
                        
        except FileNotFoundError:
            print(f"The file {filename} was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return detections
    
    def process_new_data(self, save_path_img, save_path_labels, name_prefix, start_index):
        current_img_folder = self.data_path
        current_label_path = self.folder_save_path
        print(current_img_folder)
        print(current_label_path)
        os.makedirs(save_path_img, exist_ok=True)
        os.makedirs(save_path_labels, exist_ok=True)
        current_index = int(start_index)
        index_len = len(start_index)
        starttime, stoptime, coordinates, latdir,longdir = read_json(self.json_path[0])  
        print(starttime, stoptime, latdir,longdir)                                                                             
        latitudes, longitudes, timestamps = seperate_latitude_longitude_timestamps(coordinates)
        datetime1 = datetime.fromisoformat(starttime)
        datetime2 = datetime.fromisoformat(stoptime)
        
    # Calculate the time difference
        time_difference = datetime2 - datetime1

        # Convert time difference to seconds
        time_difference_seconds = time_difference.total_seconds()
        time_per_frame = time_difference_seconds / len(current_label_path)
        detections_list = []
       
        output_name = "cracks_complete.json"
        index = 0
        for filename in os.listdir(current_label_path):
            if filename.endswith(".txt"):  # Add more extensions if needed
                lat_at_sec, long_at_sec = get_position_at_seconds(latitudes, longitudes, timestamps, index*time_per_frame, starttime)
                lat_at_sec_in_deg, long_at_sec_in_deg = transform_from_nmea_coordinates_to_degrees(lat_at_sec, long_at_sec)         
                full_filename = current_label_path + "/" + filename
                det = self.process_file(filename=full_filename,
                                        latdir=latdir,
                                        longdir=longdir,
                                        lat_at_sec_in_deg=lat_at_sec_in_deg,
                                        long_at_sec_in_deg=long_at_sec_in_deg)
                for d in det:
                          detections_list.append(d)

                new_filename = f"{name_prefix}_{current_index:0{index_len}}" + os.path.splitext(filename)[1]

                src_path_label = os.path.join(current_label_path, filename)
                dest_path_label = os.path.join(save_path_labels, new_filename)
                shutil.copyfile(src_path_label, dest_path_label)

                corresponding_img_filename = os.path.splitext(filename)[0] + ".jpg"  # Assuming image files have jpg extension
                src_img_path = os.path.join(current_img_folder, corresponding_img_filename)
                print(corresponding_img_filename)
                new_filename = f"{name_prefix}_{current_index:0{index_len}}" + ".jpg"
                dest_img_path = os.path.join(save_path_img, new_filename)

                shutil.copyfile(src_img_path, dest_img_path)
                os.remove(src_path_label)
                os.remove(src_img_path)

                current_index += 1
                index += 1
        with open(output_name, "w") as file:
            detections_json = json.dumps({"Detections": detections_list}, indent=4)
            file.write(detections_json)



    def get_images_from_folder(self):
        
        search_pattern = os.path.join(self.data_path, self.file_extension)
        image_files = glob.glob(search_pattern)
        return image_files

    def next_image(self):
        self.current_index = (self.current_index + 1) % len(self.all_images)
        self.update_image_label()

    def prev_image(self):
        self.current_index = (self.current_index - 1) % len(self.all_images)
        self.update_image_label()

    def update_image_label(self):
        image_path = self.all_images[self.current_index]
        self.current_file = os.path.basename(image_path)
        self.label_img_name.config(text=self.current_file)
        image_index = (self.current_file.split("_")[-1].split(".")[0])
        self.update_image(image_path, image_index)

    def update_image(self, image_path, iamge_index):
        image_path = image_path.replace("\\", "/")

        image = Image.open(image_path)
        
        thumbnail = image.copy()
        thumbnail.thumbnail((self.width, self.height))
        if self.image_inspector_window:
            self.image_inspector_window.update_image(thumbnail, iamge_index)
        else:
            self.image_inspector_window = BoundingBoxApp(self.root, thumbnail, self.folder_save_path, self.start_index,self.index_length, self.nameing_prefix)
            self.image_inspector_window.update_image(thumbnail, iamge_index, first_img=True)

    def on_window_resize(self, event):
        pass

if __name__ == "__main__":
    PROJECT = "AutoAnnotation"
    SUB_PROJECT = "auto_labels9"
    VIDEO_PATH = "hull.mp4"
    DATA_FOLDER = "video_frames_cropped"
    LABEL_PATH = f"{PROJECT}/{SUB_PROJECT}/labels"
    INDEX_LENGTH = 4
    root = Tk()
    start_page = AutoAnnotationApp(root, 
                                    data_path=DATA_FOLDER,
                                    folder_save_path=LABEL_PATH,
                                    width= 1800,
                                    height= 1000,
                                    start_index=0,
                                    index_length=INDEX_LENGTH,
                                    naming_prefix= "hull")
    root.mainloop()


