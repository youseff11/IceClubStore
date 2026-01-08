from django import forms
from .models import Product, ProductVariant

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'discount_price', ]

class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color_name', 'color_code', 'variant_image']