# --- Callback Data Constants for Telegram Bot ---
# Main Menu & General
CB_BROWSE_ALL = "browse_all"
CB_FILTER_PROPS = "filter_props"
CB_SUBMIT_PROPERTY = "submit_property"
CB_MY_LISTINGS = "my_listings"
CB_ADMIN_PANEL = "admin_panel"
CB_BACK_TO_MAIN = "back_to_main"
CB_CANCEL = "cancel"

# Prefixes for dynamic callbacks (used for inline keyboards)
CB_PREFIX_PROP_TYPE = "prop_type_"
CB_PREFIX_BEDROOMS = "bedrooms_"
CB_PREFIX_BATHROOMS = "bathrooms_"
CB_PREFIX_SIZE = "size_"
CB_PREFIX_LOCATION = "loc_"
CB_PREFIX_PRICE_RANGE = "price_"

# Admin
CB_ADMIN_PENDING_LISTINGS = "admin_pending"
CB_ADMIN_APPROVE = "admin_approve" # Note: constant uses underscore
CB_ADMIN_REJECT = "admin_reject"
CB_ADMIN_MARK_SOLD = "admin_sold"
CB_ADMIN_DELETE_CONFIRM = "admin_del_confirm"
CB_ADMIN_DELETE_EXECUTE = "admin_del_execute"
CB_ADMIN_DELETE_CANCEL = "admin_del_cancel"

# --- Reply Keyboard Special Options ---
ANY_OPTION = "Any"
ANY_PRICE = "Any Price"
ANY_REGION = "Any Region"
ANY_SCHEME = "Any Scheme"
DONE_UPLOADING_TEXT = "✅ Done Uploading" # For the button


# --- NEW: Regex for numeric button choices ---
NUMERIC_CHOICE_REGEX = r"^\d+(\+)?( .*)?$" # Matches "1", "6+", "0 (Ground)"

# --- Conversation States ---
(
    STATE_MAIN,
    # Submission states (New, streamlined flow)
    STATE_SUBMIT_PROP_TYPE, 
    STATE_SUBMIT_LOCATION_SUB_CITY,
    STATE_SUBMIT_SPECIFIC_AREA,
    STATE_SUBMIT_BEDROOMS, 
    STATE_SUBMIT_BATHROOMS,
    STATE_SUBMIT_SIZE, 
    STATE_SUBMIT_FLOOR_LEVEL, 
    STATE_SUBMIT_FURNISHING_STATUS,
    STATE_SUBMIT_TITLE_DEED,
    STATE_SUBMIT_PARKING_SPACES,
    STATE_SUBMIT_CONDO_SCHEME, # Only for Condos
    STATE_SUBMIT_PRICE, 
    STATE_SUBMIT_IMAGES, 
    STATE_SUBMIT_DESCRIPTION,
    
    # Filtering states
    STATE_FILTER_PROP_TYPE, STATE_FILTER_BEDROOMS, STATE_FILTER_LOCATION_REGION,
    STATE_FILTER_LOCATION_CITY, STATE_FILTER_PRICE_RANGE, STATE_FILTER_SHOW_RESULTS,
    STATE_FILTER_CONDO_SCHEME,

    # Admin state
    STATE_ADMIN_REJECT_REASON_INPUT
) = range(23)