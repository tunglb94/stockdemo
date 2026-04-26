import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0004_add_futures_bot_reasoning'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuturesTradeAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analysis_text', models.TextField()),
                ('quality_score', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('position', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='crypto.futuresposition')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
