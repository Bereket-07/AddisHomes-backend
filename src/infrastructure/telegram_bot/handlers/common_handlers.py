from telegram import Update
from functools import wraps
import logging
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.user_models import UserRole
from .. import keyboards
from src.utils.i18n import t

logger = logging.getLogger(__name__)


def ensure_user_data(func):
    """
    A decorator that ensures the user object is in context.user_data.
    If not present (e.g., after a bot restart), it fetches the user
    from the database and stores it.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # We need to check for the user in the context before every decorated function
        if 'user' not in context.user_data:
            logger.info(f"User object not in context for handler '{func.__name__}'. Refetching from DB.")
            user_use_cases: UserUseCases = context.bot_data["user_use_cases"]
            effective_user = update.effective_user

            if not effective_user:
                logger.warning("Could not find effective_user in update. Cannot refetch user.")
                # Decide how to handle this case, e.g., by ending the conversation or sending an error message.
                # For now, we'll just return, as no further action can be taken without a user.
                return

            user = await user_use_cases.get_or_create_user_by_telegram_id(
                telegram_id=effective_user.id,
                display_name=effective_user.full_name
            )
            # If a user is found or created, add it to the context
            if user:
                context.user_data['user'] = user
            else:
                # This case is unlikely but good to handle
                logger.error(f"Failed to get or create user for telegram_id {effective_user.id}")
                await update.message.reply_text("An error occurred while retrieving your profile. Please try typing /start again.")
                return ConversationHandler.END

        # Now that we're sure the user exists in context, run the original function
        return await func(update, context, *args, **kwargs)

    return wrapper


@ensure_user_data
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /start command. The decorator ensures user data is loaded,
    though this function also has its own loading logic as the primary entry point.
    """
    user = context.user_data['user']
    
    if not user.roles:
        await update.message.reply_text(
            t('welcome', name=update.effective_user.first_name),
            reply_markup=keyboards.get_role_selection_keyboard()
        )
    else:
        await update.message.reply_text(
            t('main_menu_prompt'),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    return ConversationHandler.END # End conversation to allow new commands


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


@ensure_user_data
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Back to Main Menu' button click, safely."""
    user = context.user_data['user']
    await update.message.reply_text(
        t('main_menu_prompt'),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    return ConversationHandler.END


@ensure_user_data
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels any ongoing conversation, safely."""
    # Clear any temporary data from conversations
    context.user_data.pop('submission_data', None)
    context.user_data.pop('filters', None)
    context.user_data.pop('prop_to_reject', None) # Also clear this for safety

    user = context.user_data['user']
    await update.message.reply_text(
        t('op_cancelled', default="Operation cancelled. Returning to the main menu."),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    return ConversationHandler.END