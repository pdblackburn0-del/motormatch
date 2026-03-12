import re
from django.db import migrations, models


def clean_vehicle_numeric_fields(apps, schema_editor):
    Vehicle = apps.get_model('motormatch', 'Vehicle')
    for v in Vehicle.objects.all():
        # Clean price: "£7,500" → "7500"
        if v.price:
            cleaned = re.sub(r'[^\d\.]', '', str(v.price))
            try:
                v.price = str(round(float(cleaned))) if cleaned else '0'
            except (ValueError, TypeError):
                v.price = '0'
        else:
            v.price = '0'

        # Clean mileage: "32,000 miles" → "32000", "32k mi" → "32000"
        if v.mileage:
            s = str(v.mileage).lower().strip()
            # expand "k" notation: "32k" → "32000"
            s = re.sub(r'(\d+)\s*k\b', lambda m: str(int(m.group(1)) * 1000), s)
            cleaned = re.sub(r'[^0-9]', '', s)
            v.mileage = cleaned if cleaned else '0'
        else:
            v.mileage = '0'

        # Clean year: keep 4-digit integers only
        if v.year:
            cleaned = re.sub(r'[^0-9]', '', str(v.year))[:4]
            try:
                yr = int(cleaned)
                v.year = str(yr) if 1900 <= yr <= 2100 else None
            except (ValueError, TypeError):
                v.year = None
        else:
            v.year = None

        v.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('motormatch', '0021_add_flaggedmessage_proxy'),
    ]

    operations = [
        migrations.RunPython(clean_vehicle_numeric_fields, noop),
        migrations.AlterField(
            model_name='vehicle',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='mileage',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='year',
            field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True),
        ),
    ]
