# Generated by Django 5.2.3 on 2025-07-23 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Grocery_api', '0004_remove_item_quantity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='quantity',
        ),
        migrations.AddField(
            model_name='item',
            name='unit_value',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
        ),
    ]
