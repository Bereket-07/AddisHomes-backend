"""
Updated image serving endpoint with proper error handling and logging.
Copy this code to replace the image serving section in your deployed main.py
"""

# --- Image Serving Endpoint (DB Blob) ---
import logging
logger = logging.getLogger(__name__)

repo_for_images = property_use_cases.repo

@app.get("/images/{image_id}")
async def serve_image(image_id: str):
    logger.info(f"Image request for ID: {image_id}")
    
    if not repo_for_images:
        logger.error("repo_for_images is None - image serving not available")
        return Response(status_code=404)
    
    try:
        # Log the repo type to verify it's MySQL
        logger.info(f"Using repository type: {type(repo_for_images).__name__}")
        
        record = await repo_for_images.get_image_blob(image_id)
        
        if not record:
            logger.warning(f"Image not found in database: {image_id}")
            return Response(status_code=404)
        
        content_type = record.get('content_type', 'application/octet-stream')
        data = record.get('data')
        
        if not data:
            logger.error(f"Image {image_id} has no data")
            return Response(status_code=404)
        
        logger.info(f"Serving image {image_id}, type: {content_type}, size: {len(data)} bytes")
        return Response(content=data, media_type=content_type)
        
    except Exception as e:
        logger.error(f"Error serving image {image_id}: {e}", exc_info=True)
        return Response(status_code=500)
