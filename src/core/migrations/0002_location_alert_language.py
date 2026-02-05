from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="alert_language",
            field=models.CharField(
                choices=[("en", "English"), ("ru", "Русский"), ("uk", "Українська")],
                default="en",
                max_length=2,
            ),
        ),
    ]
