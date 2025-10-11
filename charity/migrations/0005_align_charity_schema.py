from django.db import migrations


def ensure_charityproject_columns(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'charity_charityproject'

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
        existing_columns = {column.name for column in description}

        if 'impact_summary' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN impact_summary VARCHAR(255) NOT NULL DEFAULT ''"
            )
        if 'location' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN location VARCHAR(150) NOT NULL DEFAULT ''"
            )
        if 'beneficiaries_count' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN beneficiaries_count INT UNSIGNED NULL"
            )
        if 'hero_video_url' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN hero_video_url VARCHAR(200) NOT NULL DEFAULT ''"
            )
        if 'completion_date' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_charityproject "
                "ADD COLUMN completion_date DATE NULL"
            )


def ensure_donation_columns(apps, schema_editor):
    connection = schema_editor.connection
    table_name = 'charity_donation'

    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
        existing_columns = {column.name for column in description}

        if 'donor_name' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_donation "
                "ADD COLUMN donor_name VARCHAR(150) NOT NULL DEFAULT ''"
            )
        if 'donor_email' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_donation "
                "ADD COLUMN donor_email VARCHAR(254) NOT NULL DEFAULT ''"
            )
        if 'donor_phone' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_donation "
                "ADD COLUMN donor_phone VARCHAR(20) NOT NULL DEFAULT ''"
            )
        if 'created_at' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_donation "
                "ADD COLUMN created_at DATETIME(6) NULL"
            )
            cursor.execute(
                "UPDATE charity_donation SET created_at = UTC_TIMESTAMP() "
                "WHERE created_at IS NULL"
            )
            cursor.execute(
                "ALTER TABLE charity_donation "
                "MODIFY COLUMN created_at DATETIME(6) NOT NULL"
            )
        if 'updated_at' not in existing_columns:
            cursor.execute(
                "ALTER TABLE charity_donation "
                "ADD COLUMN updated_at DATETIME(6) NULL"
            )
            cursor.execute(
                "UPDATE charity_donation SET updated_at = UTC_TIMESTAMP() "
                "WHERE updated_at IS NULL"
            )
            cursor.execute(
                "ALTER TABLE charity_donation "
                "MODIFY COLUMN updated_at DATETIME(6) NOT NULL"
            )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('charity', '0004_create_missing_tables'),
    ]

    operations = [
        migrations.RunPython(ensure_charityproject_columns, migrations.RunPython.noop),
        migrations.RunPython(ensure_donation_columns, migrations.RunPython.noop),
    ]
