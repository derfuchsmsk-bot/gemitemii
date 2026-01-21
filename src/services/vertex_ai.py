import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
from src.config import settings
import base64

class VertexAIService:
    def __init__(self):
        vertexai.init(
            project=settings.PROJECT_ID, 
            location=settings.REGION
        )
        self.flash_model = GenerativeModel("gemini-3-flash-preview") 
        self.pro_model = GenerativeModel("gemini-3-pro-preview")
        
        # New Gemini 3 Pro Image model (Nano Banana)
        self.image_model = GenerativeModel("gemini-3-pro-image-preview")

    async def generate_text(self, prompt: str, history: list = None, model_type: str = "flash") -> str:
        model = self.flash_model if model_type == "flash" else self.pro_model
        chat = model.start_chat(history=history or [])
        response = await chat.send_message_async(prompt)
        return response.text

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> bytes:
        # Generate image using Gemini 3 Pro Image
        # Based on documentation: Output is "Text and image"
        
        response = await self.image_model.generate_content_async(prompt)
        
        # Extract image from response parts
        # Gemini usually returns parts. We need to find the one with inline_data (image)
        for part in response.candidates[0].content.parts:
            # Check for inline data (image bytes)
            if hasattr(part, 'inline_data') and part.inline_data:
                 return part.inline_data.data
            
            # Or maybe it's accessible differently in the SDK version
            # Usually part.inline_data.data is correct for python-vertexai
            
        # If no image found, raise error
        raise ValueError("No image generated in response. The model might have refused or returned only text.")

    async def edit_image(self, image_bytes: bytes, prompt: str) -> bytes:
        # Edit image using Gemini 3 Pro Image
        # Input: Text + Image
        
        image_part = Part.from_data(data=image_bytes, mime_type="image/png")
        
        response = await self.image_model.generate_content_async([prompt, image_part])
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                return part.inline_data.data
        
        raise ValueError("No edited image generated in response")

vertex_service = VertexAIService()
