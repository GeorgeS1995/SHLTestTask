# Generated by Django 3.0.2 on 2020-01-29 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0007_auto_20200128_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abilitytest_response',
            name='grade',
            field=models.IntegerField(null=True),
        ),
    ]
