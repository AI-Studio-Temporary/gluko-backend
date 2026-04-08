"""Seed realistic health log data for a user.

Usage:
    python manage.py seed_logs                                         # uses default email
    python manage.py seed_logs --email fernando.salinasgana@student.uts.edu.au
    python manage.py seed_logs --days 7                                # seed 7 days of data
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from logs.models import GlucoseLog, InsulinLog, MealLog, SportLog
from users.models import UserProfile

DEFAULT_EMAIL = 'fernando.salinasgana@student.uts.edu.au'

MEALS = [
    ('Oatmeal with banana and honey', 'breakfast', 58),
    ('Scrambled eggs on toast with avocado', 'breakfast', 32),
    ('Greek yoghurt with granola and berries', 'breakfast', 45),
    ('Vegemite toast with butter', 'breakfast', 28),
    ('Chicken Caesar salad', 'lunch', 22),
    ('Tuna sandwich on wholemeal bread', 'lunch', 38),
    ('Beef burrito bowl with rice and beans', 'lunch', 65),
    ('Pumpkin soup with sourdough', 'lunch', 48),
    ('Pad Thai with prawns', 'dinner', 72),
    ('Grilled salmon with sweet potato and broccoli', 'dinner', 35),
    ('Spaghetti bolognese', 'dinner', 68),
    ('Chicken stir-fry with jasmine rice', 'dinner', 55),
    ('Fish and chips', 'dinner', 80),
    ('Apple and peanut butter', 'snack', 25),
    ('Protein bar', 'snack', 22),
    ('Handful of almonds', 'snack', 6),
    ('Banana', 'snack', 27),
    ('Tim Tam biscuits (2)', 'snack', 18),
]

ACTIVITIES = [
    ('Running', 30, 'high'),
    ('Walking', 45, 'low'),
    ('Cycling', 40, 'moderate'),
    ('Swimming', 30, 'high'),
    ('Yoga', 60, 'low'),
    ('Weight training', 45, 'moderate'),
    ('Basketball', 60, 'high'),
    ('Hiking', 90, 'moderate'),
]

CONTEXTS = ['fasting', 'before_meal', 'after_meal', 'bedtime', 'other']
INSULIN_BRANDS = ['Novorapid', 'Humalog', 'Fiasp']


class Command(BaseCommand):
    help = 'Seed realistic health log data for a user'

    def add_arguments(self, parser):
        parser.add_argument('--email', default=DEFAULT_EMAIL, help='User email')
        parser.add_argument('--days', type=int, default=7, help='Number of days to seed')
        parser.add_argument('--clear', action='store_true', help='Clear existing logs before seeding')

    def handle(self, *args, **options):
        email = options['email']
        days = options['days']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(f'User with email {email} not found.')
            return

        if options['clear']:
            GlucoseLog.objects.filter(user=user).delete()
            InsulinLog.objects.filter(user=user).delete()
            MealLog.objects.filter(user=user).delete()
            SportLog.objects.filter(user=user).delete()
            self.stdout.write('Cleared existing logs.')

        # Ensure profile has ICR/ISF for bolus calculator
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.insulin_to_carb_ratio:
            profile.diabetes_type = 'type1'
            profile.on_insulin = True
            profile.insulin_to_carb_ratio = Decimal('10')
            profile.insulin_sensitivity_factor = Decimal('2.5')
            profile.target_bg_min = Decimal('4.0')
            profile.target_bg_max = Decimal('10.0')
            profile.insulin_regimen = 'mdi'
            profile.insulin_type = 'Novorapid + Lantus'
            profile.monitoring_method = 'cgm'
            profile.first_name = 'Fernando'
            profile.save()
            self.stdout.write('Updated profile with diabetes settings.')

        now = timezone.now()
        glucose_count = 0
        insulin_count = 0
        meal_count = 0
        sport_count = 0

        for day_offset in range(days):
            day = now - timedelta(days=day_offset)
            base = day.replace(hour=0, minute=0, second=0, microsecond=0)

            # Fasting glucose (6-7am)
            GlucoseLog.objects.create(
                user=user, value_mgdl=random.randint(80, 120),
                measurement_context='fasting',
                logged_at=base + timedelta(hours=6, minutes=random.randint(0, 59)),
            )
            glucose_count += 1

            # Basal insulin (7am)
            InsulinLog.objects.create(
                user=user, units=Decimal(str(random.randint(18, 24))),
                insulin_type='basal', insulin_brand='Lantus',
                logged_at=base + timedelta(hours=7, minutes=random.randint(0, 30)),
            )
            insulin_count += 1

            # 3 meals with before/after glucose + bolus insulin
            meal_times = [
                (8, 'breakfast'),
                (12, 'lunch'),
                (19, 'dinner'),
            ]
            for hour, meal_type_filter in meal_times:
                meal_options = [m for m in MEALS if m[1] == meal_type_filter]
                desc, meal_type, carbs = random.choice(meal_options)
                carbs_var = carbs + random.randint(-5, 5)
                meal_time = base + timedelta(hours=hour, minutes=random.randint(0, 30))

                # Before meal glucose
                before_bg = random.randint(85, 160)
                GlucoseLog.objects.create(
                    user=user, value_mgdl=before_bg,
                    measurement_context='before_meal',
                    logged_at=meal_time - timedelta(minutes=5),
                )
                glucose_count += 1

                # Meal
                MealLog.objects.create(
                    user=user, description=desc,
                    estimated_carbs=Decimal(str(carbs_var)),
                    carb_source='manual', meal_type=meal_type,
                    logged_at=meal_time,
                )
                meal_count += 1

                # Bolus insulin
                bolus = round(carbs_var / 10, 1)
                InsulinLog.objects.create(
                    user=user, units=Decimal(str(bolus)),
                    insulin_type='bolus',
                    insulin_brand=random.choice(INSULIN_BRANDS),
                    logged_at=meal_time + timedelta(minutes=2),
                )
                insulin_count += 1

                # After meal glucose (1-2h later)
                after_bg = before_bg + random.randint(20, 80)
                GlucoseLog.objects.create(
                    user=user, value_mgdl=min(after_bg, 300),
                    measurement_context='after_meal',
                    logged_at=meal_time + timedelta(hours=random.choice([1, 2]), minutes=random.randint(0, 30)),
                )
                glucose_count += 1

            # Snack (random, 60% chance)
            if random.random() < 0.6:
                snack_options = [m for m in MEALS if m[1] == 'snack']
                desc, meal_type, carbs = random.choice(snack_options)
                MealLog.objects.create(
                    user=user, description=desc,
                    estimated_carbs=Decimal(str(carbs)),
                    carb_source='manual', meal_type='snack',
                    logged_at=base + timedelta(hours=15, minutes=random.randint(0, 59)),
                )
                meal_count += 1

            # Bedtime glucose
            GlucoseLog.objects.create(
                user=user, value_mgdl=random.randint(90, 150),
                measurement_context='bedtime',
                logged_at=base + timedelta(hours=22, minutes=random.randint(0, 30)),
            )
            glucose_count += 1

            # Sport (50% chance per day)
            if random.random() < 0.5:
                activity, duration, intensity = random.choice(ACTIVITIES)
                sport_hour = random.choice([7, 10, 16, 18])
                bg_before = random.randint(90, 160)
                bg_after = max(bg_before - random.randint(10, 40), 70)
                SportLog.objects.create(
                    user=user, activity_type=activity,
                    duration_min=duration, intensity=intensity,
                    glucose_before=bg_before, glucose_after=bg_after,
                    logged_at=base + timedelta(hours=sport_hour, minutes=random.randint(0, 30)),
                )
                sport_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {days} days: {glucose_count} glucose, {insulin_count} insulin, '
            f'{meal_count} meals, {sport_count} sport logs for {email}'
        ))
