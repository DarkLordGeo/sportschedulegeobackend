from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("sports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=280)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("country", models.CharField(blank=True, max_length=120)),
                ("city", models.CharField(blank=True, max_length=120)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("source_url", models.URLField(unique=True)),
                ("external_id", models.CharField(blank=True, max_length=150)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("upcoming", "Upcoming"),
                            ("live", "Live"),
                            ("completed", "Completed"),
                            ("cancelled", "Cancelled"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="sports.organization",
                    ),
                ),
                (
                    "sport",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="sports.sport",
                    ),
                ),
            ],
            options={
                "ordering": ["start_date", "title"],
            },
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["sport", "status"], name="events_even_sport_i_0fe643_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["organization", "status"], name="events_even_organiz_a2ef24_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["country"], name="events_even_country_586822_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["start_date"], name="events_even_start_d_d4b514_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["end_date"], name="events_even_end_dat_ef2904_idx"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["status"], name="events_even_status_5709b6_idx"),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                condition=~models.Q(external_id=""),
                fields=("organization", "external_id"),
                name="unique_event_external_id_per_organization",
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.UniqueConstraint(
                fields=("organization", "slug", "start_date"),
                name="unique_event_slug_date_per_organization",
            ),
        ),
    ]
