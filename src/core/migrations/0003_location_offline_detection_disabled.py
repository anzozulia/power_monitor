from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_location_alert_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='is_offline_detection_disabled',
            field=models.BooleanField(
                default=False,
                help_text='Disable auto power-off when heartbeat timeout exceeds grace period.',
            ),
        ),
    ]
