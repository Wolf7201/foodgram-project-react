# Generated by Django 3.2 on 2023-10-18 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customusers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, verbose_name='Логин'),
        ),
    ]