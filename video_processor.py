from datetime import datetime, timedelta
from scipy.interpolate import CubicSpline
import json
import numpy as np
from ultralytics import YOLO, SAM
import os
import cv2
import torch

def get_bounding_box(mask):
    # Convert tensor to numpy array if it's a PyTorch tensor
    if isinstance(mask, torch.Tensor):
        mask = mask.cpu().numpy()
   
    _ , height, width = mask.shape  
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    
    for y in range(height):
        for x in range(width):
            if mask[0, y, x] == True:  
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    
    # If no True pixels found, return None
    if min_x == width or min_y == height or max_x == 0 or max_y == 0:
        print("No 'True' pixels found in the mask.")
        return None
     
    width_bb = max_x - min_x + 1
    height_bb = max_y - min_y + 1
    
    return min_x, min_y, width_bb, height_bb


def crop_image(image_path, min_x, min_y, max_x, max_y):
    image = cv2.imread(image_path)
    cropped_image = image[min_y:max_y, min_x:max_x]
    return cropped_image

def extract_frames(video_path, output_folder, focus_point,frames_per_second, auto_crop=False):
    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()
    count = 0
    img_index = 0
    print(video_path)
    prefix = video_path.split(".")[0].split("/")[-1]
    print(prefix)
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    num_digits = len(str(total_frames))
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    skip_rate = fps // frames_per_second
    if auto_crop:
        sam = SAM('sam_l.pt')
        cropped_output_folder = f"{output_folder}_cropped"
        while success:
            if count % skip_rate == 0:
                filename = f"{prefix}_{img_index:0{num_digits}}.jpg"
                cv2.imwrite(output_folder + "/" + filename, image)  # save frame as JPEG file
                result = sam(output_folder + "/" + filename, points=focus_point)
                bbox = get_bounding_box(result[0].masks.data)
                min_x, min_y, width, height = bbox
                cropped_image = crop_image(output_folder + "/" + filename,min_x, min_y, min_x+width, min_y+height)
                retries = 0
                w, h = focus_point

                while (cropped_image.shape[0] < 300 and cropped_image.shape[1] < 300):
                    print("The cropped image is to small, retrying...")
                    w += 50
                    print("The cropped image is to small, retrying with " + str((w,h)))
                    result = sam(output_folder + "/" + filename, points=(w,h))
                    bbox = get_bounding_box(result[0].masks.data)
                    min_x, min_y, width, height = bbox
                    cropped_image = crop_image(output_folder + "/" + filename,min_x, min_y, min_x+width, min_y+height)
                    retries += 1
                    if retries ==3:
                        break
                cv2.imwrite(f"{cropped_output_folder}/{filename}", cropped_image)
                print('Saved frame %s' % filename)
                img_index += 1
            success, image = vidcap.read()
            count += 1
    else: 
         while success:
            if count % skip_rate == 0:
                filename = f"{prefix}_{img_index:0{num_digits}}.jpg"
                cv2.imwrite(output_folder + "/" + filename, image)  # save frame as JPEG file
                img_index += 1
            success, image = vidcap.read()
            count += 1


def crop_images(image_folder, output_folder, focus_point):
    sam = SAM('sam_l.pt')
    image_files = os.listdir(image_folder)
    image_paths = [os.path.join(image_folder, file) for file in image_files]
    for path in image_paths:
        
        filename = path.split("\\")[-1]
        filename = filename.split(".")[0]
        
        result = sam(path, points=focus_point)
        bbox = get_bounding_box(result[0].masks.data)
        min_x, min_y, width, height = bbox
        cropped_image = crop_image(path,min_x, min_y, min_x+width, min_y+height)
        print(f"{output_folder}/{filename}")
        cv2.imwrite(f"{output_folder}/{filename}.jpg", cropped_image)

