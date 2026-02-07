from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_location_offline_detection_disabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='is_router_reconnect_window_enabled',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Enable a router reconnect window after power-on '
                    '(5 minutes window + 3 minutes extra grace).'
                ),
            ),
        ),
    ]
