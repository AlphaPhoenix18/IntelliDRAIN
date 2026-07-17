import os
import ctypes

try:
    import torch
    dll_path = os.path.join(os.path.dirname(torch.__file__), "lib", "c10.dll")
    if os.path.exists(dll_path):
        ctypes.CDLL(os.path.normpath(dll_path))
except Exception:
    pass

from ultralytics import YOLO

# 1. Load the model
model = YOLO("yolov8n.pt")

# 2. Run detection on a sample image (using an official sample that has a bottle!)
results = model("https://ultralytics.com/images/bus.jpg")

# Define what we consider as "Garbage" from YOLO's standard 80 objects
GARBAGE_CLASSES = ["bottle", "cup", "handbag", "bowl"]

# Define a mock total area for the drain grate in pixels
# (Assuming a standard 640x640 frame size for simplicity)
TOTAL_DRAIN_AREA = 640 * 640  
total_garbage_area = 0

print("\n--- INTELLIDRAIN ANALYSIS ---")

for result in results:
    boxes = result.boxes
    
    for box in boxes:
        class_id = int(box.cls[0])
        object_name = model.names[class_id]
        
        # Check if the detected object matches our garbage list
        if object_name in GARBAGE_CLASSES:
            confidence = float(box.conf[0])
            
            # Get coordinates: x_min, y_min, x_max, y_max
            coords = box.xyxy[0].tolist()
            x_min, y_min, x_max, y_max = coords
            
            # Calculate the area of this specific bounding box
            width = x_max - x_min
            height = y_max - y_min
            item_area = width * height
            
            # Add to our total garbage accumulation
            total_garbage_area += item_area
            
            print(f"🗑️ Found Garbage: {object_name} | Confidence: {confidence:.2f} | Area: {item_area:.0f} px")

# 3. Calculate Final Blockage Percentage
blockage_percentage = (total_garbage_area / TOTAL_DRAIN_AREA) * 100

# Cap it at 100% just in case boxes overlap heavily
if blockage_percentage > 100:
    blockage_percentage = 100.0

print("-" * 30)
print(f"📊 FINAL CALCULATED BLOCKAGE: {blockage_percentage:.2f}%")
print("-" * 30)