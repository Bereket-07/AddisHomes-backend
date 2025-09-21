import aiohttp
import firebase_admin
from firebase_admin import storage
from uuid import uuid4
import os

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
    # 1. Get Telegram file path
    tg_file = await bot.get_file(file_id)
    file_url = tg_file.file_path  # relative path like "photos/file_123.jpg"
    download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_url}"

    # 2. Download file bytes
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download Telegram file: {resp.status}")
            file_bytes = await resp.read()

    # 3. Upload to Firebase Storage
    bucket = storage.bucket()
    blob_name = f"properties/{uuid4()}.jpg"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type="image/jpeg")

    # 4. Make file public (or use signed URLs if you prefer)
    blob.make_public()
    return blob.public_url
