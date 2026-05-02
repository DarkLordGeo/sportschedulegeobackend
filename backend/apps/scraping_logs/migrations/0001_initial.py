from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ScrapeRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_name", models.CharField(max_length=150)),
                ("started_at", models.DateTimeField()),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("partial", "Partial"),
                        ],
                        default="running",
                        max_length=20,
                    ),
                ),
                ("total_found", models.PositiveIntegerField(default=0)),
                ("total_created", models.PositiveIntegerField(default=0)),
                ("total_updated", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="scraperun",
            index=models.Index(fields=["source_name", "status"], name="scraping_lo_source__caa79f_idx"),
        ),
        migrations.AddIndex(
            model_name="scraperun",
            index=models.Index(fields=["started_at"], name="scraping_lo_started_ebc5a8_idx"),
        ),
    ]
