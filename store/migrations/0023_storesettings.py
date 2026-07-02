from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_alter_productimage_image_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('global_discount_percentage', models.PositiveIntegerField(default=0, verbose_name='Global Discount %')),
                ('show_discount_banner', models.BooleanField(default=False, verbose_name='Show Discount Banner')),
                ('banner_text', models.CharField(blank=True, default='', max_length=300, verbose_name='Banner Text (auto-generated or custom)')),
            ],
            options={
                'verbose_name': 'Store Settings',
                'verbose_name_plural': 'Store Settings',
            },
        ),
    ]
