# Generated by Django 3.0.2 on 2020-01-28 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0006_auto_20200128_1954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abilitytest',
            name='vacancy',
            field=models.ManyToManyField(blank=True, to='API.Vacancy'),
        ),
    ]