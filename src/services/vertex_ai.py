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
            location=settings.REGION 
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
                logger.error(f"Attempt {attempt+1} failed: {error_str}")
                # Check for Quota/Resource Exhausted errors
                if "429" in error_str or "Resource exhausted" in error_str or "exhausted" in error_str:
                    if attempt == max_retries - 1:
                        logger.error("Max retries reached for rate limit.")
                        raise e
                    
                    delay = base_delay * (2 ** attempt) # Exponential backoff: 2, 4, 8
                    logger.warning(f"Got 429/Quota, retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    # Non-retryable error
                    raise e

    async def generate_text(self, prompt: str, history: list = None, model_type: str = "flash") -> str:
        model = self.flash_model if model_type == "flash" else self.pro_model
        
        async def _call():
            chat = model.start_chat(history=history or [])
            # Increased timeout for text generation as well
            response = await asyncio.wait_for(chat.send_message_async(prompt), timeout=120.0)
            return response.text

        return await self._retry_request(_call)

    async def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> tuple[bytes, str]:
        
        full_prompt = (
            f"User request: '{prompt}'. "
            f"Aspect Ratio: {aspect_ratio}. "
            f"Action: 1. Create a detailed prompt in English for this image. 2. GENERATE the image."
        )
        
        logger.info(f"Generating image with AR: {aspect_ratio}")
        
        async def _call():
            # Increased timeout significantly for image generation (can take 3-5 mins on cold start)
            response = await asyncio.wait_for(self.image_model.generate_content_async(full_prompt), timeout=300.0)
            
            image_bytes = None
            text_response = ""

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        try:
                            if hasattr(part, 'text') and part.text:
                                text_response += part.text + "\n"
                        except Exception:
                            pass
                        
                        # Handle inline_data (images)
                        # Try both 'inline_data' attribute and checking mime_type
                        if hasattr(part, 'inline_data') and part.inline_data:
                             image_bytes = part.inline_data.data
                             break
            else:
                logger.warning("No candidates in response")

            if not image_bytes:
                error_msg = f"No image generated. Model response: {text_response[:500]}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
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
