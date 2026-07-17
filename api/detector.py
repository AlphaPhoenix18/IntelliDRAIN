import os
import ctypes
from django.conf import settings
from PIL import Image

# Global placeholder for the lazy-loaded YOLO model
_model = None

def get_yolo_model():
    """
    Lazy loads the YOLOv8 model once and caches it in memory.
    """
    global _model
    if _model is None:
        # Load Windows dependencies if PyTorch requires c10.dll (copied from detect.py logic)
        try:
            import torch
            dll_path = os.path.join(os.path.dirname(torch.__file__), "lib", "c10.dll")
            if os.path.exists(dll_path):
                ctypes.CDLL(os.path.normpath(dll_path))
        except Exception:
            pass
        
        from ultralytics import YOLO
        # Path to yolov8n.pt in the workspace root
        model_path = os.path.join(settings.BASE_DIR, "yolov8n.pt")
        _model = YOLO(model_path)
    
    return _model


def calculate_blockage_and_risk(pil_image):
    """
    Runs YOLO detection on a PIL image, calculates the drain blockage percentage
    based on garbage objects, and evaluates flood risk.
    """
    # 1. Load the cached YOLO model
    model = get_yolo_model()
    
    # 2. Run inference
    # YOLO can accept a PIL Image directly.
    results = model(pil_image)
    
    # Define what we consider as "Garbage" (identical to detect.py)
    GARBAGE_CLASSES = ["bottle", "cup", "handbag", "bowl"]
    
    # Use the actual uploaded image dimensions for the total grate area
    img_width, img_height = pil_image.size
    total_drain_area = img_width * img_height
    total_garbage_area = 0.0
    
    detections = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls[0])
            object_name = model.names[class_id]
            
            # Check if the detected object is garbage
            if object_name in GARBAGE_CLASSES:
                confidence = float(box.conf[0])
                
                # Get bounding box: [x_min, y_min, x_max, y_max]
                coords = box.xyxy[0].tolist()
                x_min, y_min, x_max, y_max = coords
                
                # Calculate bounding box area
                width = x_max - x_min
                height = y_max - y_min
                item_area = width * height
                
                # Accumulate area
                total_garbage_area += item_area
                
                detections.append({
                    "class": object_name,
                    "confidence": round(confidence, 4),
                    "box": [round(c, 2) for c in coords],
                    "area_px": round(item_area, 2)
                })
    
    # 3. Calculate Blockage Percentage
    if total_drain_area > 0:
        blockage_percentage = (total_garbage_area / total_drain_area) * 100
    else:
        blockage_percentage = 0.0
        
    # Cap blockage at 100% in case boxes overlap heavily
    if blockage_percentage > 100:
        blockage_percentage = 100.0
        
    # 4. Assess Flood Risk
    if blockage_percentage < 25.0:
        flood_risk = "Low"
    elif blockage_percentage < 50.0:
        flood_risk = "Moderate"
    elif blockage_percentage < 75.0:
        flood_risk = "High"
    else:
        flood_risk = "Critical"
        
    return {
        "status": "success",
        "blockage_percentage": round(blockage_percentage, 2),
        "flood_risk": flood_risk,
        "total_garbage_area_px": round(total_garbage_area, 2),
        "total_drain_area_px": total_drain_area,
        "detections": detections
    }
