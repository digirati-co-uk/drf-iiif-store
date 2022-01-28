# Generated by Django 3.1.6 on 2021-04-26 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("iiif_store", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="storediiifresource",
            name="original_id",
            field=models.URLField(unique=True, verbose_name="IIIF id"),
        ),
    ]