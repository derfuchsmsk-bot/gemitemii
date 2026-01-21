import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
from src.config import settings
import base64
import asyncio
import logging

logger = logging.getLogger(__name__)

from google.cloud import storage
import uuid

class VertexAIService:
    def __init__(self):
        vertexai.init(
            project=settings.PROJECT_ID, 
            location=settings.REGION 
        )
        
        self.flash_model = GenerativeModel("gemini-3-flash-preview") 
        self.pro_model = GenerativeModel("gemini-3-pro-preview")
        self.image_model = GenerativeModel("gemini-3-pro-image-preview")
        
        # Initialize GCS client
        try:
            self.storage_client = storage.Client(project=settings.PROJECT_ID)
            logger.info(f"GCS client initialized successfully for project {settings.PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.storage_client = None

    async def upload_to_gcs(self, image_bytes: bytes) -> str:
        """Uploads image to GCS and returns the file name (UUID)"""
        if not self.storage_client:
            logger.warning("GCS Upload skipped: Storage client not initialized")
            return None
        if not settings.GCS_BUCKET_NAME:
            logger.warning("GCS Upload skipped: GCS_BUCKET_NAME not set")
            return None
            
        try:
            bucket = self.storage_client.bucket(settings.GCS_BUCKET_NAME)
            file_name = f"{uuid.uuid4()}.png"
            blob = bucket.blob(file_name)
            
            logger.info(f"Uploading {len(image_bytes)} bytes to GCS bucket {settings.GCS_BUCKET_NAME} as {file_name}")
            
            # Use run_in_executor for synchronous GCS library
            await asyncio.to_thread(blob.upload_from_string, image_bytes, content_type="image/png")
            
            logger.info("GCS Upload successful")
            return file_name
        except Exception as e:
            logger.error(f"GCS Upload failed: {e}", exc_info=True)
            return None

    async def download_from_gcs(self, file_name: str) -> bytes:
        """Downloads image from GCS"""
        if not self.storage_client or not settings.GCS_BUCKET_NAME:
            logger.warning("GCS Download skipped: client or bucket not set")
            return None
            
        try:
            logger.info(f"Downloading {file_name} from GCS bucket {settings.GCS_BUCKET_NAME}")
            bucket = self.storage_client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(file_name)
            data = await asyncio.to_thread(blob.download_as_bytes)
            logger.info(f"Downloaded {len(data)} bytes from GCS")
            return data
        except Exception as e:
            logger.error(f"GCS Download failed for {file_name}: {e}", exc_info=True)
            return None

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
            f"Action: GENERATE the image. "
            f"In your text response, provide ONLY a very brief, one-sentence description of the image in Russian. "
            f"DO NOT include your reasoning, thoughts, or internal monologue."
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
