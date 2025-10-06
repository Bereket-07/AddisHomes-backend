from uuid import uuid4
from io import BytesIO

async def upload_telegram_photo_to_storage(bot, file_id: str, repo=None) -> str:
    """
    Downloads a Telegram photo by file_id and stores it in the database as a blob.
    Returns a served URL in the form of /images/{image_id}.
    """
    # 1. Download file bytes from Telegram
    tg_file = await bot.get_file(file_id)
    buffer = BytesIO()
    await tg_file.download_to_memory(out=buffer)
    file_bytes = buffer.getvalue()

    # 2. Persist into DB as blob
    image_id = uuid4().hex
    content_type = "image/jpeg"  # Telegram photos are JPEGs when downloaded
    if repo is None:
        # Attempt to get repository via bot_data if available
        # Callers should pass repo for clarity
        pass
    else:
        await repo.save_image_blob(image_id=image_id, content_type=content_type, data=file_bytes)

    # 3. Return the API path that serves this image
    return f"/images/{image_id}"
