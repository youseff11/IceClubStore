from django import forms
from .models import Product, ProductVariant, ProductSize, SizeGuide
from .widgets import SizeChartWidget

PRODUCT_CHART_HINT = "Leave the values empty to use the category's size guide."


class SizeChartFormMixin:
    """يحوّل حقل size_chart لجدول قابل للتعديل، ويملأ عمود المقاسات بمقاسات المنتج الموجودة"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'size_chart' in self.fields:
            sizes = []
            if self.instance and self.instance.pk:
                names = ProductSize.objects.filter(variant__product=self.instance).order_by('id').values_list('size_name', flat=True)
                sizes = list(dict.fromkeys(names))
            self.fields['size_chart'].widget = SizeChartWidget(sizes=sizes, hint=PRODUCT_CHART_HINT)


class ProductForm(SizeChartFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        # أضفنا 'is_new_arrival' هنا لكي يظهر لك في صفحة manage_product.html
        fields = ['name', 'category', 'show_size_chart', 'size_guide', 'size_chart', 'size_chart_image', 'description', 'price', 'discount_price', 'is_new_arrival']

        # إضافة تنسيقات (Bootstrap) لتبدو الخانة بشكل جيد
        widgets = {
            'is_new_arrival': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_size_chart': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'size_guide': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProductAdminForm(SizeChartFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'


class SizeGuideAdminForm(forms.ModelForm):
    class Meta:
        model = SizeGuide
        fields = '__all__'
        widgets = {'chart': SizeChartWidget()}
        help_texts = {'chart': "First row = column names, then one row per size. Use + Add Size / + Add Column to extend the table."}


class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color_name', 'color_code', 'variant_image']
