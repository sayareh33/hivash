from django.db import migrations


def create_missing_tables(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())
    models_to_check = [
        ('charity', 'ImpactStat'),
        ('charity', 'ParticipationMethod'),
        ('charity', 'ProjectGallery'),
        ('charity', 'CharityProject'),
        ('charity', 'Donation'),
        ('charity', 'ProjectUpdate'),
        ('charity', 'PaymentTransaction'),
        ('charity', 'DonationReceipt'),
    ]

    for app_label, model_name in models_to_check:
        model = apps.get_model(app_label, model_name)
        table_name = model._meta.db_table
        if table_name not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(table_name)
            for m2m in model._meta.local_many_to_many:
                existing_tables.add(m2m.m2m_db_table())


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('charity', '0003_ensure_project_status_column'),
    ]

    operations = [
        migrations.RunPython(create_missing_tables, migrations.RunPython.noop),
    ]
