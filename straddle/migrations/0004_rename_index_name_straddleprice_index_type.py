# Generated by Django 5.1.5 on 2025-02-07 08:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('straddle', '0003_alter_straddleprice_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='straddleprice',
            old_name='index_name',
            new_name='index_type',
        ),
    ]
