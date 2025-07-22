import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.config import settings
from src.controllers import property_controller, auth_controller
from src.infrastructure.telegram_bot.bot import setup_bot_application
from src.app.startup import user_use_cases, property_use_cases

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for the Ethiopian Real Estate Platform, serving a web app and Telegram bot.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_app = setup_bot_application(user_use_cases, property_use_cases)

async def run_bot():
    """Initializes and runs the Telegram bot in the background."""
    try:
        await bot_app.initialize()
        await bot_app.updater.start_polling()
        await bot_app.start()
        logger.info("Telegram bot has started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")

@app.on_event("startup")
async def on_startup():
    """Handles application startup logic."""
    logger.info("FastAPI application starting up...")
    await user_use_cases.initialize_admin_user()
    asyncio.create_task(run_bot())

@app.on_event("shutdown")
async def on_shutdown():
    """Handles application shutdown logic."""
    logger.info("FastAPI application shutting down...")
    if bot_app.updater and bot_app.updater.running:
        await bot_app.updater.stop()
    await bot_app.stop()
    logger.info("Telegram bot has been stopped.")

app.include_router(property_controller.router)
app.include_router(auth_controller.router)

@app.get("/", tags=["Health Check"])
def health_check():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )