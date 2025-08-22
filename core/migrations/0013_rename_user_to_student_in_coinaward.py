# Generated manually to fix CoinAward model field name

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_purchase_options_purchase_delivered_and_more'),
    ]

    operations = [
        # Переименовываем поле user_id в student_id в таблице core_coinaward
        migrations.RunSQL(
            sql="ALTER TABLE core_coinaward RENAME COLUMN user_id TO student_id;",
            reverse_sql="ALTER TABLE core_coinaward RENAME COLUMN student_id TO user_id;",
            state_operations=[
                # Указываем Django что поле теперь называется student
                migrations.RenameField(
                    model_name='coinaward',
                    old_name='user',
                    new_name='student',
                ),
            ]
        ),
    ]
