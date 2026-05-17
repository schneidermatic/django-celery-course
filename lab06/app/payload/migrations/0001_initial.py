from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Payload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100)),
                ('data', models.TextField()),
                ('status', models.CharField(default='pending', max_length=20)),
                ('response_body', models.TextField(blank=True, null=True)),
                ('response_status', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
