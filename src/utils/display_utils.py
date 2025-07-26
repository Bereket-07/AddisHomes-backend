# src/infrastructure/telegram_bot/display_utils.py

from src.domain.models.property_models import Property, PropertyType, PropertyStatus
from src.utils.config import settings

def create_property_card_text(prop: Property, for_admin: bool = False, for_broker: bool = False) -> str:
    """
    Generates a beautifully formatted, detailed text card for a given property.
    """
    
    # Emoji mapping for property types
    type_emojis = {
        PropertyType.APARTMENT: "🏢",
        PropertyType.CONDOMINIUM: "🏙️",
        PropertyType.VILLA: "🏡",
    }
    header_emoji = type_emojis.get(prop.property_type, "🏠")

    # --- Card Header ---
    if for_admin:
        header = f"**{header_emoji} Property Review: {prop.property_type.value}**"
    elif for_broker:
        header = f"**{header_emoji} Your Listing: {prop.property_type.value}**"
    else:
        header = f"**{header_emoji} {prop.property_type.value} in {prop.location.city}**"

    # --- Build details list, omitting empty fields ---
    details_list = []
    details_list.append(f"**💰 Price:** {prop.price_etb:,.2f} ETB")
    
    location_str = f"{prop.location.region} - {prop.location.city}"
    if prop.location.sub_city:
        location_str += f" - {prop.location.sub_city}"
    details_list.append(f"**📍 Location:** {location_str}")
    
    details_list.append(f"**📐 Size:** {prop.size_sqm} m²")
    details_list.append(f"**🛏️ Bedrooms:** {prop.bedrooms}")
    details_list.append(f"**🛁 Bathrooms:** {prop.bathrooms}")

    if prop.floor_level is not None:
        if prop.property_type == PropertyType.VILLA:
            # Display as G+ for villas
            details_list.append(f"**🧗 Structure:** G+{prop.floor_level}")
        else:
            # Display as Floor Level for others
            details_list.append(f"**🧗 Floor Level:** {prop.floor_level}")
    if prop.furnishing_status:
        details_list.append(f"**🛋️ Furnishing:** {prop.furnishing_status.value}")
    if prop.parking_spaces is not None:
        details_list.append(f"**🚗 Parking:** {prop.parking_spaces}")

    # Conditional display for Condo Scheme
    if prop.property_type == PropertyType.CONDOMINIUM and prop.condominium_scheme:
        details_list.append(f"** схеме:** {prop.condominium_scheme.value}")

    details_list.append(f"**📜 Title Deed:** {'✅ Yes' if prop.title_deed else '❌ No'}")
    
    # --- Description ---
    description = f"\n**📝 Description:**\n_{prop.description}_"

    # --- Conditional Sections ---
    extra_info = ""
    if for_admin:
        extra_info = (
            f"\n\n---\n**Admin Info:**\n"
            f"**Property ID:** `{prop.pid}`\n"
            f"**Current Status:** {prop.status.value.title()}\n"
            f"**Broker:** {prop.broker_name} (`{prop.broker_id}`)"
        )
    elif for_broker:
        rejection_reason = f"\n**Reason:** {prop.rejection_reason}" if prop.rejection_reason else ""
        extra_info = (
            f"\n\n---\n**Listing Status: {prop.status.value.upper()}**"
            f"{rejection_reason}"
        )
    else: # For Buyer
        phone = settings.ADMIN_PHONE_NUMBER
        telegram = settings.ADMIN_TG_USERNAME
        
        extra_info = (
            f"\n\n---\n"
            f"**Interested in this property? Contact the agent:**\n"
            f"**📞 Phone:** `{phone}`\n"
            f"**💬 Telegram:** {telegram}"
        )

    # --- Assemble the Final Card ---
    card_text = (
        f"{header}\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"{'\n'.join(details_list)}"  # Join the list of details
        f"{description}"
        f"{extra_info}"
    )

    return card_text