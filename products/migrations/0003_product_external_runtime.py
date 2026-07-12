from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_billing_gateways'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_externally_served',
            field=models.BooleanField(
                default=False,
                help_text='If true, product UI lives on runtime_url (not this Django process).',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='runtime_url',
            field=models.URLField(
                blank=True,
                help_text='Base URL of the external product, e.g. https://app.revnext.in',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='launch_path',
            field=models.CharField(
                blank=True,
                default='/',
                help_text='Path appended after OIDC auth on the external host, e.g. /dashboard/',
                max_length=255,
            ),
        ),
    ]
