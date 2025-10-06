# src/infrastructure/telegram_bot/handlers/common_handlers.py

from telegram import Update
from functools import wraps
import logging
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.user_models import UserRole , User
from .. import keyboards
from src.utils.i18n import t
from src.utils.exceptions import RealEstatePlatformException, TelegramApiError

logger = logging.getLogger(__name__)


def handle_exceptions(func):
    """
    A decorator that wraps handler functions to catch and handle exceptions gracefully.
    It logs the error, notifies the user, and returns them to the main menu.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            # Try to execute the actual handler function
            return await func(update, context, *args, **kwargs)
        
        except RealEstatePlatformException as e:
            # Handle our custom application exceptions
            logger.error(f"Custom exception in handler '{func.__name__}': {e}", exc_info=True)
            user_message = f"⚠️ Error: {e.message}"
            await _send_error_response(update, context, user_message)
            return ConversationHandler.END

        except TelegramError as e:
            # Handle errors from the Telegram API itself
            logger.error(f"Telegram API error in handler '{func.__name__}': {e}", exc_info=True)
            custom_error = TelegramApiError(message=f"A Telegram error occurred: {e.message}")
            await _send_error_response(update, context, custom_error.message)
            return ConversationHandler.END

        except Exception as e:
            # Handle any other unexpected exceptions
            logger.critical(f"UNHANDLED exception in handler '{func.__name__}': {e}", exc_info=True)
            user_message = "An unexpected error occurred. Our team has been notified. Please try again later."
            await _send_error_response(update, context, user_message)
            return ConversationHandler.END
            
    return wrapper

async def _send_error_response(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Helper function to send a formatted error message and return to main menu."""
    # Clear any lingering conversation data
    context.user_data.pop('submission_data', None)
    context.user_data.pop('filters', None)
    context.user_data.pop('prop_to_reject', None)
    
    user = context.user_data.get('user')
    main_menu_keyboard = keyboards.get_main_menu_keyboard(user) if user else keyboards.get_role_selection_keyboard()

    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=main_menu_keyboard
        )
        # Add website inline keyboard as a separate message to ensure visibility
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t('website_cta', default="Visit our website:"),
            reply_markup=keyboards.get_website_inline_keyboard()
        )

def ensure_user_data(func):
    """
    A decorator that ensures the user object is in context.user_data.
    If not present (e.g., after a bot restart), it fetches the user
    from the database and stores it.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if 'user' not in context.user_data:
            logger.info(f"User object not in context for handler '{func.__name__}'. Refetching from DB.")
            user_use_cases: UserUseCases = context.bot_data["user_use_cases"]
            effective_user = update.effective_user

            if not effective_user:
                logger.warning("Could not find effective_user in update. Cannot refetch user.")
                return

            user = await user_use_cases.get_or_create_user_by_telegram_id(
                telegram_id=effective_user.id,
                display_name=effective_user.full_name
            )
            if user:
                context.user_data['user'] = user
            else:
                logger.error(f"Failed to get or create user for telegram_id {effective_user.id}")
                await update.message.reply_text("An error occurred while retrieving your profile. Please try typing /start again.")
                return ConversationHandler.END

        return await func(update, context, *args, **kwargs)

    return wrapper


@handle_exceptions
@ensure_user_data
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /start command. The decorator ensures user data is loaded.
    """
    user = context.user_data['user']
    
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if not user.roles:
        if source_message:
            await source_message.reply_text(
                t('welcome', name=update.effective_user.first_name),
                reply_markup=keyboards.get_role_selection_keyboard()
            )
    else:
        if source_message:
            await source_message.reply_text(
                t('main_menu_prompt'),
                reply_markup=keyboards.get_main_menu_keyboard(user)
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t('website_cta', default="Visit our website:"),
            reply_markup=keyboards.get_website_inline_keyboard()
        )
    return ConversationHandler.END


@handle_exceptions
@ensure_user_data
async def set_user_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the role selection from the first-time menu."""
    role_text = update.message.text
    role = UserRole.BUYER if role_text == t('buyer_role') else UserRole.BROKER
    
    user = context.user_data['user']
    user_use_cases: UserUseCases = context.bot_data["user_use_cases"]
    
    updated_user = await user_use_cases.add_user_role(user.uid, role)
    context.user_data['user'] = updated_user
    
    await update.message.reply_text(
        f"You are now registered as a {role.value}!",
        reply_markup=keyboards.get_main_menu_keyboard(updated_user)
    )


@handle_exceptions
@ensure_user_data
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Back to Main Menu' button click, safely."""
    user = context.user_data['user']
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message:
        await source_message.reply_text(
            t('main_menu_prompt'),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('website_cta', default="Visit our website:"),
        reply_markup=keyboards.get_website_inline_keyboard()
    )
    return ConversationHandler.END


@handle_exceptions
@ensure_user_data
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels any ongoing conversation, safely."""
    context.user_data.pop('submission_data', None)
    context.user_data.pop('filters', None)
    context.user_data.pop('prop_to_reject', None)

    user = context.user_data['user']
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message:
        await source_message.reply_text(
            t('op_cancelled', default="Operation cancelled. Returning to the main menu."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('website_cta', default="Visit our website:"),
        reply_markup=keyboards.get_website_inline_keyboard()
    )
    return ConversationHandler.END


@handle_exceptions
@ensure_user_data
async def select_language_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the language selection menu."""
    user = context.user_data['user']
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message:
        await source_message.reply_text(
            text=t('select_language_prompt', lang=user.language),
            reply_markup=keyboards.get_language_selection_keyboard()
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('website_cta', default="Visit our website:"),
        reply_markup=keyboards.get_website_inline_keyboard()
    )
@handle_exceptions
@ensure_user_data
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets the user's language and returns to the main menu."""
    user = context.user_data['user']
    user_use_cases: UserUseCases = context.bot_data["user_use_cases"]

    chosen_lang = update.message.text
    lang_code = 'am' if 'አማርኛ' in chosen_lang else 'en'
    
    updated_user = await user_use_cases.set_user_language(user.uid, lang_code)
    context.user_data['user'] = updated_user # IMPORTANT: Update context
    
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message:
        await source_message.reply_text(
            text=t('language_updated', lang=lang_code, lang_name=chosen_lang),
            reply_markup=keyboards.get_main_menu_keyboard(updated_user)
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t('website_cta', default="Visit our website:"),
        reply_markup=keyboards.get_website_inline_keyboard()
    )

@handle_exceptions
@ensure_user_data
async def handle_stuck_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    A catch-all fallback handler.
    If the user is in a conversation and sends a message that doesn't match any
    state or the cancel button, this function will catch it, end the conversation,
    and return them to the main menu.
    """
    user_id = update.effective_user.id
    user_message = update.message.text
    logger.warning(f"User {user_id} sent an unexpected message ('{user_message}') in a conversation. Resetting flow.")

    # Clean up any lingering data to ensure a fresh start.
    context.user_data.pop('submission_data', None)
    context.user_data.pop('filters', None)
    context.user_data.pop('prop_to_reject', None)

    user = context.user_data['user']
    
    # Send a helpful message explaining what happened.
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message:
        await source_message.reply_text(
            text=t('stuck_conversation_message', lang=user.language, default="It looks like that action is no longer valid. Let's go back to the main menu to start fresh."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    
    # Officially end the conversation.
    return ConversationHandler.END