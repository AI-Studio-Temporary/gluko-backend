from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=100)),
                ('last_name', models.CharField(blank=True, max_length=100)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], max_length=20)),
                ('weight_kg', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('height_cm', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('diabetes_type', models.CharField(blank=True, choices=[('type1', 'Type 1'), ('type2', 'Type 2'), ('gestational', 'Gestational'), ('lada', 'LADA (Type 1.5)'), ('mody', 'MODY'), ('prediabetes', 'Prediabetes'), ('other', 'Other')], max_length=20)),
                ('diagnosis_year', models.PositiveIntegerField(blank=True, null=True)),
                ('on_insulin', models.BooleanField(default=False)),
                ('insulin_regimen', models.CharField(blank=True, choices=[('mdi', 'Multiple Daily Injections (MDI)'), ('pump', 'Insulin Pump (CSII)'), ('basal_only', 'Basal Only'), ('premixed', 'Premixed Insulin'), ('none', 'Not on Insulin')], max_length=20)),
                ('insulin_type', models.CharField(blank=True, help_text='e.g. Novorapid + Lantus', max_length=200)),
                ('insulin_to_carb_ratio', models.DecimalField(blank=True, decimal_places=2, help_text='Grams of carbs covered by 1 unit of insulin', max_digits=5, null=True)),
                ('insulin_sensitivity_factor', models.DecimalField(blank=True, decimal_places=2, help_text='mmol/L drop per 1 unit of correction insulin', max_digits=4, null=True)),
                ('target_bg_min', models.DecimalField(blank=True, decimal_places=1, help_text='mmol/L', max_digits=4, null=True)),
                ('target_bg_max', models.DecimalField(blank=True, decimal_places=1, help_text='mmol/L', max_digits=4, null=True)),
                ('last_hba1c', models.DecimalField(blank=True, decimal_places=1, help_text='%', max_digits=4, null=True)),
                ('monitoring_method', models.CharField(blank=True, choices=[('cgm', 'Continuous Glucose Monitor (CGM)'), ('finger_prick', 'Finger Prick'), ('both', 'Both CGM & Finger Prick'), ('none', 'None currently')], max_length=20)),
                ('cgm_device', models.CharField(blank=True, help_text='e.g. Dexcom G7, Libre 3', max_length=100)),
                ('other_medications', models.TextField(blank=True, help_text='List any other medications you take')),
                ('other_conditions', models.TextField(blank=True, help_text='e.g. hypertension, coeliac disease')),
                ('dietary_restrictions', models.TextField(blank=True, help_text='e.g. vegetarian, gluten-free, low-carb')),
                ('activity_level', models.CharField(blank=True, choices=[('sedentary', 'Sedentary (little or no exercise)'), ('light', 'Light (1–3 days/week)'), ('moderate', 'Moderate (3–5 days/week)'), ('active', 'Active (6–7 days/week)'), ('very_active', 'Very Active (twice/day or physical job)')], max_length=20)),
                ('management_goals', models.TextField(blank=True, help_text='What are your main diabetes management goals?')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
