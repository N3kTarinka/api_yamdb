# Generated by Django 3.2 on 2024-09-29 07:32

from django.db import migrations, models
import users.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'Пользователь с таким именем уже существует!'}, max_length=150, unique=True, validators=[users.validators.username_validator], verbose_name='Имя пользователя'),
        ),
    ]