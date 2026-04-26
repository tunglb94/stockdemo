from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0003_trade_analyzer_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='futuresposition',
            name='bot_reasoning',
            field=models.TextField(blank=True, default=''),
        ),
    ]
