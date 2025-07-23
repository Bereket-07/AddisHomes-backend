# src/infrastructure/telegram_bot/bot.py

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler
)
from src.utils.config import settings
from src.utils.i18n import t
from src.utils.constants import * # Import all constants
from src.use_cases.user_use_cases import UserUseCases
from src.use_cases.property_use_cases import PropertyUseCases
from .handlers import (
    common_handlers, admin_handlers, buyer_handlers, broker_handlers
)

def setup_bot_application(user_cases: UserUseCases, prop_cases: PropertyUseCases) -> Application:
    """Creates and aconfigures the Telegram bot application."""
    builder = Application.builder().token(settings.TELEGRAM_BOT_TOKEN)
    application = builder.build()
    application.bot_data["user_use_cases"] = user_cases
    application.bot_data["property_use_cases"] = prop_cases

    # --- CONVERSATION HANDLER DEFINITIONS ---
    # 1. Broker: Property Submission Flow
    submission_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{t('submit_property')}$"), broker_handlers.start_submission)],
        states={
            STATE_SUBMIT_PROP_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_property_type)],
            STATE_SUBMIT_LOCATION_SUB_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_sub_city)],
            STATE_SUBMIT_SPECIFIC_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_specific_area)],
            STATE_SUBMIT_BEDROOMS: [MessageHandler(filters.Regex(NUMERIC_CHOICE_REGEX), broker_handlers.receive_bedrooms)],
            STATE_SUBMIT_BATHROOMS: [MessageHandler(filters.Regex(NUMERIC_CHOICE_REGEX), broker_handlers.receive_bathrooms)],
            
            # --- THE MISSING STATES ARE NOW ADDED HERE ---
            STATE_SUBMIT_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_size)],
            STATE_SUBMIT_FLOOR_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_floor_level)],
            STATE_SUBMIT_FURNISHING_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_furnishing_status)],
            STATE_SUBMIT_TITLE_DEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_title_deed)],
            STATE_SUBMIT_PARKING_SPACES: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_parking_spaces)],
            # --- END OF ADDED STATES ---
            
            STATE_SUBMIT_CONDO_SCHEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_condo_scheme)],
            STATE_SUBMIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_price)],
            STATE_SUBMIT_IMAGES: [
                MessageHandler(filters.PHOTO, broker_handlers.receive_images),
                MessageHandler(filters.Regex(f"^{DONE_UPLOADING_TEXT}$"), broker_handlers.done_receiving_images),
            ],
            STATE_SUBMIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, broker_handlers.receive_description)],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{t('cancel')}$"), common_handlers.cancel_conversation)],
        per_message=False
    )

    # 2. Buyer: Property Filtering Flow
    filter_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{t('filter_properties')}$"), buyer_handlers.start_filtering)],
        states={
            STATE_FILTER_PROP_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_handlers.receive_filter_prop_type)],
            STATE_FILTER_BEDROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_handlers.receive_filter_bedrooms)],
            STATE_FILTER_LOCATION_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_handlers.receive_filter_region)],
            STATE_FILTER_PRICE_RANGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_handlers.receive_filter_price_range)],
            STATE_FILTER_CONDO_SCHEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_handlers.receive_filter_condo_scheme)],
        },
        fallbacks=[MessageHandler(filters.Regex(f"^{t('cancel')}$"), common_handlers.cancel_conversation)],
        per_message=False
    )

    # 3. Admin: Property Rejection Flow
    admin_rejection_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.reject_property_start, pattern=f"^{CB_ADMIN_REJECT}_")],
        states={
            STATE_ADMIN_REJECT_REASON_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.reject_property_reason)]
        },
        fallbacks=[CommandHandler("cancel", common_handlers.cancel_conversation)],
        per_message=False
    )

    # --- REGISTERING ALL HANDLERS ---
    application.add_handler(CommandHandler("start", common_handlers.start))
    application.add_handler(MessageHandler(
        filters.Regex(f"^{t('buyer_role')}|{t('broker_role')}$"),
        common_handlers.set_user_role
    ))

    # Add Conversation Handlers for multi-step processes
    application.add_handler(submission_conv)
    application.add_handler(filter_conv)
    application.add_handler(admin_rejection_conv)

    # Add MessageHandlers for top-level main menu actions
    application.add_handler(MessageHandler(filters.Regex(f"^{t('browse_properties')}$"), buyer_handlers.browse_all_properties))
    application.add_handler(MessageHandler(filters.Regex(f"^{t('my_listings')}$"), broker_handlers.my_listings))
    application.add_handler(MessageHandler(filters.Regex(f"^{t('admin_panel')}$"), admin_handlers.admin_panel))
    application.add_handler(MessageHandler(filters.Regex(f"^{t('admin_pending_listings')}$"), admin_handlers.view_pending_listings))
    application.add_handler(MessageHandler(filters.Regex(f"^{t('back_to_main_menu')}$"), common_handlers.back_to_main_menu))

    # Add the single CallbackQueryHandler for approving properties
    application.add_handler(CallbackQueryHandler(admin_handlers.approve_property, pattern=f"^{CB_ADMIN_APPROVE}_"))

    return application