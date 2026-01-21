import logging
from google.cloud import firestore
from src.config import settings

logger = logging.getLogger(__name__)

# Initialize Firestore
try:
    db = firestore.Client(project=settings.PROJECT_ID)
    users_ref = db.collection("user_settings")
except Exception as e:
    logger.error(f"Failed to initialize Firestore: {e}")
    db = None

DEFAULT_SETTINGS = {
    "aspect_ratio": "1:1",
    "style": "photo",
    "magic_prompt": True,
    "resolution": "Standard" # Standard, HD, 4K
}

def get_user_settings(user_id: int) -> dict:
    if db is None:
        return DEFAULT_SETTINGS.copy()
        
    try:
        doc = users_ref.document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        logger.error(f"Error fetching settings for {user_id}: {e}")
        
    return DEFAULT_SETTINGS.copy()

def update_user_setting(user_id: int, key: str, value: any):
    if db is None:
        return
        
    try:
        users_ref.document(str(user_id)).set({key: value}, merge=True)
    except Exception as e:
        logger.error(f"Error updating setting for {user_id}: {e}")

def get_all_user_ids():
    if db is None:
        return []
    return [doc.id for doc in users_ref.stream()]
