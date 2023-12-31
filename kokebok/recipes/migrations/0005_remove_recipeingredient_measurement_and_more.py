# Generated by Django 4.2.5 on 2023-10-05 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_rename_ingress_recipe_preamble'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipeingredient',
            name='measurement',
        ),
        migrations.AddField(
            model_name='recipeingredient',
            name='unit',
            field=models.CharField(blank=True, choices=[('g', 'Gram'), ('kg', 'Kilogram'), ('oz', 'Ounce'), ('lb', 'Pound'), ('l', 'Liter'), ('dl', 'Deciliter'), ('cl', 'Centiliter'), ('ml', 'Milliliter'), ('cup', 'Cup'), ('tbsp', 'Tablespoon'), ('tsp', 'Teaspoon'), ('', 'Count'), ('slice', 'Slice'), ('cm', 'Centimetre'), ('inch', 'Inch')], max_length=16),
        ),
    ]
