# src/infrastructure/telegram_bot/handlers/admin_handlers.py
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.domain.models.property_models import Property , PropertyFilter 
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text
from .common_handlers import ensure_user_data, handle_exceptions
from src.domain.models.common_models import PropertyStatus
from src.utils.config import settings

logger = logging.getLogger(__name__)

def _resolve_image_url(url: str) -> str:
    if url and (url.startswith('/uploads/') or url.startswith('/images/')):
        base = settings.SERVICE_URL or 'http://localhost:8000'
        return f"{base}{url}"
    return url

@handle_exceptions
@ensure_user_data
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the dedicated admin sub-menu."""
    await update.message.reply_text(
        text="👑 Admin Panel",
        reply_markup=keyboards.get_admin_panel_keyboard(),
    )

@handle_exceptions
@ensure_user_data
async def view_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers display of pending properties using the rich card format."""
    logger.info("Admin requested to view pending listings.")
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    pending_props = await prop_cases.get_pending_properties()
    
    logger.info(f"Found {len(pending_props)} pending properties in the database.")

    if not pending_props:
        await update.message.reply_text(
            "There are no pending properties for approval.",
            reply_markup=keyboards.get_admin_panel_keyboard()
        )
        return

    await update.message.reply_text(f"Found {len(pending_props)} pending listings. Please review them below:")
    
    user_cases: UserUseCases = context.bot_data["user_use_cases"]

    for prop in pending_props:
        resolved_urls = [_resolve_image_url(url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_admin=True)
        # Append broker contact info (admin-only)
        broker_user = await user_cases.get_user_by_id(prop.broker_id) if prop.broker_id else None
        contact_lines = "\n\n**Broker Contact:**"
        # Phone preference: property-specific phone if present, else user's phone_number
        phone_val = prop.broker_phone or (getattr(broker_user, 'phone_number', None) or '')
        if phone_val:
            contact_lines += f"\n**📞 Phone:** `{phone_val}`"
        if broker_user and getattr(broker_user, 'telegram_id', None):
            contact_lines += f"\n**💬 Telegram:** [Open chat](tg://user?id={broker_user.telegram_id})"
        prop_details_with_contact = f"{prop_details_card}{contact_lines}"
        approval_keyboard = keyboards.create_admin_approval_keyboard(prop.pid)

        if not resolved_urls:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
        elif len(resolved_urls) == 1:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=resolved_urls[0]
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
        else:
            media_group = [InputMediaPhoto(media=url) for url in resolved_urls]
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
    
    await update.message.reply_text(
        "End of pending list.",
        reply_markup=keyboards.get_admin_panel_keyboard()
    )

@handle_exceptions
@ensure_user_data
async def approve_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Approve' inline button click."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]

    approved_prop = await prop_cases.approve_property(prop_id)
    broker = await user_cases.get_user_by_id(approved_prop.broker_id)
    if broker and broker.telegram_id:
        notification_text = t('property_approved_notification', default="Your property submission has been approved and is now live!")
        await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
    
    await query.edit_message_text(
        text=f"✅ **ACTION TAKEN: APPROVED**\n\nProperty `{approved_prop.pid}` has been approved.",
        parse_mode='Markdown'
    )

# --- REJECTION CONVERSATION ---
@handle_exceptions
@ensure_user_data
async def reject_property_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the rejection conversation. Asks for a reason."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]
    context.user_data['prop_to_reject'] = prop_id

    await query.edit_message_text(
        text=f"⏳ **ACTION: REJECTING**\n\nProperty `{prop_id}`. Please provide a reason in the next message.",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text="Please type the reason for rejection now:",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_ADMIN_REJECT_REASON_INPUT

@handle_exceptions
@ensure_user_data
async def reject_property_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the text reason for rejection and finalizes the process."""
    reason = update.message.text
    prop_id = context.user_data.get('prop_to_reject')
    user = context.user_data.get('user')

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    rejected_prop = await prop_cases.reject_property(prop_id, reason)

    broker = await user_cases.get_user_by_id(rejected_prop.broker_id)
    if broker and broker.telegram_id:
        notification_text = t('property_rejected_notification', reason=reason, default=f"Your property submission was rejected. Reason: {reason}")
        await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)

    await update.message.reply_text(
        f"❌ Property {rejected_prop.pid[:8]}... has been rejected.",
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    
    context.user_data.pop('prop_to_reject', None)
    return ConversationHandler.END

@handle_exceptions
@ensure_user_data
async def manage_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows all APPROVED properties to the admin for management."""
    logger.info("Admin requested to manage listings.")
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user = context.user_data['user']
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    
    # We'll find properties with the 'approved' status
    approved_props = await prop_cases.find_properties(PropertyFilter(status=PropertyStatus.APPROVED)) # We need to modify find_properties for this
    
    if not approved_props:
        await update.message.reply_text(
            "There are no approved properties to manage.",
            reply_markup=keyboards.get_admin_panel_keyboard(lang=user.language)
        )
        return

    await update.message.reply_text(f"Found {len(approved_props)} approved listings to manage:")
    
    for prop in approved_props:
        resolved_urls = [_resolve_image_url(url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_admin=True)
        # Append broker contact info (admin-only)
        broker_user = await user_cases.get_user_by_id(prop.broker_id) if prop.broker_id else None
        contact_lines = "\n\n**Broker Contact:**"
        phone_val = prop.broker_phone or (getattr(broker_user, 'phone_number', None) or '')
        if phone_val:
            contact_lines += f"\n**📞 Phone:** `{phone_val}`"
        if broker_user and getattr(broker_user, 'telegram_id', None):
            contact_lines += f"\n**💬 Telegram:** [Open chat](tg://user?id={broker_user.telegram_id})"
        prop_details_with_contact = f"{prop_details_card}{contact_lines}"
        management_keyboard = keyboards.create_admin_management_keyboard(prop.pid, lang=user.language)

        if not resolved_urls:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=management_keyboard
            )
        elif len(resolved_urls) == 1:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=resolved_urls[0]
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=management_keyboard
            )
        else:
            media_group = [InputMediaPhoto(media=url) for url in resolved_urls]
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_with_contact,
                parse_mode='Markdown',
                reply_markup=management_keyboard
            )
