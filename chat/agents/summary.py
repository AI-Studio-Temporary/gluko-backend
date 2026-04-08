"""Summary agent — query today's logs and present a formatted summary."""

from django.db.models import Sum
from django.utils import timezone

from logs.models import GlucoseLog, InsulinLog, MealLog, SportLog


def handle(user) -> str:
    """Build a summary of today's health data."""
    today = timezone.localdate()

    glucose = list(GlucoseLog.objects.filter(user=user, logged_at__date=today).order_by('logged_at'))
    insulin = list(InsulinLog.objects.filter(user=user, logged_at__date=today).order_by('logged_at'))
    meals = list(MealLog.objects.filter(user=user, logged_at__date=today).order_by('logged_at'))
    sport = list(SportLog.objects.filter(user=user, logged_at__date=today).order_by('logged_at'))

    if not any([glucose, insulin, meals, sport]):
        return "No logs for today yet. Start by logging your glucose, a meal, or an activity!"

    parts = [f"**Your day so far** — {today.strftime('%A, %d %B %Y')}\n"]

    # Glucose
    if glucose:
        parts.append(f"**Glucose** ({len(glucose)} readings)")
        for g in glucose:
            time = timezone.localtime(g.logged_at).strftime('%H:%M')
            flag = ' ⚠️' if g.value_mgdl < 70 or g.value_mgdl > 180 else ''
            parts.append(f"  {time} — {g.value_mgdl} mg/dL ({g.get_measurement_context_display()}){flag}")

    # Insulin
    if insulin:
        total = InsulinLog.objects.filter(user=user, logged_at__date=today).aggregate(t=Sum('units'))['t']
        parts.append(f"\n**Insulin** ({len(insulin)} doses, {total}u total)")
        for i in insulin:
            time = timezone.localtime(i.logged_at).strftime('%H:%M')
            brand = f' {i.insulin_brand}' if i.insulin_brand else ''
            parts.append(f"  {time} — {i.units}u {i.insulin_type}{brand}")

    # Meals
    if meals:
        total_carbs = MealLog.objects.filter(user=user, logged_at__date=today).aggregate(t=Sum('estimated_carbs'))['t'] or 0
        parts.append(f"\n**Meals** ({len(meals)} meals, {total_carbs}g carbs total)")
        for m in meals:
            time = timezone.localtime(m.logged_at).strftime('%H:%M')
            carbs = f" — {m.estimated_carbs}g" if m.estimated_carbs else ''
            parts.append(f"  {time} — {m.description}{carbs}")

    # Sport
    if sport:
        total_min = SportLog.objects.filter(user=user, logged_at__date=today).aggregate(t=Sum('duration_min'))['t'] or 0
        parts.append(f"\n**Activity** ({len(sport)} sessions, {total_min} min total)")
        for s in sport:
            time = timezone.localtime(s.logged_at).strftime('%H:%M')
            parts.append(f"  {time} — {s.activity_type} {s.duration_min}min ({s.intensity})")

    return '\n'.join(parts)
