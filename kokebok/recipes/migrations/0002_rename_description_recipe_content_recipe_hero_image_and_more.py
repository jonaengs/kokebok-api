# Generated by Django 4.2.5 on 2023-10-03 19:06

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recipe',
            old_name='description',
            new_name='content',
        ),
        migrations.AddField(
            model_name='recipe',
            name='hero_image',
            field=models.ImageField(blank=True, upload_to='recipes/banners'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingress',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='other_source',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='recipe',
            name='servings',
            field=models.IntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipe',
            name='total_time',
            field=models.IntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipe',
            name='video_url',
            field=models.URLField(blank=True),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='base_ingredient',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='recipe_ingredients', to='recipes.ingredient'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='name_in_recipe',
            field=models.CharField(max_length=128),
        ),
    ]
