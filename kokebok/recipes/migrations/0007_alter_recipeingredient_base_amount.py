# Generated by Django 4.2.5 on 2023-10-05 20:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_alter_recipeingredient_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='base_amount',
            field=models.FloatField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
    ]
