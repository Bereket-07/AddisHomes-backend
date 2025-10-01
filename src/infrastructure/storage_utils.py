import aiohttp
import firebase_admin
from firebase_admin import storage
from uuid import uuid4
import os
from io import BytesIO

# Make sure Firebase app is initialized somewhere in your app bootstrap
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        options={
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
        }
    )

async def upload_telegram_photo_to_storage(bot, file_id: str) -> str:
    """
    Downloads a Telegram photo by file_id and uploads it to Firebase Storage.
    Returns the public URL.
    """
    # 1. Get Telegram file and download via API (avoids manual URL 404 issues)
    tg_file = await bot.get_file(file_id)
    buffer = BytesIO()
    await tg_file.download_to_memory(out=buffer)
    file_bytes = buffer.getvalue()

    # 3. Store image either in Firebase Storage (if configured) or locally
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    if bucket_name:
        bucket = storage.bucket(bucket_name)
        blob_name = f"properties/{uuid4()}.jpg"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(file_bytes, content_type="image/jpeg")

        # 4a. Make file public (or use signed URLs if you prefer)
        blob.make_public()
        return blob.public_url
    else:
        # 4b. Fallback: save locally similar to website uploads
        upload_dir = "uploads/properties"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid4()}.jpg")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        # Return URL path consistent with website endpoints
        return f"/uploads/properties/{os.path.basename(file_path)}"
