from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.forms import inlineformset_factory
from .models import Product, Category, ContactMessage, ProductVariant, Order, OrderItem, ProductSize
from .forms import ProductForm
from django import forms
from django.utils.html import strip_tags
from django.template.loader import render_to_string

# التحديث: تم حذف 'stock' من هنا لأنه انتقل لموديل ProductSize
VariantFormSet = inlineformset_factory(
    Product, 
    ProductVariant, 
    fields=['color_name', 'color_code', 'variant_image'],
    extra=3, 
    can_delete=True,
    widgets={
        'color_code': forms.TextInput(attrs={
            'type': 'color', 
            'class': 'form-control'
        }),
        'color_name': forms.TextInput(attrs={
            'placeholder': 'e.g. Black', 
            'class': 'form-control'
        }),
    }
)

def home(request):
    return render(request, 'home.html')

# --- 2. صفحة المتجر (SHOP) ---
def shop_view(request, category_slug=None):
    categories = Category.objects.all()
    products = Product.objects.all()
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    context = {
        'products': products.order_by('-created_at'),
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'shop.html', context)

# --- 3. صفحة تفاصيل المنتج (Product Detail) ---
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product_detail.html', {'product': product})

# --- 4. صفحة اتصل بنا (Contact Us) ---
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject') or "No Subject"
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name, 
            email=email, 
            phone=phone,
            subject=subject, 
            message=message
        )

        full_message = f"New message from {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"
        
        try:
            send_mail(
                subject=f"Ice Club Store: {subject}",
                message=full_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            messages.success(request, 'Sent! We received your message.')
        except Exception as e:
            messages.warning(request, 'Message saved, but email notification failed.')

        return redirect('contact')

    return render(request, 'contact.html')

# --- 5. منطق عربة التسوق المطور (تم تحديثه ليدعم المقاس) ---

@login_required(login_url='login')
def add_to_cart(request, product_id):
    user_cart_key = f"cart_{request.user.id}"
    cart = request.session.get(user_cart_key, {})
    
    selected_color = request.GET.get('color', 'Default') 
    selected_size = request.GET.get('size', 'N/A') # استقبال المقاس الجديد
    
    # جعل مفتاح العنصر يعتمد على المنتج واللون والمقاس معاً
    item_key = f"{product_id}_{selected_color}_{selected_size}"
    
    if item_key in cart:
        cart[item_key]['quantity'] += 1
    else:
        cart[item_key] = {
            'product_id': product_id,
            'quantity': 1,
            'color': selected_color,
            'size': selected_size
        }
        
    request.session[user_cart_key] = cart
    request.session.modified = True
    messages.success(request, f'Added to cart ({selected_color} - {selected_size})!')
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

@login_required(login_url='login')
def cart_view(request):
    user_cart_key = f"cart_{request.user.id}"
    cart = request.session.get(user_cart_key, {})
    cart_items = []
    total_price = 0
    
    if not isinstance(cart, dict):
        cart = {}
        request.session[user_cart_key] = cart

    for item_key, item_data in cart.items():
        if not isinstance(item_data, dict):
            continue
            
        try:
            product = Product.objects.get(id=item_data.get('product_id'))
            quantity = item_data.get('quantity', 1)
            actual_price = product.discount_price if product.discount_price else product.price
            subtotal = actual_price * quantity
            total_price += subtotal
            
            variant = ProductVariant.objects.filter(product=product, color_name=item_data.get('color')).first()
            # استخدام صورة اللون أو الصورة الافتراضية
            display_image = variant.variant_image.url if variant else product.main_image
            
            cart_items.append({
                'item_key': item_key,
                'product': product,
                'quantity': quantity,
                'color': item_data.get('color'),
                'size': item_data.get('size', 'N/A'), # عرض المقاس في السلة
                'display_image': display_image,
                'subtotal': subtotal,
                'actual_price': actual_price
            })
        except (Product.DoesNotExist, AttributeError):
            continue
        
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required(login_url='login')
def update_cart(request, item_key, action):
    user_cart_key = f"cart_{request.user.id}"
    cart = request.session.get(user_cart_key, {})
    if item_key in cart:
        if action == 'increase': cart[item_key]['quantity'] += 1
        elif action == 'decrease':
            cart[item_key]['quantity'] -= 1
            if cart[item_key]['quantity'] <= 0: del cart[item_key]
        request.session[user_cart_key] = cart
        request.session.modified = True
    return redirect('cart_view')

@login_required(login_url='login')
def remove_from_cart(request, item_key):
    user_cart_key = f"cart_{request.user.id}"
    cart = request.session.get(user_cart_key, {})
    if item_key in cart:
        del cart[item_key]
        request.session[user_cart_key] = cart
        request.session.modified = True
    return redirect('cart_view')

@login_required(login_url='login')
def checkout(request):
    user_cart_key = f"cart_{request.user.id}"
    cart = request.session.get(user_cart_key, {})
    
    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect('shop_view')

    total_price = 0
    checkout_items = []
    
    # 1. التحقق من توافر الكمية
    for item_key, item_data in cart.items():
        product = get_object_or_404(Product, id=item_data['product_id'])
        color_name = item_data.get('color')
        size_name = item_data.get('size')
        quantity_requested = item_data['quantity']
        
        variant_size = ProductSize.objects.filter(
            variant__product=product, 
            variant__color_name=color_name, 
            size_name=size_name
        ).first()
        
        if variant_size:
            if variant_size.stock < quantity_requested:
                messages.error(request, f"Sorry, only {variant_size.stock} left for {product.name} ({color_name} - {size_name}).")
                return redirect('cart_view')
        else:
            if product.stock < quantity_requested:
                messages.error(request, f"Sorry, {product.name} is out of stock.")
                return redirect('cart_view')

        price = product.discount_price if product.discount_price else product.price
        subtotal = price * quantity_requested
        total_price += subtotal

        # جلب صورة المنتج أو اللون مع تحويل الرابط لرابط كامل للإيميل
        variant = ProductVariant.objects.filter(product=product, color_name=color_name).first()
        if variant and variant.variant_image:
            img_path = variant.variant_image.url
        else:
            img_path = product.main_image.url
        
        image_url = request.build_absolute_uri(img_path)

        checkout_items.append({
            'product': product, 
            'subtotal': subtotal, 
            'data': item_data, 
            'variant_size': variant_size,
            'unit_price': price,
            'image_url': image_url
        })

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        governorate = request.POST.get('governorate')
        address = request.POST.get('address')

        order = Order.objects.create(
            name=name, email=email, phone=phone,
            governorate=governorate, address=address,
            total_price=total_price
        )

        email_items_html = ""
        for item in checkout_items:
            product = item['product']
            variant_size = item['variant_size']
            qty = item['data']['quantity']
            color = item['data']['color']
            size = item['data']['size']
            price_each = item['unit_price']
            img = item['image_url']
            sku = product.sku if product.sku else "N/A" # جلب الـ SKU

            OrderItem.objects.create(
                order=order, product=product, color=color, size=size,
                quantity=qty, price_at_purchase=price_each
            )

            # --- بناء صف الجدول مع إضافة الـ SKU ---
            email_items_html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; vertical-align: middle;">
                        <img src="{img}" width="60" style="border-radius:8px; margin-right:12px; vertical-align:middle; border:1px solid #ddd;">
                        <div style="display: inline-block; vertical-align: middle;">
                            <strong style="font-size: 15px; color: #333;">{product.name}</strong><br>
                            <span style="font-size: 12px; color: #888;">SKU: {sku}</span><br>
                            <span style="font-size: 12px; color: #555;">Color: {color} | Size: {size}</span>
                        </div>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align:center;">{qty}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #eee; text-align:right; font-weight: bold;">{int(price_each * qty)} EGP</td>
                </tr>
            """

            if variant_size:
                variant_size.stock -= qty
                variant_size.save()
            else:
                product.stock -= qty
                product.save()

        # التصميم النهائي للإيميل
        html_message = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #f0f0f0; border-radius: 15px; overflow: hidden; background-color: #ffffff;">
            <div style="background-color: #000000; color: #ffffff; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; letter-spacing: 2px;">ICE CLUB</h1>
                <p style="margin: 5px 0 0; opacity: 0.7;">Order Confirmation #{order.id}</p>
            </div>
            <div style="padding: 30px;">
                <h2 style="color: #333; margin-top: 0;">Hi {name},</h2>
                <p style="color: #666; line-height: 1.6;">Thank you for your purchase! We've received your order and we're getting it ready for shipment.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 25px;">
                    <thead>
                        <tr style="background-color: #fafafa; border-bottom: 2px solid #333;">
                            <th style="text-align: left; padding: 12px; color: #333;">Product Details</th>
                            <th style="text-align: center; padding: 12px; color: #333;">Qty</th>
                            <th style="text-align: right; padding: 12px; color: #333;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {email_items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="2" style="padding: 20px 10px; text-align: right; font-size: 16px; color: #777;">Grand Total:</td>
                            <td style="padding: 20px 0; text-align: right; font-size: 22px; font-weight: bold; color: #d63031;">{int(total_price)} EGP</td>
                        </tr>
                    </tfoot>
                </table>

                <div style="margin-top: 30px; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
                    <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #ddd; padding-bottom: 5px;">Shipping Information</h4>
                    <p style="margin: 5px 0; font-size: 14px; color: #555;"><strong>Address:</strong> {address}</p>
                    <p style="margin: 5px 0; font-size: 14px; color: #555;"><strong>City:</strong> {governorate}</p>
                    <p style="margin: 5px 0; font-size: 14px; color: #555;"><strong>Phone:</strong> {phone}</p>
                </div>
            </div>
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 11px; color: #999;">
                This is an automated message. Please do not reply directly to this email.<br>
                © 2026 Ice Club Store. All rights reserved.
            </div>
        </div>
        """

        subject = f"Ice Club - Order Confirmation #{order.id}"
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject, 
                plain_message, 
                settings.EMAIL_HOST_USER, 
                [email, settings.EMAIL_HOST_USER], 
                html_message=html_message,
                fail_silently=True
            )
        except:
            pass

        request.session[user_cart_key] = {}
        request.session.modified = True
        return render(request, 'order_success.html', {'order': order})

    return render(request, 'checkout.html', {'total_price': total_price})

