# Generated manually for DeviceRegistration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_subscriptionplan_tenant_api_calls_reset_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceRegistration',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=512, unique=True)),
                ('platform', models.CharField(
                    choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')],
                    default='android',
                    max_length=20,
                )),
                ('device_name', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True)),
                ('tenant', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='devices',
                    to='tenants.tenant',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='devices',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'device_registrations',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='deviceregistration',
            index=models.Index(fields=['user', 'is_active'], name='device_regi_user_id_7c0a1a_idx'),
        ),
        migrations.AddIndex(
            model_name='deviceregistration',
            index=models.Index(fields=['tenant', 'is_active'], name='device_regi_tenant__b8e2c1_idx'),
        ),
    ]
