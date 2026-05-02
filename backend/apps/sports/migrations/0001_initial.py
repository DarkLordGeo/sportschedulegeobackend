from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Sport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220)),
                ("website_url", models.URLField(blank=True)),
                (
                    "sport",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizations",
                        to="sports.sport",
                    ),
                ),
            ],
            options={
                "ordering": ["sport__name", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="sport",
            index=models.Index(fields=["slug"], name="sports_spor_slug_ca78a5_idx"),
        ),
        migrations.AddIndex(
            model_name="organization",
            index=models.Index(fields=["sport", "slug"], name="sports_orga_sport_i_459a4e_idx"),
        ),
        migrations.AddConstraint(
            model_name="organization",
            constraint=models.UniqueConstraint(
                fields=("sport", "slug"),
                name="unique_organization_slug_per_sport",
            ),
        ),
    ]