# --- 7. لوحة تحكم الإدارة الكاملة ---

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin, login_url='login')
def dashboard_view(request):
    orders = Order.objects.all().order_by('-created_at')
    products = Product.objects.all().order_by('-created_at')
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    total_revenue = sum(order.total_price for order in orders if order.status == 'Delivered')
    
    context = {
        'orders': orders,
        'products': products,
        'messages': messages_list,
        'orders_count': orders.count(),
        'pending_orders': orders.filter(status='Pending').count(),
        'shipped_orders': orders.filter(status='Shipped').count(),
        'delivered_orders': orders.filter(status='Delivered').count(),
        'products_count': products.count(),
        'total_revenue': total_revenue,
    }
    return render(request, 'dashboard.html', context)

@user_passes_test(is_admin, login_url='login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = VariantFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.product = product
                instance.save()
            formset.save_m2m() 
            messages.success(request, 'Product and colors added! Go to Admin to add sizes. ✅')
            return redirect('dashboard')
    else:
        form = ProductForm()
        formset = VariantFormSet()
    
    return render(request, 'manage_product.html', {
        'form': form,
        'formset': formset,
        'title': 'Add New Product'
    })

@user_passes_test(is_admin, login_url='login')
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = VariantFormSet(request.POST, request.FILES, instance=product)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Product updated successfully! ✨')
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)
        formset = VariantFormSet(instance=product)
    
    return render(request, 'manage_product.html', {
        'form': form,
        'formset': formset,
        'title': f'Edit: {product.name}'
    })

@user_passes_test(is_admin, login_url='login')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.error(request, 'Product has been deleted! 🗑️')
    return redirect('dashboard')

# --- 8. تسجيل الدخول والاشتراك ---

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Account created! Please login.')
        return redirect('login')
    return render(request, 'signup.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# --- 9. صفحات إضافية ---

def about_view(request):
    return render(request, 'about.html')

def offers_view(request):
    offered_products = Product.objects.filter(discount_price__gt=0).order_by('-created_at')
    return render(request, 'offers.html', {'products': offered_products, 'title': 'Exclusive Offers'})

def policies(request):
    return render(request, 'policies.html')