from django.db import migrations


def ensure_status_column(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'charity_charityproject'

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
        column_names = {column.name for column in description}

        if 'status' not in column_names:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('charity', '0002_alter_donation_donor_name'),
    ]

    operations = [
        migrations.RunPython(ensure_status_column, migrations.RunPython.noop),
    ]