def process_video_geo(video_path, model_path, save_dir_images, json_data, project, sub_project, focus_point,fps, auto_crop=False):
    starttime, stoptime, coordinates, latdir,longdir = read_json(json_data)                                                                               
    latitudes, longitudes, timestamps = seperate_latitude_longitude_timestamps(coordinates)
    datetime1 = datetime.fromisoformat(starttime)
    datetime2 = datetime.fromisoformat(stoptime)
    class_mapping = {
    0: 'D00',
    1: 'D10',
    2: 'D20',
    3: 'D40'
}
# Calculate the time difference
    time_difference = datetime2 - datetime1

    # Convert time difference to seconds
    time_difference_seconds = time_difference.total_seconds()

    print("Time difference in seconds:", time_difference_seconds)
    extract_frames(video_path=video_path, output_folder=save_dir_images, focus_point=focus_point, frames_per_second=fps, auto_crop=auto_crop)
    yolo =  YOLO(model_path)
    
    if auto_crop:
        image_files = os.listdir(f"{save_dir_images}_cropped")
        image_paths = [os.path.join(f"{save_dir_images}_cropped", file) for file in image_files]
    else:
        image_files = os.listdir(save_dir_images)
        image_paths = [os.path.join(save_dir_images, file) for file in image_files]
    time_per_frame = time_difference_seconds / len(image_paths)
    print(time_per_frame)
    results = yolo(image_paths, stream=True,  save_crop=True, save_txt=True, project=project, name=sub_project)
    detections_list = []
    for idx, result in enumerate(results):
        if result.boxes:  # Check if there are any bounding boxes detected
            for box in result.boxes:
                crack_type = box.cls.item()
                conf = box.conf.item()
                time_of_detection = datetime1+timedelta(seconds=(idx*time_per_frame))
                lat_at_sec, long_at_sec = get_position_at_seconds(latitudes, longitudes, timestamps, idx*time_per_frame, starttime)
                lat_at_sec_in_deg, long_at_sec_in_deg = transform_from_nmea_coordinates_to_degrees(lat_at_sec, long_at_sec)
                
                detection = {
                "crackType": class_mapping[int(crack_type)],
                "confidence": conf,
                "timeSinceStart": time_of_detection.strftime("%Y-%m-%d %H:%M:%S"),  # Format datetime as string
                "latitude": lat_at_sec_in_deg,
                "longitude": long_at_sec_in_deg,
                "lat_dir": latdir,
                "long_dir": longdir
                 }   
                detections_list.append(detection)
    output_name = "cracks.json"
    with open(output_name, "w") as file:
        detections_json = json.dumps({"Detections": detections_list}, indent=4)
        file.write(detections_json)

def process_video(video_path, save_dir_images, project, sub_project, focus_point,fps, auto_crop=False):
    extract_frames(video_path=video_path, output_folder=save_dir_images,focus_point=focus_point, frames_per_second=fps, auto_crop=auto_crop)
    yolo =  YOLO("../runs/detect/train31/weights/best.pt")
    
    if auto_crop:
        image_files = os.listdir(f"{save_dir_images}_cropped")
        image_paths = [os.path.join(f"{save_dir_images}_cropped", file) for file in image_files]
    else:
        
        image_files = os.listdir(save_dir_images)
        image_paths = [os.path.join(save_dir_images, file) for file in image_files]

    results = yolo(image_paths, stream=True, save_txt=True, project=project, name=sub_project)
    for result in results:
        boxes = result.boxes  # Boxes object for bbox outputs


def process_folder(data_folder, output_folder, project, sub_project,focus_point, auto_crop=False):
    yolo =  YOLO("../Norway/datasets/ai_cropped/runs/detect/train14/weights/best.pt")
    if auto_crop:
        crop_images(data_folder, output_folder=f"{output_folder}_cropped", focus_point=focus_point)
    if auto_crop:
        image_files = os.listdir(f"{output_folder}_cropped")
        image_paths = [os.path.join(f"{output_folder}_cropped", file) for file in image_files]
    else:
        image_files = os.listdir(data_folder)
        
        image_paths = [os.path.join(data_folder, file) for file in image_files]
    results = yolo(image_paths, stream=True, save_txt=True, project=project, name=sub_project)
    for result in results:
        boxes = result.boxes  # Boxes object for bbox outputs



def read_json(filename: str):
    '''Reads coordinates from a json file and returns them in there original structure'''
    print(filename)
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['startTime'], data['stopTime'], data['coordinates'], data["coordinates"][0]["latDirection"], data["coordinates"][0]["longDirection"]

