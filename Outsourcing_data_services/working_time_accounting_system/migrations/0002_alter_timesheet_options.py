# Generated by Django 4.2.5 on 2023-10-08 10:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("working_time_accounting_system", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="timesheet",
            options={
                "ordering": ["employee"],
                "verbose_name": "Таймшит",
                "verbose_name_plural": "Таймшиты",
            },
        ),
    ]