@handle_exceptions
@ensure_user_data
async def mark_as_sold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Mark as Sold' inline button click."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    sold_prop = await prop_cases.mark_property_as_sold(prop_id)
    
    await query.edit_message_text(
        text=f"💰 **ACTION TAKEN: SOLD**\n\nProperty `{sold_prop.pid}` has been marked as sold.",
        parse_mode='Markdown'
    )

@handle_exceptions
@ensure_user_data
async def delete_property_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the confirmation keyboard for deleting a property."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]
    user = context.user_data['user']
    
    confirmation_keyboard = keyboards.create_delete_confirmation_keyboard(prop_id, lang=user.language)
    await query.edit_message_text(
        text=f"**ARE YOU SURE?**\n\nThis will permanently delete property `{prop_id}`. This action cannot be undone.",
        parse_mode='Markdown',
        reply_markup=confirmation_keyboard
    )

@handle_exceptions
@ensure_user_data
async def delete_property_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executes the permanent deletion of a property."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    await prop_cases.delete_property(prop_id)
    
    await query.edit_message_text(
        text=f"🗑️ **ACTION TAKEN: DELETED**\n\nProperty `{prop_id}` has been permanently deleted.",
        parse_mode='Markdown'
    )
@handle_exceptions
@ensure_user_data
async def delete_property_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the delete action and restores the original message."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]
    user = context.user_data['user']

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    prop = await prop_cases.get_property_details(prop_id)
    
    prop_details_card = create_property_card_text(prop, for_admin=True)
    management_keyboard = keyboards.create_admin_management_keyboard(prop.pid, lang=user.language)

    await query.edit_message_text(
        text=prop_details_card,
        parse_mode='Markdown',
        reply_markup=management_keyboard
    )

@handle_exceptions
@ensure_user_data
async def view_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and displays the property analytics dashboard."""
    logger.info("Admin requested to view analytics.")
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user = context.user_data['user']
    
    analytics_data = await prop_cases.get_analytics_summary()
    
    # Calculate total
    total_properties = sum(analytics_data.values())

    # Format the message
    dashboard_text = (
        f"**📊 Real Estate Platform Analytics**\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"**Total Properties:** {total_properties}\n\n"
        f"**Status Breakdown:**\n"
        f"- `⏳ Pending:`   {analytics_data.get(PropertyStatus.PENDING, 0)}\n"
        f"- `✅ Approved:`  {analytics_data.get(PropertyStatus.APPROVED, 0)}\n"
        f"- `💰 Sold:`       {analytics_data.get(PropertyStatus.SOLD, 0)}\n"
        f"- `❌ Rejected:`   {analytics_data.get(PropertyStatus.REJECTED, 0)}\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖➖"
    )

    await update.message.reply_text(
        text=dashboard_text,
        parse_mode='Markdown',
        reply_markup=keyboards.get_admin_panel_keyboard(lang=user.language)
    )