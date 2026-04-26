from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0002_futures'),
    ]

    operations = [
        # 3 fields mới trên CryptoOrder
        migrations.AddField(
            model_name='cryptoorder',
            name='bot_reasoning',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='cryptoorder',
            name='cost_basis_usd',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='cryptoorder',
            name='pnl_usd',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True),
        ),
        # 3 model mới
        migrations.CreateModel(
            name='BotRoundLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bot_username', models.CharField(max_length=50)),
                ('analysis_text', models.TextField(blank=True, default='')),
                ('decisions_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='LearnedLesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_bot', models.CharField(max_length=50)),
                ('lesson_text', models.TextField()),
                ('polarity', models.CharField(choices=[('GOOD', 'Good'), ('WARNING', 'Warning')], default='GOOD', max_length=10)),
                ('tags', models.CharField(blank=True, default='universal', max_length=200)),
                ('quality_score', models.FloatField(default=0.5)),
                ('pnl_at_extraction', models.FloatField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lessons', to='crypto.cryptoorder')),
            ],
            options={'ordering': ['-quality_score', '-created_at']},
        ),
        migrations.CreateModel(
            name='TradeAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analysis_text', models.TextField()),
                ('quality_score', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='crypto.cryptoorder')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
