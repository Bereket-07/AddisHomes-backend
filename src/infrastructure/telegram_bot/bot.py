# src/infrastructure/telegram_bot/bot.py

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ConversationHandler
)
from src.utils.config import settings
from src.utils.i18n import t, create_i18n_regex
from src.utils.constants import * # Import all constants
from src.use_cases.user_use_cases import UserUseCases
from src.use_cases.property_use_cases import PropertyUseCases
from .handlers import (
    common_handlers, admin_handlers, buyer_handlers, broker_handlers
)

def setup_bot_application(user_cases: UserUseCases, prop_cases: PropertyUseCases) -> Application:
    """Creates and configures the Telegram bot application."""
    builder = Application.builder().token(settings.TELEGRAM_BOT_TOKEN)
    application = builder.build()
    application.bot_data["user_use_cases"] = user_cases
    application.bot_data["property_use_cases"] = prop_cases

    # --- NEW & IMPROVED: Reusable Components for Robust Conversations ---
    # 1. A filter that specifically matches the "Cancel" button in any language
    cancel_regex = create_i18n_regex('cancel')
    cancel_filter = filters.Regex(cancel_regex)

    # 2. A filter for general text input that EXCLUDES the cancel command
    text_input_filter = filters.TEXT & ~filters.COMMAND & ~cancel_filter
    
    # 3. A filter for the "stuck conversation" safety net
    stuck_filter = filters.TEXT & ~filters.COMMAND

    # 4. A standard timeout for all conversations (1800 seconds = 30 minutes)
    CONVERSATION_TIMEOUT = 1800

    # 5. A reusable list of fallback handlers for ALL conversations.
    common_fallbacks = [
        MessageHandler(cancel_filter, common_handlers.cancel_conversation),
        MessageHandler(stuck_filter, common_handlers.handle_stuck_conversation)
    ]
    # --- END of New Components ---


    # --- CONVERSATION HANDLER DEFINITIONS ---

    # 1. Broker: Property Submission Flow
    submission_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(create_i18n_regex('submit_property')), broker_handlers.start_submission)],
        states={
            # Apply the specific text_input_filter to all states that expect text
            STATE_SUBMIT_PROP_TYPE: [MessageHandler(text_input_filter, broker_handlers.receive_property_type)],
            STATE_SUBMIT_CONDO_SCHEME: [MessageHandler(text_input_filter, broker_handlers.receive_condo_scheme)],
            STATE_SUBMIT_SITE: [MessageHandler(text_input_filter, broker_handlers.receive_site)],
            STATE_SUBMIT_OTHER_SITE: [MessageHandler(text_input_filter, broker_handlers.receive_other_site)],
            STATE_SUBMIT_BEDROOMS: [MessageHandler(text_input_filter, broker_handlers.receive_bedrooms)],
            STATE_SUBMIT_BATHROOMS: [MessageHandler(text_input_filter, broker_handlers.receive_bathrooms)],
            STATE_SUBMIT_IS_COMMERCIAL: [MessageHandler(text_input_filter, broker_handlers.receive_is_commercial)],
            STATE_SUBMIT_TOTAL_FLOORS: [MessageHandler(text_input_filter, broker_handlers.receive_total_floors)],
            STATE_SUBMIT_TOTAL_UNITS: [MessageHandler(text_input_filter, broker_handlers.receive_total_units)],
            STATE_SUBMIT_HAS_ELEVATOR: [MessageHandler(text_input_filter, broker_handlers.receive_has_elevator)],
            STATE_SUBMIT_SIZE: [MessageHandler(text_input_filter, broker_handlers.receive_size)],
            STATE_SUBMIT_FLOOR_LEVEL: [MessageHandler(text_input_filter, broker_handlers.receive_floor_level)],
            STATE_SUBMIT_FURNISHING_STATUS: [MessageHandler(text_input_filter, broker_handlers.receive_furnishing_status)],
            STATE_SUBMIT_HAS_ROOFTOP: [MessageHandler(text_input_filter, broker_handlers.receive_has_rooftop)],
            STATE_SUBMIT_IS_TWO_STORY: [MessageHandler(text_input_filter, broker_handlers.receive_is_two_story)],
            STATE_SUBMIT_HAS_ENTRANCE: [MessageHandler(text_input_filter, broker_handlers.receive_has_entrance)],
            STATE_SUBMIT_TITLE_DEED: [MessageHandler(text_input_filter, broker_handlers.receive_title_deed)],
            STATE_SUBMIT_PARKING_SPACES: [MessageHandler(text_input_filter, broker_handlers.receive_parking_spaces)],
            STATE_SUBMIT_PRICE: [MessageHandler(text_input_filter, broker_handlers.receive_price)],
            STATE_SUBMIT_IMAGES: [
                MessageHandler(filters.PHOTO, broker_handlers.receive_images),
                MessageHandler(filters.Regex(f"^{DONE_UPLOADING_TEXT}$"), broker_handlers.done_receiving_images),
            ],
            STATE_SUBMIT_DESCRIPTION: [MessageHandler(text_input_filter, broker_handlers.receive_description)],
        },
        fallbacks=common_fallbacks, # Use the new common fallbacks list
        conversation_timeout=CONVERSATION_TIMEOUT,
        name="property_submission",
        per_message=False
    )

    # 2. Buyer: Property Filtering Flow
    filter_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(create_i18n_regex('filter_properties')), buyer_handlers.start_filtering)],
        states={
            # Apply the specific text_input_filter to all states
            STATE_FILTER_PROP_TYPE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_prop_type)],
            STATE_FILTER_CONDO_SCHEME: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_condo_scheme)],
            STATE_FILTER_SITE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_site)],
            STATE_FILTER_OTHER_SITE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_other_site)],
            STATE_FILTER_IS_COMMERCIAL: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_is_commercial)],
            STATE_FILTER_HAS_ELEVATOR: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_has_elevator)],
            STATE_FILTER_HAS_ROOFTOP: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_has_rooftop)],
            STATE_FILTER_IS_TWO_STORY: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_is_two_story)],
            STATE_FILTER_HAS_ENTRANCE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_has_entrance)],
            STATE_FILTER_PRICE_RANGE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_price_range)],
            STATE_FILTER_LOCATION_REGION: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_region)],
            STATE_FILTER_VILLA_STRUCTURE: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_villa_structure)],
            STATE_FILTER_BEDROOMS: [MessageHandler(text_input_filter, buyer_handlers.receive_filter_bedrooms)],
        },
        fallbacks=common_fallbacks, # Use the new common fallbacks list
        conversation_timeout=CONVERSATION_TIMEOUT,
        name="property_filtering",
        per_message=False
    )

    # 3. Admin: Property Rejection Flow
    admin_rejection_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.reject_property_start, pattern=f"^{CB_ADMIN_REJECT}_")],
        states={
            STATE_ADMIN_REJECT_REASON_INPUT: [MessageHandler(text_input_filter, admin_handlers.reject_property_reason)]
        },
        fallbacks=common_fallbacks, # Use the new common fallbacks list
        conversation_timeout=CONVERSATION_TIMEOUT,
        name="admin_rejection",
        per_message=False
    )

    # --- REGISTERING ALL HANDLERS (Preserved from your original code) ---
    application.add_handler(CommandHandler("start", common_handlers.start))
    role_regex = f"^({t('buyer_role', lang='en')}|{t('broker_role', lang='en')}|{t('buyer_role', lang='am')}|{t('broker_role', lang='am')})$"
    application.add_handler(MessageHandler(
        filters.Regex(role_regex), common_handlers.set_user_role
    ))

    application.add_handler(submission_conv)
    application.add_handler(filter_conv)
    application.add_handler(admin_rejection_conv)

    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('language_select')), common_handlers.select_language_start))
    application.add_handler(MessageHandler(filters.Regex(r'^(English 🇬🇧|አማርኛ 🇪🇹)$'), common_handlers.set_language))

    # Preserving your original emoji-based regex handlers
    application.add_handler(MessageHandler(filters.Regex(f"^🗂️ Manage Listings$"), admin_handlers.manage_listings))
    application.add_handler(MessageHandler(filters.Regex(f"^📊 View Analytics$"), admin_handlers.view_analytics))
    
    # Other top-level menu commands
    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('browse_properties')), buyer_handlers.browse_all_properties))
    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('my_listings')), broker_handlers.my_listings))
    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('admin_panel')), admin_handlers.admin_panel))
    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('admin_pending_listings')), admin_handlers.view_pending_listings))
    application.add_handler(MessageHandler(filters.Regex(create_i18n_regex('back_to_main_menu')), common_handlers.back_to_main_menu))

    # Inline Keyboard (Callback) Handlers
    application.add_handler(CallbackQueryHandler(admin_handlers.approve_property, pattern=f"^{CB_ADMIN_APPROVE}_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.mark_as_sold, pattern=f"^{CB_ADMIN_MARK_SOLD}_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.delete_property_confirm, pattern=f"^{CB_ADMIN_DELETE_CONFIRM}_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.delete_property_execute, pattern=f"^{CB_ADMIN_DELETE_EXECUTE}_"))
    application.add_handler(CallbackQueryHandler(admin_handlers.delete_property_cancel, pattern=f"^{CB_ADMIN_DELETE_CANCEL}_"))

    return application