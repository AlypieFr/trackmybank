# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-16 14:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20180916_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='month',
            name='salary',
            field=models.FloatField(default=0, verbose_name='salary'),
            preserve_default=False,
        ),
    ]