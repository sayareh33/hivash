from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Visit

@staff_member_required
def analytics_dashboard(request):
    stats = (
        Visit.objects
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total=Count('id'))
        .order_by('-date')[:7]
    )
    daily_data = {item['date'].strftime('%Y-%m-%d'): item['total'] for item in stats}

    context = {
        'chart_data': daily_data,
        'total_visits': Visit.objects.count(),
        'unique_ips': Visit.objects.values('ip_address').distinct().count(),
    }
    return render(request, 'analytics/dashboard.html', context)