def transform_from_nmea_coordinates_to_degrees(latitude_ddmm, longitude_ddmm) -> tuple[float, float]: 
    '''Converting the coordinates from nmea format (ddmm.mm) to degreees format (D.d)'''
    # Latitude conversion
    lat_degrees = int(latitude_ddmm // 100)  # Extracting degrees
    lat_minutes = latitude_ddmm % 100  # Extracting minutes
    latitude_decimal = lat_degrees + lat_minutes / 60  # Convert to decimal degrees

    # Longitude conversion
    lon_degrees = int(longitude_ddmm // 100)  # Extracting degrees
    lon_minutes = longitude_ddmm % 100  # Extracting minutes
    longitude_decimal = lon_degrees + lon_minutes / 60  # Convert to decimal degrees
    return latitude_decimal, longitude_decimal

def seperate_latitude_longitude_timestamps(coordinates: list):
    latitudes = []
    longitudes = []
    timestamps = []
    for c in coordinates:
        latitudes.append(c['lat'])
        longitudes.append(c['long'])
        timestamps.append(c['timeStamp'])
    return latitudes, longitudes, timestamps


def convert_timestamp_to_seconds(timestamp: str, starttime: str, utcDifference = 1):
    # Convert 'hhmmss.mm' format to seconds
    start_date = datetime.strptime(starttime, "%Y-%m-%dT%H:%M:%S.%f")

    hours = int(timestamp[:2]) - start_date.hour + utcDifference
    minutes = int(timestamp[2:4]) - start_date.minute
    seconds = int(timestamp[4:6]) - start_date.second
    centiseconds = int(timestamp[7:]) - round(start_date.microsecond/10000)
    total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
    return total_seconds


def interpolate_coordinates_linear(latitudes, longitudes, timestamps, starttime):
    # Convert strings to floats
    latitudes = [float(lat) for lat in latitudes]
    longitudes = [float(lon) for lon in longitudes]
    timestamps = [convert_timestamp_to_seconds(timestamp, starttime) for timestamp in timestamps]

    # Convert timestamps to milliseconds
    timestamps_ms = [timestamp * 1000 for timestamp in timestamps]

    # Create a linearly spaced array for each millisecond
    interpolated_timestamps = np.arange(timestamps_ms[0], timestamps_ms[-1] + 1, 1)

    # Interpolate latitude and longitude
    interpolated_latitudes = np.interp(interpolated_timestamps, timestamps_ms, latitudes)
    interpolated_longitudes = np.interp(interpolated_timestamps, timestamps_ms, longitudes)

    # Convert interpolated timestamps back to seconds
    interpolated_timestamps /= 1000

    return interpolated_latitudes, interpolated_longitudes, interpolated_timestamps


def interpolate_coordinates_smooth(latitudes, longitudes, timestamps, starttime):
    # Convert strings to floats
    latitudes = np.array([float(lat) for lat in latitudes])
    longitudes = np.array([float(lon) for lon in longitudes])
    timestamps = np.array([convert_timestamp_to_seconds(timestamp, starttime) for timestamp in timestamps])

    # Convert timestamps to milliseconds
    timestamps_ms = timestamps * 1000

    # Create a cubic spline interpolation for latitude and longitude
    spline_lat = CubicSpline(timestamps_ms, latitudes)
    spline_lon = CubicSpline(timestamps_ms, longitudes)

    # Interpolate at a higher resolution
    interpolated_timestamps_ms = np.arange(timestamps_ms[0], timestamps_ms[-1] + 1, 1)
    interpolated_latitudes = spline_lat(interpolated_timestamps_ms)
    interpolated_longitudes = spline_lon(interpolated_timestamps_ms)

    # Convert interpolated timestamps back to seconds
    interpolated_timestamps = interpolated_timestamps_ms / 1000

    return interpolated_latitudes, interpolated_longitudes, interpolated_timestamps


def get_position_at_time(latitudes:list, longitudes:list, timestamps:list, target_time:str, starttime: str, utcDifference=0):
    # Interpolate coordinates
    interpolated_latitudes, interpolated_longitudes, interpolated_timestamps = interpolate_coordinates_linear(
        latitudes, longitudes, timestamps, starttime) 
    # Find the index of the target time in the interpolated timestamps
    target_time_seconds = convert_timestamp_to_seconds(target_time, starttime, utcDifference)
    index = np.searchsorted(interpolated_timestamps, target_time_seconds)
    # Return the corresponding latitude and longitude
    return interpolated_latitudes[index], interpolated_longitudes[index]

def get_position_at_seconds(latitudes:list, longitudes:list, timestamps:list, target_seconds:float, starttime: str):
    # Interpolate coordinates
    interpolated_latitudes, interpolated_longitudes, interpolated_timestamps = interpolate_coordinates_linear(
        latitudes, longitudes, timestamps, starttime)
    # Find the index of the target time in the interpolated timestamps
    index = np.searchsorted(interpolated_timestamps, target_seconds)
    # Return the corresponding latitude and longitude
    return interpolated_latitudes[index-1], interpolated_longitudes[index-1]

def write_smooth_geojson_file(input_filename: str, output_filename: str):
    starttime, stoptime, coordinates = read_json(input_filename)
    latitudes, longitudes, timestamps = seperate_latitude_longitude_timestamps(coordinates)
    interpolated_latitudes, interpolated_longitudes, interpolated_timestamps = interpolate_coordinates_smooth(latitudes, longitudes, timestamps)
    interpolated_coordinates = []
    for i in range(len(interpolated_timestamps)):
        i_lat = interpolated_latitudes[i]
        i_long = interpolated_longitudes[i]
        i_lat_dec, i_long_dec = transform_from_nmea_coordinates_to_degrees(i_lat, i_long)
        cord = [i_long_dec, i_lat_dec]
        interpolated_coordinates.append(cord)
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "LineString",
            "coordinates": interpolated_coordinates
        }
    }
    with open(output_filename, 'w') as file:
        json.dump(feature, file)

def write_linear_geojson_file(input_filename: str, output_filename: str):
    starttime, stoptime, coordinates = read_json(input_filename)
    latitudes, longitudes, timestamps = seperate_latitude_longitude_timestamps(coordinates)
    interpolated_latitudes, interpolated_longitudes, interpolated_timestamps = interpolate_coordinates_linear(latitudes, longitudes, timestamps, starttime)
    interpolated_coordinates = []
    for i in range(len(interpolated_timestamps)):
        i_lat = interpolated_latitudes[i]
        i_long = interpolated_longitudes[i]
        i_lat_dec, i_long_dec = transform_from_nmea_coordinates_to_degrees(i_lat, i_long)
        cord = [i_long_dec, i_lat_dec]
        interpolated_coordinates.append(cord)
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "LineString",
            "coordinates": interpolated_coordinates
        }
    }
    with open(output_filename, 'w') as file:
        json.dump(feature, file)