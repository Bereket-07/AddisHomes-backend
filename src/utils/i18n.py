translations = {
    'en': {
        'welcome': "Welcome, {name}! Please choose your role:",
        'main_menu_prompt': "What would you like to do?",
        'browse_properties': "🔍 Browse Properties",
        'submit_property': "➕ Submit a Property",
        'my_listings': "📋 My Listings",
        'admin_panel': "👑 Admin Panel",
        'go_to_website': "Go to Website ↗️",
        'back': "⬅️ Back",
        'cancel': "❌ Cancel",
        'buyer_role': "I'm a Buyer",
        'broker_role': "I'm a Broker",
        'admin_pending_listings': "⏳ View Pending Listings",
        'admin_approve': "✅ Approve",
        'admin_reject': "❌ Reject",
        'select_property_type': "Please select a property type:",
        'property_submission_start': "Let's submit a new property. First, what type is it?",
        'how_many_bedrooms': "Great. How many bedrooms does it have?",
        'how_many_bathrooms': "How many bathrooms?",
        'what_is_size': "What is the size in square meters (e.g., 120)?",
        'what_is_price': "What is the price in ETB (e.g., 15000000)?",
        'select_region': "Please select the region:",
        'upload_images': "Please upload at least 3 images for the property. Send them one by one, and type 'done' when finished.",
        'image_received': "Image received. Send more or type 'done'.",
        'need_more_images': "Please upload at least 3 images to continue.",
        'enter_description': "Finally, please enter a short description for the property.",
        'submission_complete': "✅ Submission complete! Your property has been sent for admin approval. You will be notified of its status.",
        'new_pending_property': "🔔 New Pending Property for Approval!\n\n**Type:** {type}\n**Broker:** {broker_name}\n**Price:** {price} ETB",
        'property_approved_notification': "✅ Your property submission has been approved and is now live!",
        'property_rejected_notification': "❌ Your property submission has been rejected. Reason: {reason}",
    },
    'am': {
        # Amharic translations would go here
        'welcome': "እንኳን ደህና መጡ, {name}! እባክዎ ሚናዎን ይምረጡ:",
        'main_menu_prompt': "ምን ማድረግ ይፈልጋሉ?",
        'browse_properties': "🔍 ንብረቶችን ያስሱ",
        'submit_property': "➕ ንብረት ያስገቡ",
        'my_listings': "📋 የእኔ ዝርዝሮች",
        'admin_panel': "👑 የአስተዳዳሪ ፓነል",
    }
}

def t(key: str, lang: str = 'en', **kwargs) -> str:
    """Simple translator function."""
    return translations.get(lang, translations['en']).get(key, key).format(**kwargs)