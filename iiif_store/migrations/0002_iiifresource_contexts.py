# Generated by Django 4.1.4 on 2022-12-20 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_service', '0002_context_indexable_contexts_jsonresource_contexts'),
        ('iiif_store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='iiifresource',
            name='contexts',
            field=models.ManyToManyField(to='search_service.context'),
        ),
    ]
