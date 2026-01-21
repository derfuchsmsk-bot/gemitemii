import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
from src.config import settings
import base64
import asyncio
import logging

logger = logging.getLogger(__name__)

class VertexAIService:
    def __init__(self):
        # Use us-central1 as fallback or main location, 
        # as global prediction is sometimes tricky with SDKs.
        # But for Gemini 3, let's try to respect the config unless forced.
        # Given 429 errors and docs about 'global' endpoint support:
        
        # We explicitly set location to 'us-central1' because:
        # 1. 'global' location in init often throws "location must be a region" in Python SDK.
        # 2. 'us-central1' is the main region where Gemini 3 lives.
        # 3. If user wants to use Global Endpoint feature (for routing), it is usually handled 
        #    by not specifying location or using specific api_endpoint, but 'us-central1' is the safest bet for resources.
        
        # However, to use the "Global" endpoint (publishers/google/models/...), 
        # we might need to set api_endpoint='us-central1-aiplatform.googleapis.com' but use a global resource name?
        # No, usually just picking a region like us-central1 works best for quota.
        
        vertexai.init(
            project=settings.PROJECT_ID, 
            location="global" 
        )
        
        self.flash_model = GenerativeModel("gemini-3-flash-preview") 
        self.pro_model = GenerativeModel("gemini-3-pro-preview")
        self.image_model = GenerativeModel("gemini-3-pro-image-preview")

    async def _retry_request(self, func, *args, **kwargs):
        """Retry wrapper for 429 errors"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                # Check for Quota/Resource Exhausted errors
                if "429" in error_str or "Resource exhausted" in error_str:
                    if attempt == max_retries - 1:
                        raise e
                    
                    delay = base_delay * (2 ** attempt) # Exponential backoff: 2, 4, 8
                    logger.warning(f"Got 429, retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    raise e

    async def generate_text(self, prompt: str, history: list = None, model_type: str = "flash") -> str:
        model = self.flash_model if model_type == "flash" else self.pro_model
        
        async def _call():
            chat = model.start_chat(history=history or [])
            # Set a timeout for the response
            response = await asyncio.wait_for(chat.send_message_async(prompt), timeout=60.0)
            return response.text

        return await self._retry_request(_call)

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes, str]:
        
        full_prompt = (
            f"User request: '{prompt}'. "
            f"Aspect Ratio: {aspect_ratio}. "
            f"Action: 1. Create a detailed prompt in English for this image. 2. GENERATE the image."
        )
        
        async def _call():
            # Set a timeout for image generation
            response = await asyncio.wait_for(self.image_model.generate_content_async(full_prompt), timeout=90.0)
            
            image_bytes = None
            text_response = ""

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    try:
                        if part.text:
                            text_response += part.text + "\n"
                    except:
                        pass
                    
                    if hasattr(part, 'inline_data') and part.inline_data:
                         image_bytes = part.inline_data.data

            if not image_bytes:
                raise ValueError(f"No image generated. Model said: {text_response}")
                
            return image_bytes, text_response.strip()

        return await self._retry_request(_call)

    async def edit_image(self, image_bytes: bytes, prompt: str) -> bytes:
        image_part = Part.from_data(data=image_bytes, mime_type="image/png")
        
        async def _call():
            response = await asyncio.wait_for(
                self.image_model.generate_content_async([prompt, image_part]),
                timeout=90.0
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return part.inline_data.data
            raise ValueError("No edited image generated")

        return await self._retry_request(_call)

vertex_service = VertexAIService()
