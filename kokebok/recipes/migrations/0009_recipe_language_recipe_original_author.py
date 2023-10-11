# Generated by Django 4.2.5 on 2023-10-10 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_alter_recipe_hero_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='language',
            field=models.CharField(blank=True, choices=[('no', 'Norwegian'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('it', 'Italian')], max_length=8),
        ),
        migrations.AddField(
            model_name='recipe',
            name='original_author',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]