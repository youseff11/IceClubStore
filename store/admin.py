from django.contrib import admin
from django.utils.html import format_html
import nested_admin
from .models import Product, Category, ContactMessage, ProductVariant, ProductSize, Order, OrderItem

# --- 1. ProductSizeInline ---
class ProductSizeInline(nested_admin.NestedTabularInline):
    model = ProductSize
    extra = 1
    fields = ['size_name', 'stock']

# --- 2. ProductVariantInline ---
class ProductVariantInline(nested_admin.NestedStackedInline):
    model = ProductVariant
    extra = 1
    fields = ['color_name', 'color_code', 'variant_image', 'image_preview']
    readonly_fields = ['image_preview']
    inlines = [ProductSizeInline]

    def image_preview(self, obj):
        if obj.variant_image:
            return format_html('<img src="{}" style="width: 100px; height: auto; border-radius: 5px; border: 1px solid #ddd;" />', obj.variant_image.url)
        return "No Image"
    image_preview.short_description = 'Preview'

# --- 3. ProductAdmin ---
@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    inlines = [ProductVariantInline]
    
    # تحسين عرض الجدول الرئيسي
    list_display = ['sku', 'name', 'category', 'colored_stock', 'display_price', 'display_discount', 'created_at']
    list_display_links = ['name'] 
    list_editable = ['sku', 'category'] 
    list_filter = ['category', 'created_at']
    search_fields = ['sku', 'name', 'description']

    # تنظيم الحقول داخل صفحة المنتج
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'category', 'description'),
            'classes': ('wide',),
        }),
        ('Pricing & Inventory', {
            'fields': (('price', 'discount_price'), 'stock'),
        }),
    )
    readonly_fields = ['stock'] # جعل الإجمالي للقراءة فقط لأنه يُحسب تلقائياً

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.update_total_stock()

    # تحسين بصري للمخزون (لون أحمر إذا نفد)
    def colored_stock(self, obj):
        color = 'green' if obj.stock > 10 else 'orange' if obj.stock > 0 else 'red'
        return format_html('<b style="color: {};">{}</b>', color, obj.stock)
    colored_stock.short_description = 'Stock Status'

    def display_price(self, obj):
        return format_html('<b>{}</b> <small>EGP</small>', int(obj.price)) if obj.price else 0
    display_price.short_description = 'Price'

    def display_discount(self, obj):
        return int(obj.discount_price) if obj.discount_price else "-"
    display_discount.short_description = 'Discount'

# --- 4. CategoryAdmin ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

# --- 5. ContactMessageAdmin ---
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'email', 'created_at']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']

# --- 6. OrderItemInline & OrderAdmin ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'color', 'size', 'quantity', 'display_item_price']
    can_delete = False

    def display_item_price(self, obj):
        return int(obj.price_at_purchase)
    display_item_price.short_description = 'Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'governorate', 'display_total', 'status', 'is_completed', 'created_at']
    list_filter = ['status', 'is_completed', 'governorate', 'created_at']
    search_fields = ['name', 'phone', 'email', 'id']
    list_editable = ['status', 'is_completed'] 
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Customer Info', {'fields': (('name', 'email'), 'phone', 'governorate', 'address')}),
        ('Status & Total', {'fields': (('status', 'is_completed'), 'total_price')}),
    )
    readonly_fields = ['total_price']

    def display_total(self, obj):
        return int(obj.total_price)
    display_total.short_description = 'Total Price'

# admin.site.register(ProductVariant)
# admin.site.register(ProductSize)