# Generated by Django 5.1.5 on 2025-02-06 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('straddle', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='straddleprice',
            name='index_name',
            field=models.CharField(default='NIFTY', max_length=50),
        ),
    ]
