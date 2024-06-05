import os
from tkinter import Tk, Button, filedialog

from AutoLab import AutoAnnotationApp
from video_processor import process_video, process_folder, process_video_geo

from InputFrom import InputFormVideo, InputFormImageFolder


class StartPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Start Page")
        
        self.process_video_button = Button(root, text="Process Video (Only MP4 files)", command=self.process_video)
        self.process_video_button.pack(pady=10)
        
        self.go_to_image_folder_button = Button(root, text="Go to Image Folder", command=self.go_to_image_folder)
        self.go_to_image_folder_button.pack(pady=10)
    
    def process_video(self):
        input_form = InputFormVideo(self)
    
    def get_prefix_from_folder(self, folder_path):
        # Get list of files in the folder
        files = os.listdir(folder_path)

        # Check if there are any files in the folder
        if files:
            # Get the first file in the folder
            first_file = files[0]

            # Split the filename into parts based on underscore '_'
            parts = first_file.split('_')

            # Extract the part before the underscore
            prefix = parts[0]

            return prefix
        else:
            # No files found in the folder
            return None
    def process_inputs(self,inputs, type):
        if type == "video":
            video_path = inputs["Video Path"]
            save_dir = inputs["Save Directory for Images"]
            model_path = inputs["Model Path"]
            json_path = inputs["JSON Path"]
            proj = inputs["Project"]
            sub_proj = inputs["Sub Project"]
            focus_point = inputs["Focus Point"]
            fps = float(inputs["FPS"]) 
            if inputs["Auto Crop"] == "Yes":
                auto_crop = True
            else:
                auto_crop = False
            print(video_path)
            prefix = video_path.split(".")[0].split("/")[-1]
            print(prefix)
            process_video_geo(video_path=video_path,model_path= model_path,json_data= json_path,save_dir_images= save_dir,project= proj, sub_project=sub_proj, focus_point=focus_point, fps=fps, auto_crop=auto_crop)
            if auto_crop:
                self.start_auto_annotation_app(image_folder = f"{save_dir}_cropped",
                                            lable_path= f"{proj}/{sub_proj}/labels",
                                            naming_prefix=prefix,
                                            json_path = json_path)
            else:
                self.start_auto_annotation_app(image_folder = f"{save_dir}",
                                            lable_path= f"{proj}/{sub_proj}/labels",
                                            naming_prefix=prefix,
                                            json_path = json_path)
        elif type == "img_folder":
            folder_path = inputs["Folder Path"]
            save_dir = inputs["Save Directory for Images"]
            proj = inputs["Project"]
            sub_proj = inputs["Sub Project"]
            focus_point = inputs["Focus Point"]
            fps = int(inputs["FPS"]) 
            if inputs["Auto Crop"] == "Yes":
                auto_crop = True
            else:
                auto_crop = False
            
            process_folder(data_folder=folder_path, 
                           output_folder=save_dir,
                           project=proj,
                           sub_project=sub_proj,
                           focus_point=focus_point,
                           auto_crop=auto_crop)
            if auto_crop:
                self.start_auto_annotation_app(image_folder = f"{save_dir}_cropped",
                                            lable_path= f"{proj}/{sub_proj}/labels",
                                            naming_prefix=self.get_prefix_from_folder(folder_path))
            else:
                self.start_auto_annotation_app(image_folder = f"{folder_path}",
                                            lable_path= f"{proj}/{sub_proj}/labels",
                                            naming_prefix=self.get_prefix_from_folder(folder_path))

            

    def go_to_image_folder(self):
        input_folder_form = InputFormImageFolder(self)
        
    
    def start_auto_annotation_app(self, image_folder, lable_path, json_path, naming_prefix):
        root = Tk()
        
        app = AutoAnnotationApp(root, 
                                data_path=image_folder,
                                folder_save_path=lable_path,
                                json_path = json_path,
                                width=1800,
                                height= 1000,
                                start_index=0,
                                index_length=4,
                                naming_prefix=naming_prefix)
        root.mainloop()
        
if __name__ == "__main__":
    root = Tk()
    start_page = StartPage(root)
    root.mainloop()