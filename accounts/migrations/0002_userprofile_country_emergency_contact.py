from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, null=True, verbose_name='Country'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='emergency_contact',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Emergency contact'),
        ),
    ]
