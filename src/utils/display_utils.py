from src.domain.models.property_models import Property, PropertyType
from src.utils.config import settings
from telegram.helpers import escape_markdown

def create_property_card_text(prop: Property, for_admin: bool = False, for_broker: bool = False) -> str:
    """
    Generates a beautifully formatted, detailed text card for a given property.
    """
    type_emojis = {
        PropertyType.APARTMENT: "🏢",
        PropertyType.CONDOMINIUM: "🏙️",
        PropertyType.VILLA: "🏡",
        PropertyType.BUILDING: "🏭",
        PropertyType.PENTHOUSE: "🌟",
        PropertyType.DUPLEX: "🏘️",
    }
    header_emoji = type_emojis.get(prop.property_type, "🏠")

    # --- Escaped Variables ---
    property_type_val = escape_markdown(prop.property_type.value)
    city = escape_markdown(prop.location.city)
    # --- UPDATED: Use the new 'site' field ---
    site = escape_markdown(prop.location.site) if prop.location.site else ""

    # --- Header Construction ---
    if for_admin:
        header = f"**{header_emoji} Property Review: {property_type_val}**"
    elif for_broker:
        header = f"**{header_emoji} Your Listing: {property_type_val}**"
    else:
        # --- UPDATED: Header for public view ---
        display_location = site if site else city
        header = f"**{header_emoji} {property_type_val} in {display_location}**"

    details_list = []
    details_list.append(f"**💰 Price:** {prop.price_etb:,.2f} ETB")

    # --- Location String Construction (UPDATED) ---
    location_str = f"{city}"
    if site:
        location_str += f" - {site}"
    details_list.append(f"**📍 Location:** {location_str}")

    details_list.append(f"**📐 Size:** {prop.size_sqm} m²")
    
    if prop.property_type != PropertyType.BUILDING:
        details_list.append(f"**🛏️ Bedrooms:** {prop.bedrooms}")
        details_list.append(f"**🛁 Bathrooms:** {prop.bathrooms}")

    if prop.floor_level is not None:
        if prop.property_type == PropertyType.VILLA:
            details_list.append(f"**🧗 Structure:** G+{prop.floor_level}")
        elif prop.property_type not in [PropertyType.BUILDING, PropertyType.DUPLEX]:
            details_list.append(f"**🧗 Floor Level:** {prop.floor_level}")

    # --- Optional Details (Unchanged) ---
    if prop.furnishing_status:
        details_list.append(f"**🛋️ Furnishing:** {escape_markdown(prop.furnishing_status.value)}")
    if prop.parking_spaces is not None:
        details_list.append(f"**🚗 Parking:** {prop.parking_spaces}")
    if prop.property_type == PropertyType.CONDOMINIUM and prop.condominium_scheme:
        details_list.append(f"** схеме:** {escape_markdown(prop.condominium_scheme.value)}") # Note: Typo in original key " схеме"

    if prop.property_type == PropertyType.BUILDING:
        if prop.is_commercial is not None:
            details_list.append(f"**Usage:** {'Commercial' if prop.is_commercial else 'Residential/Mixed'}")
        if prop.total_floors is not None:
            details_list.append(f"**Total Floors:** {prop.total_floors}")
        if prop.total_units is not None:
            details_list.append(f"**Total Units:** {prop.total_units}")
        if prop.has_elevator is not None:
            details_list.append(f"**Elevator:** {'✅ Yes' if prop.has_elevator else '❌ No'}")

    if prop.property_type == PropertyType.PENTHOUSE:
        if prop.has_private_rooftop is not None:
            details_list.append(f"**Private Rooftop:** {'✅ Yes' if prop.has_private_rooftop else '❌ No'}")
        if prop.is_two_story_penthouse is not None:
            details_list.append(f"**Two Story:** {'✅ Yes' if prop.is_two_story_penthouse else '❌ No'}")

    if prop.property_type == PropertyType.DUPLEX:
        if prop.has_private_entrance is not None:
            details_list.append(f"**Private Entrance:** {'✅ Yes' if prop.has_private_entrance else '❌ No'}")
    
    details_list.append(f"**📜 Title Deed:** {'✅ Yes' if prop.title_deed else '❌ No'}")

    # --- Description (Unchanged) ---
    escaped_description = escape_markdown(prop.description)
    description = f"\n**📝 Description:**\n_{escaped_description}_"
    
    # --- Extra Info (Unchanged) ---
    extra_info = ""
    if for_admin:
        extra_info = (f"\n\n---\n**Admin Info:**\n"
                      f"**Property ID:** `{prop.pid}`\n"
                      f"**Current Status:** {escape_markdown(prop.status.value.title())}\n"
                      f"**Broker:** {escape_markdown(prop.broker_name)} (`{prop.broker_id}`)")
    elif for_broker:
        rejection_reason = f"\n**Reason:** {escape_markdown(prop.rejection_reason)}" if prop.rejection_reason else ""
        extra_info = (f"\n\n---\n**Listing Status: {escape_markdown(prop.status.value.upper())}**"
                      f"{rejection_reason}")
    else:
        phone = settings.ADMIN_PHONE_NUMBER
        telegram = escape_markdown(settings.ADMIN_TG_USERNAME)
        extra_info = (f"\n\n---\n"
                      f"**Interested in this property? Contact the agent:**\n"
                      f"**📞 Phone:** `{phone}`\n"
                      f"**💬 Telegram:** {telegram}")

    # --- Website footer ---
    website_url = settings.WEB_APP_URL or "https://addishomess.com"
    website_footer = (f"\n\n"
                      f"🌐 For more properties and cars, visit our website: {website_url}")

    card_text = (f"{header}\n"
                 f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
                 f"{'\n'.join(details_list)}\n"
                 f"{description}"
                 f"{extra_info}"
                 f"{website_footer}")
    return card_text