import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.domain.models.property_models import Property # <<< ADD THIS IMPORT IF MISSING
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *

# --- NEW: Import the decorator that prevents crashes after a restart ---
from .common_handlers import ensure_user_data

logger = logging.getLogger(__name__)


@ensure_user_data
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows the dedicated admin sub-menu.
    """
    await update.message.reply_text(
        text="👑 Admin Panel",
        # --- MODIFIED LINE ---
        # Use the new, dedicated admin keyboard instead of the main menu
        reply_markup=keyboards.get_admin_panel_keyboard(),
    )


@ensure_user_data
async def view_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by a text message from the admin panel keyboard."""
    logger.info("Admin requested to view pending listings.")
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    pending_props = await prop_cases.get_pending_properties()
    
    logger.info(f"Found {len(pending_props)} pending properties in the database.")

    user = context.user_data['user']
    if not pending_props:
        await update.message.reply_text(
            "There are no pending properties for approval.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return

    # --- THIS IS THE FIX ---
    # We will now loop through the properties and display each one.

    await update.message.reply_text(f"Found {len(pending_props)} pending listings. Please review them below:")
    
    for prop in pending_props:
        # 1. Create the descriptive text for the property
        prop_details = (
            f"**New Pending Property**\n\n"
            f"**ID:** `{prop.pid}`\n"
            f"**Type:** {prop.property_type.value}\n"
            f"**Location:** {prop.location.region}, {prop.location.city}\n"
            f"**Price:** {prop.price_etb:,.0f} ETB\n"
            f"**Bed/Bath:** {prop.bedrooms} / {prop.bathrooms}\n"
            f"**Size:** {prop.size_sqm} m²\n\n"
            f"**Description:**\n_{prop.description}_\n\n"
            f"**Submitted by:** {prop.broker_name} (`{prop.broker_id}`)"
        )

        # 2. Create the Approve/Reject inline keyboard
        approval_keyboard = keyboards.create_admin_approval_keyboard(prop.pid)

        # 3. Send the first image as a photo with the details and keyboard
        try:
            # We use send_photo to make it visually appealing
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=prop.image_urls[0],  # Send the first image
                caption=prop_details,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send photo for pending property {prop.pid}: {e}. Sending as text.")
            # Fallback to a text message if sending the photo fails (e.g., bad file_id)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
    
    # After showing all properties, you can send a concluding message
    await update.message.reply_text(
        "End of pending list.",
        reply_markup=keyboards.get_admin_panel_keyboard() # Keep the user in the admin panel
    )



@ensure_user_data
async def approve_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Approve' inline button click."""
    query = update.callback_query
    await query.answer()

    prop_id = query.data.split('_')[-1]

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]

    approved_prop = await prop_cases.approve_property(prop_id)
    if approved_prop:
        broker = await user_cases.get_user_by_id(approved_prop.broker_id)
        if broker and broker.telegram_id:
            notification_text = t('property_approved_notification', default="Your property submission has been approved and is now live!")
            try:
                await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
            except Exception as e:
                logger.error(f"Failed to send approval notification to broker {broker.uid}: {e}")
        
        # --- FIX: Use edit_message_caption instead of edit_message_text ---
        await query.edit_message_caption(caption=f"✅ **APPROVED**\n\nProperty {approved_prop.pid[:8]}... has been approved.")
    else:
        # If the property was already handled, the message might be text.
        # We use a try-except block for robustness.
        try:
            await query.edit_message_caption(caption="❌ This property might have been handled already.")
        except Exception:
            await query.edit_message_text("❌ This property might have been handled already.")


# --- REJECTION CONVERSATION ---

@ensure_user_data
async def reject_property_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the rejection conversation. Asks for a reason."""
    query = update.callback_query
    await query.answer()

    prop_id = query.data.split('_')[-1]
    context.user_data['prop_to_reject'] = prop_id

    # --- FIX: We can't remove the reply_markup from a caption, so we edit the caption to show it's being handled ---
    await query.edit_message_caption(caption=f"⏳ **REJECTING...**\n\nPlease provide a reason for rejecting property {prop_id[:8]}... in the next message.")
    
    # Send a new message to ask for the reason, as we can't get text input directly after an inline button.
    await query.message.reply_text(
        text="Please type the reason for rejection now:",
        reply_markup=keyboards.REMOVE_KEYBOARD # This is correct
    )

    return STATE_ADMIN_REJECT_REASON_INPUT


@ensure_user_data
async def reject_property_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the text reason for rejection and finalizes the process."""
    reason = update.message.text
    prop_id = context.user_data.get('prop_to_reject')
    user = context.user_data.get('user')

    if not prop_id:
        await update.message.reply_text(
            "Error: Property ID not found in session. Please try again from the pending list.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return ConversationHandler.END

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]

    rejected_prop = await prop_cases.reject_property(prop_id, reason)

    if rejected_prop:
        broker = await user_cases.get_user_by_id(rejected_prop.broker_id)
        if broker and broker.telegram_id:
            notification_text = t('property_rejected_notification', reason=reason, default=f"Your property submission was rejected. Reason: {reason}")
            try:
                await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
            except Exception as e:
                logger.error(f"Failed to send rejection notification to broker {broker.uid}: {e}")

        await update.message.reply_text(
            f"❌ Property {rejected_prop.pid[:8]}... has been rejected.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    else:
        await update.message.reply_text(
            "❌ Could not find or reject property. It might have been handled already.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )

    context.user_data.pop('prop_to_reject', None)
    return ConversationHandler.END