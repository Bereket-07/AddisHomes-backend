from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.user_models import UserRole
from .. import keyboards
from src.utils.i18n import t

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_use_cases: UserUseCases = context.bot_data["user_use_cases"]
    effective_user = update.effective_user
    
    user = await user_use_cases.get_or_create_user_by_telegram_id(
        telegram_id=effective_user.id,
        display_name=effective_user.full_name
    )
    context.user_data['user'] = user
    
    if not user.roles:
        await update.message.reply_text(
            t('welcome', name=effective_user.first_name),
            reply_markup=keyboards.get_role_selection_keyboard()
        )
    else:
        await update.message.reply_text(
            t('main_menu_prompt'),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    return ConversationHandler.END # End conversation to allow new commands

async def set_user_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data['user']
    await update.message.reply_text(
        t('main_menu_prompt'),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('submission_data', None)
    context.user_data.pop('filters', None)
    user = context.user_data['user']
    await update.message.reply_text(
        t('op_cancelled', default="Operation cancelled. Returning to the main menu."),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    return ConversationHandler.END