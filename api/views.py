from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from PIL import Image
import io

from .detector import calculate_blockage_and_risk

class BlockageDetectionView(APIView):
    """
    API endpoint that accepts an image upload in a POST request,
    runs YOLO detection to identify garbage, and returns the 
    calculated blockage percentage and flood risk level.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # 1. Validate that an image file is provided in the request
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided. Please send an image file under the key 'image'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        uploaded_image = request.FILES['image']
        
        # 2. Try parsing the file as an image
        try:
            pil_image = Image.open(uploaded_image)
            # Ensure it is in RGB format (handles PNGs, grayscale, etc. properly for YOLO)
            pil_image = pil_image.convert("RGB")
        except Exception as e:
            return Response(
                {"error": f"Invalid image file. Details: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 3. Perform calculations
        try:
            result = calculate_blockage_and_risk(pil_image)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"An error occurred during object detection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
