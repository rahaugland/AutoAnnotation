from tkinter import *
from PIL import Image, ImageTk
import tkinter.ttk as ttk
colors = {"D00": "red", "D10":"green", "D20":"orange", "D40": "purple"}
class BoundingBoxApp:
    def __init__(self, root, image, folder_path, start_index,index_length, naming_prefix):
        self.root = root
        self.root.title("Bounding Box Annotation")
        self.nameing_prefix = naming_prefix
        self.index_length = index_length
        self.boundingBoxes = []
        self.rectangles= []
        self.current_index = start_index
        self.folder_path = folder_path
        self.image = image
        self.frame = Frame(self.root)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.start_index=start_index
        self.canvas = Canvas(self.frame, width=self.image.width, height=self.image.height)
        self.photo = ImageTk.PhotoImage(self.image, master=self.root)
        self.canvas.create_image(0, 0, anchor=NW, image=self.photo)
        self.canvas.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.selected_item = StringVar()
        
        items = ["D00", "D10", "D20", "D40", "Delete boxes", "Disable labeling"]
        radbut1 = ttk.Radiobutton(self.frame, text="D00", variable=self.selected_item, value="D00", command=lambda: self.on_radio_button_select("D00"))
        radbut1.grid(row=0, column=0+1, sticky="w")

        radbut2 = ttk.Radiobutton(self.frame, text="D10", variable=self.selected_item, value="D10", command=lambda: self.on_radio_button_select("D10"))
        radbut2.grid(row=0, column=1+1, sticky="w")

        radbut3 = ttk.Radiobutton(self.frame, text="D20", variable=self.selected_item, value="D20", command=lambda: self.on_radio_button_select("D20"))
        radbut3.grid(row=0, column=3, sticky="w")

        radbut4 = ttk.Radiobutton(self.frame, text="D40", variable=self.selected_item, value="D40", command=lambda: self.on_radio_button_select("D40"))
        radbut4.grid(row=0, column=4, sticky="w")

        radbut5 = ttk.Radiobutton(self.frame, text="Delete boxes", variable=self.selected_item, value="Delete boxes", command=lambda: self.on_radio_button_select("Delete boxes"))
        radbut5.grid(row=0, column=5, sticky="w")

        radbut6 = ttk.Radiobutton(self.frame, text="Disable labeling", variable=self.selected_item, value="Disable labeling", command=lambda: self.on_radio_button_select("Disable labeling"))
        radbut6.grid(row=0, column=6, sticky="w")        
        self.text = Text(self.frame, height=self.image.height // 20, width=30)
        self.text.grid(row=1, column=1, columnspan=6, sticky="nsew")
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
    
    def on_radio_button_select(self, update_string):
        self.selected_item.set(update_string)
        print(f"Selected Item: {update_string}")  
         
    

    def is_inside_box(self, x, y):    
         for bbox, rect_id in zip(self.boundingBoxes, self.rectangles):
            bbox_x1, bbox_y1, bbox_x2, bbox_y2, _ = bbox
            if bbox_x1 < x < bbox_x2 and bbox_y1 < y < bbox_y2:
                print(rect_id)
        
                
                self.canvas.delete(rect_id)
                self.rectangles.remove(rect_id)
                self.boundingBoxes.remove(bbox)
                self.update_boundbox_list()
                
                return True

         return False

    def on_mouse_click(self, event):
        print(self.selected_item.get())
        if (self.selected_item.get() == "Delete boxes"):
            self.is_inside_box(event.x, event.y)  
        else:
            self.start_x = event.x
            self.start_y = event.y
            print(self.selected_item)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, width=2, outline=colors[self.selected_item.get()], tags="bbox")
        
    def on_mouse_drag(self, event):
        if self.selected_item.get() not in ["Disable labeling", "Delete boxes"]:
            x = min(max(0, event.x), self.image.width)
            y = min(max(0, event.y), self.image.height)
            self.canvas.coords(self.rect, self.start_x, self.start_y, x, y)

    def on_mouse_release(self, event):
        if self.selected_item.get() not in ["Disable labeling", "Delete boxes"]:
            end_x = min(max(0, event.x), self.image.width)
            end_y = min(max(0, event.y), self.image.height)
            start_x = min(self.start_x, end_x)
            start_y = min(self.start_y, end_y)
            end_x = max(self.start_x, end_x)
            end_y=max(self.start_y, end_y)
            bounding_box = (start_x, start_y, end_x, end_y, self.selected_item.get())
            self.boundingBoxes.append(bounding_box)
            self.update_boundbox_list()
            self.rectangles.append(self.rect)
            self.start_x = None
            self.start_y = None
            self.rect = None

    def update_boundbox_list(self):
        self.text.delete(1.0, END)
        for box in self.boundingBoxes:
            self.text.insert(END,f'({box[0]},{box[1]}),({box[2]},{box[3]}) - {box[4]} \n')


    def update_image(self, image, image_index, first_img=False):
        if not first_img: 
            self.save_bboxes(self.current_index)
        self.current_index = image_index
        new_image = image
        self.photo = ImageTk.PhotoImage(new_image, master=self.root)
        self.canvas.config(width=new_image.width, height=new_image.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=NW, image=self.photo)
        self.image = new_image
        formatted_index =str(image_index).zfill(self.index_length)
        next_filename = f"{self.folder_path}/{self.nameing_prefix}_{formatted_index}.txt"
        print(next_filename)
        self.rectangles = []
        self.boundingBoxes = self.read_bboxes(next_filename)
        for box in self.boundingBoxes:
            start_x, start_y, end_x, end_y, crack_type = box
            rect = self.canvas.create_rectangle(start_x, start_y, end_x, end_y, width=3, outline=colors[crack_type])
            self.rectangles.append(rect)
        self.update_boundbox_list()


    def save_bboxes(self, index):
   
        class_map = {"D00": 0,
                     "D10": 1,
                     "D20": 2,
                     "D40" : 3}
        formatted_index =str(index).zfill(self.index_length)
        with open(f"{self.folder_path}/{self.nameing_prefix}_{formatted_index}.txt", "w") as f:    
            for box in self.boundingBoxes:
                start_x, start_y, end_x, end_y, crack_type = box
                crack_id = class_map[crack_type]
                center_x_norm = ((start_x+end_x)//2)/self.image.width
                center_y_norm = ((start_y+end_y)//2)/self.image.height
                width_norm = (end_x-start_x)/self.image.width
                height_norm = (end_y-start_y)/self.image.height
                f.write(f"{crack_id} {center_x_norm} {center_y_norm} {width_norm} {height_norm}\n")
   
    def read_bboxes(self, filename):
        class_map_inv = {0: "D00",
                        1: "D10",
                        2: "D20",
                        4: "D40"}

        bounding_boxes = []
        try:
            with open(filename, "r") as f:
                lines = f.readlines()

            for line in lines:
                parts = line.strip().split()
                if len(parts) == 5:  # Ensure correct format
                    crack_id = int(parts[0])
                    center_x_norm = float(parts[1])
                    center_y_norm = float(parts[2])
                    width_norm = float(parts[3])
                    height_norm = float(parts[4])

                    crack_type = class_map_inv.get(crack_id, "Unknown")
                    if crack_type != "Unknown":
                        # Convert normalized coordinates back to pixel coordinates
                        start_x = int((center_x_norm - width_norm / 2) * self.image.width)
                        start_y = int((center_y_norm - height_norm / 2) * self.image.height)
                        end_x = int((center_x_norm + width_norm / 2) * self.image.width)
                        end_y = int((center_y_norm + height_norm / 2) * self.image.height)

                        bounding_boxes.append((start_x, start_y, end_x, end_y, crack_type))
            return bounding_boxes
        except:
            return bounding_boxes