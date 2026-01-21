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

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes, str]:
        # Generate image using Gemini 3 Pro Image
        # Output is "Text and image"
        
        full_prompt = (
            f"User request: '{prompt}'. "
            f"Aspect Ratio: {aspect_ratio}. "
            f"Action: 1. Create a detailed prompt in English for this image. 2. GENERATE the image."
        )
        
        response = await self.image_model.generate_content_async(full_prompt)
        
        image_bytes = None
        text_response = ""

        # Parse response parts
        # Gemini usually returns a list of parts (Text, Image, etc.)
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                # Check if part has text attribute
                # In vertexai SDK, part can be accessed via .text if it's a text part
                try:
                    if part.text:
                        text_response += part.text + "\n"
                except:
                    pass
                
                # Check for inline data (image)
                if hasattr(part, 'inline_data') and part.inline_data:
                     image_bytes = part.inline_data.data

        if not image_bytes:
            # Fallback: sometimes model refuses to generate image but gives text reason
            raise ValueError(f"No image generated. Model said: {text_response}")
            
        return image_bytes, text_response.strip()

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
