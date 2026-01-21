import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.generative_models import GenerativeModel, Part, Image
from src.config import settings

class VertexAIService:
    def __init__(self):
        # In Cloud Run, credentials are automatically discovered if GOOGLE_APPLICATION_CREDENTIALS is not set
        # But if it IS set in config.py (even to None/Empty), we should be careful.
        
        # Explicitly passing credentials=None forces ADC (Application Default Credentials)
        vertexai.init(
            project=settings.PROJECT_ID, 
            location=settings.REGION
        )
        self.flash_model = GenerativeModel("gemini-3.0-flash-preview") 
        self.pro_model = GenerativeModel("gemini-3.0-pro-preview")
        
        # Initialize Imagen model
        # Use 'imagegeneration@006' or newer for better quality
        self.imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@006")

    async def generate_text(self, prompt: str, history: list = None, model_type: str = "flash") -> str:
        model = self.flash_model if model_type == "flash" else self.pro_model
        chat = model.start_chat(history=history or [])
        response = await chat.send_message_async(prompt)
        return response.text

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> str:
        # Generate image using Imagen
        images = self.imagen_model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        
        # Save to a temporary URL or upload to Cloud Storage
        # Since we can't return bytes directly as URL to Telegram easily without saving,
        # we will return the first image object, and handler will handle bytes.
        # But for this interface we need to change return type or logic.
        
        # Important: Imagen API returns Image object which has ._image_bytes or .save()
        # To make it compatible with current handler which expects URL:
        # 1. Upload to GCS (Best practice)
        # 2. Return bytes and change handler (Easier for MVP)
        
        # Let's change this method to return bytes, and update handler.
        return images[0]._image_bytes

    async def edit_image(self, image_bytes: bytes, prompt: str) -> str:
        # Placeholder for image editing
        return "https://via.placeholder.com/1024"

vertex_service = VertexAIService()
