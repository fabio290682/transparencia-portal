import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_projeto"),
    ]

    operations = [
        migrations.AddField(
            model_name="projeto",
            name="arquivo",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="projeto_documentos/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "xls", "xlsx"],
                    ),
                ],
            ),
        ),
    ]
