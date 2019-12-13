# Generated by Django 2.2 on 2019-12-13 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0003_auto_20191116_0207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='total_money',
            field=models.DecimalField(decimal_places=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='money',
            field=models.DecimalField(decimal_places=0, max_digits=10),
        ),
    ]
