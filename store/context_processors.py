def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        user_cart_key = f"cart_{request.user.id}"
    else:
        user_cart_key = "cart_guest"
        
    cart = request.session.get(user_cart_key, {})
    
    try:
        if isinstance(cart, dict):
            for item in cart.values():
                if isinstance(item, dict):
                    count += item.get('quantity', 0)
    except Exception:
        count = 0
        
    return {'cart_count': count}


def store_settings(request):
    """Provide global discount banner info to all templates."""
    try:
        from .models import StoreSettings
        settings = StoreSettings.load()
        return {
            'global_discount': settings.global_discount_percentage,
            'show_discount_banner': settings.show_discount_banner,
            'discount_banner_text': settings.banner_text,
        }
    except Exception:
        return {
            'global_discount': 0,
            'show_discount_banner': False,
            'discount_banner_text': '',
        }