"""
Standalone Telegram Bot Entry Point
Runs independently on VPS with SSH tunnel to cPanel MySQL
"""
import asyncio
import logging
from sshtunnel import SSHTunnelForwarder
from src.utils.config import settings
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SSH Tunnel Configuration
SSH_HOST = os.getenv('SSH_HOST')  # cPanel server IP/domain
SSH_PORT = int(os.getenv('SSH_PORT', '22'))
SSH_USER = os.getenv('SSH_USER')  # cPanel username
SSH_PASSWORD = os.getenv('SSH_PASSWORD', None)
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', None)

# MySQL Configuration (on cPanel)
REMOTE_MYSQL_HOST = os.getenv('REMOTE_MYSQL_HOST', 'localhost')
REMOTE_MYSQL_PORT = int(os.getenv('REMOTE_MYSQL_PORT', '3306'))

# Local tunnel port
LOCAL_BIND_PORT = int(os.getenv('LOCAL_BIND_PORT', '3307'))


import aiohttp.web

async def health_check(request):
    """Simple health check endpoint for UptimeRobot."""
    return aiohttp.web.Response(text="Bot is running OK")

async def start_background_web_app():
    """Starts a lightweight web server in the background."""
    app = aiohttp.web.Application()
    app.router.add_get('/', health_check)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    
    # Render provides PORT env var. Default to 10000 if not set.
    port = int(os.environ.get("PORT", 10000))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"🕸️ Web server started on port {port}")

async def start_bot_with_tunnel():
    """Start the Telegram bot with SSH tunnel to cPanel MySQL"""
    
    # 1. Start the background web server (Keep-alive mechanism)
    await start_background_web_app()
    
    # Determine SSH authentication method
    ssh_auth = {}
    if SSH_KEY_PATH and os.path.exists(SSH_KEY_PATH):
        # Ensure key has correct permissions (SSH requires 600)
        try:
            os.chmod(SSH_KEY_PATH, 0o600)
        except:
            pass
        ssh_auth['ssh_pkey'] = SSH_KEY_PATH
        logger.info(f"Using SSH key authentication: {SSH_KEY_PATH}")
    elif SSH_PASSWORD:
        ssh_auth['ssh_password'] = SSH_PASSWORD
        logger.info("Using SSH password authentication")
    else:
        raise ValueError("No SSH authentication method provided (SSH_PASSWORD or SSH_KEY_PATH)")
    
    # Create SSH tunnel
    logger.info(f"Creating SSH tunnel to {SSH_HOST}:{SSH_PORT}")
    logger.info(f"Forwarding {REMOTE_MYSQL_HOST}:{REMOTE_MYSQL_PORT} to localhost:{LOCAL_BIND_PORT}")
    
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        **ssh_auth,
        remote_bind_address=(REMOTE_MYSQL_HOST, REMOTE_MYSQL_PORT),
        local_bind_address=('127.0.0.1', LOCAL_BIND_PORT),
        set_keepalive=30  # Keep connection alive
    )
    
    try:
        # Start the tunnel
        tunnel.start()
        logger.info(f"✅ SSH tunnel established on localhost:{LOCAL_BIND_PORT}")
        
        # Update MySQL settings to use tunnel
        # We need to update the settings object directly because it was already initialized
        settings.MYSQL_HOST = '127.0.0.1'
        settings.MYSQL_PORT = LOCAL_BIND_PORT
        
        # Also update os.environ just in case new instances are created
        os.environ['MYSQL_HOST'] = '127.0.0.1'
        os.environ['MYSQL_PORT'] = str(LOCAL_BIND_PORT)
        
        # Import bot components (after tunnel is ready)
        from src.infrastructure.telegram_bot.bot import setup_bot_application
        from src.use_cases.user_use_cases import UserUseCases
        from src.use_cases.property_use_cases import PropertyUseCases
        from src.infrastructure.repository.database_factory import get_database_repository
        
        logger.info("Initializing use cases...")
        repo = get_database_repository()
        user_use_cases = UserUseCases(repo)
        property_use_cases = PropertyUseCases(repo)
        
        logger.info("Setting up Telegram bot application...")
        application = setup_bot_application(user_use_cases, property_use_cases)
        
        logger.info("Starting Telegram bot polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ Bot is running! Press Ctrl+C to stop.")
        
        # Keep the bot running
        import signal
        stop_event = asyncio.Event()
        
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            stop_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await stop_event.wait()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
    finally:
        logger.info("Stopping bot...")
        try:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
        except:
            pass
        
        logger.info("Closing SSH tunnel...")
        tunnel.stop()
        logger.info("Bot stopped")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Real Estate Telegram Bot - VPS Deployment")
    logger.info("=" * 50)
    
    # Validate configuration
    if not SSH_HOST or not SSH_USER:
        logger.error("Missing SSH configuration. Set SSH_HOST and SSH_USER in .env.bot")
        exit(1)
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN in .env.bot")
        exit(1)
    
    # Run the bot
    asyncio.run(start_bot_with_tunnel())
