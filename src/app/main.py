import asyncio
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from telegram import Update
import os

from src.utils.config import settings
from src.controllers import property_controller, auth_controller, admin_controller
from src.infrastructure.telegram_bot.bot import setup_bot_application
from src.infrastructure.repository.mysql_repo import MySQLRealEstateRepository
from src.app.startup import user_use_cases, property_use_cases
from src.utils.exceptions import RealEstatePlatformException, NotFoundError

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for the Ethiopian Real Estate Platform, serving a web app and Telegram bot.",
    version="1.0.0",
    # Add docs_url=None, redoc_url=None to disable interactive docs in production
    # docs_url=None, 
    # redoc_url=None
)

application = app  # For compatibility with some deployment setups
# --- Centralized FastAPI Exception Handler ---
@app.exception_handler(RealEstatePlatformException)
async def custom_app_exception_handler(request: Request, exc: RealEstatePlatformException):
    logger.error(f"Application error occurred for request {request.url}: {exc.message}")
    
    status_code = 500  # Internal Server Error by default
    if isinstance(exc, NotFoundError):
        status_code = 404  # Not Found
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )

# --- CORS ---
# If credentials are allowed, we must specify explicit origins (no "*")
frontend_origin = getattr(settings, 'FRONTEND_ORIGIN', "http://localhost:5173")
service_origin = settings.WEB_APP_URL if hasattr(settings, 'WEB_APP_URL') and settings.WEB_APP_URL else None
public_base = getattr(settings, 'PUBLIC_BASE_URL', None)
allowed_origins = [frontend_origin]
if service_origin:
    allowed_origins.append(service_origin)
if public_base:
    allowed_origins.append(public_base)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Bot and Webhook Setup ---
bot_app = setup_bot_application(user_use_cases, property_use_cases)
WEBHOOK_PATH = "/webhook"
# Ensure you have SERVICE_URL in your settings file (e.g., from an environment variable)
# It should be your full Cloud Run URL: https://allin1-br-....run.app
WEBHOOK_URL = f"{settings.SERVICE_URL}{WEBHOOK_PATH}"

@app.on_event("startup")
async def on_startup():
    """Handles application startup: initialize DB and set Telegram webhook."""
    logger.info("FastAPI application starting up...")
    await user_use_cases.initialize_admin_user()
    
    # Set the webhook
    try:
        await bot_app.bot.set_webhook(
            url=WEBHOOK_URL, 
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True # Recommended to clear out old updates
        )
        logger.info(f"Telegram webhook set successfully to {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"FATAL: Failed to set Telegram webhook: {e}")

    # These are still needed to prepare the application instance
    await bot_app.initialize()
    await bot_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    """Handles application shutdown: properly stop the bot application."""
    logger.info("FastAPI application shutting down...")
    await bot_app.stop()
    logger.info("Bot application has been stopped.")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """
    This is the main endpoint that receives updates from Telegram.
    """
    try:
        update_data = await request.json()
        update = Update.de_json(data=update_data, bot=bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}")
        return Response(status_code=500) # Let Telegram know something went wrong

# --- Static Files ---
# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- API Routers ---
app.include_router(property_controller.router)
app.include_router(property_controller.car_router)
app.include_router(auth_controller.router)
app.include_router(admin_controller.router)

@app.get("/", tags=["Health Check"])
def health_check():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "1.0.0"}

# --- Image Serving Endpoint (DB Blob) ---
repo_for_images = None
try:
    # Only available if using MySQL repo
    if hasattr(property_use_cases.repo, 'get_image_blob'):
        repo_for_images = property_use_cases.repo
except Exception:
    pass

@app.get("/images/{image_id}")
async def serve_image(image_id: str):
    if not repo_for_images:
        return Response(status_code=404)
    record = await repo_for_images.get_image_blob(image_id)
    if not record:
        return Response(status_code=404)
    content_type = record.get('content_type', 'application/octet-stream')
    data = record.get('data')
    return Response(content=data, media_type=content_type)

# --- Main Execution ---
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    # 'reload=True' is great for development but should be False in production
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False 
    )