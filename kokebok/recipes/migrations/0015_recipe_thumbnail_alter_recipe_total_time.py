# Generated by Django 4.2.5 on 2023-11-01 18:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0014_alter_recipe_hero_image_alter_recipeingredient_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to='recipes/thumbnails'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='total_time',
            field=models.IntegerField(blank=True, default=None, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
