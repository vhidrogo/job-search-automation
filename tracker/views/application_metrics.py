from collections import defaultdict

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from tracker.models import Application


def application_metrics(request):
    """
    Three-part analysis view:
    1. Overall summary (total/callback/rejected/closed counts and percentages)
    2. Callback analysis (dimensional breakdowns of successful applications)
    3. Rejection analysis (summary of rejection patterns)
    
    Supports dynamic filtering by date range and all job dimensions.
    """
    filters = _get_filters_from_request(request)
    
    applications = Application.objects.select_related(
        'job', 'status', 'interview_process_status'
    ).filter(**_build_filter_query(filters))
    
    # Part 1: Overall Summary
    total_count = applications.count()
    callback_count = applications.filter(status__state='callback').count()
    rejected_count = applications.filter(status__state='rejected').count()
    closed_count = applications.filter(status__state='closed').count()
    no_response_count = applications.filter(status__isnull=True).count()
    
    overall_summary = {
        'total': total_count,
        'callbacks': {
            'count': callback_count,
            'percent': _safe_percentage(callback_count, total_count),
        },
        'rejected': {
            'count': rejected_count,
            'percent': _safe_percentage(rejected_count, total_count),
        },
        'closed': {
            'count': closed_count,
            'percent': _safe_percentage(closed_count, total_count),
        },
        'no_response': {
            'count': no_response_count,
            'percent': _safe_percentage(no_response_count, total_count),
        },
    }
    
    volume_timeline = _build_volume_timeline(applications)
    
    # Part 2: Callback Analysis
    callbacks = applications.filter(status__state='callback')
    callback_analysis = _analyze_dimension_breakdowns(callbacks)
    callback_timeline = _build_callback_timeline(callbacks)
    
    # Part 3: Rejection Analysis (summary only)
    rejections = applications.filter(status__state='rejected')
    rejection_summary = _build_rejection_summary(rejections)
    
    context = {
        'overall_summary': overall_summary,
        'volume_timeline': volume_timeline,
        'callback_analysis': callback_analysis,
        'callback_timeline': callback_timeline,
        'rejection_summary': rejection_summary,
        'filters': filters,
        'filter_options': _get_filter_options(),
    }
    
    return render(request, 'application_metrics.html', context)


def _get_filters_from_request(request):
    """Extract filter parameters from request."""
    return {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'role': request.GET.getlist('role'),
        'specialization': request.GET.getlist('specialization'),
        'level': request.GET.getlist('level'),
        'location': request.GET.getlist('location'),
        'work_setting': request.GET.getlist('work_setting'),
    }


def _build_filter_query(filters):
    """Build Django ORM filter dict from filter parameters."""
    query = {}
    
    if filters['start_date']:
        query['applied_date__gte'] = filters['start_date']
    if filters['end_date']:
        query['applied_date__lte'] = filters['end_date']
    if filters['role']:
        query['job__role__in'] = filters['role']
    if filters['specialization']:
        query['job__specialization__in'] = filters['specialization']
    if filters['level']:
        query['job__level__in'] = filters['level']
    if filters['location']:
        query['job__location__in'] = filters['location']
    if filters['work_setting']:
        query['job__work_setting__in'] = filters['work_setting']
    
    return query


def _get_filter_options():
    """Get all available filter options from existing jobs."""
    from tracker.models import Job
    
    return {
        'roles': Job.objects.values_list('role', flat=True).distinct().order_by('role'),
        'specializations': Job.objects.exclude(specialization='').values_list('specialization', flat=True).distinct().order_by('specialization'),
        'levels': Job.objects.values_list('level', flat=True).distinct().order_by('level'),
        'locations': Job.objects.values_list('location', flat=True).distinct().order_by('location'),
        'work_settings': Job.objects.values_list('work_setting', flat=True).distinct().order_by('work_setting'),
    }


def _analyze_dimension_breakdowns(queryset):
    """
    Analyze dimensional breakdowns for a filtered queryset (callbacks or rejections).
    Returns breakdown by role, specialization, level, location, work_setting, 
    min_experience_years, and salary_range.
    """
    total = queryset.count()
    
    if total == 0:
        return {}
    
    analysis = {
        'total': total,
        'role': _dimension_breakdown(queryset, 'job__role', total),
        'specialization': _dimension_breakdown(queryset, 'job__specialization', total),
        'level': _dimension_breakdown(queryset, 'job__level', total),
        'location': _location_breakdown(queryset, total),
        'work_setting': _dimension_breakdown(queryset, 'job__work_setting', total),
        'min_experience_years': _dimension_breakdown(queryset, 'job__min_experience_years', total),
        'min_salary_range': _salary_range_breakdown(queryset, 'min_salary', total),
        'max_salary_range': _salary_range_breakdown(queryset, 'max_salary', total),
    }
    
    return analysis


def _dimension_breakdown(queryset, field, total):
    """
    Generate breakdown for a single dimension.
    Returns list of dicts with value, count, and percent, sorted by count descending.
    """
    breakdown = queryset.values(field).annotate(
        count=Count('id')
    ).order_by('-count')
    
    return [
        {
            'value': item[field] or 'Not specified',
            'count': item['count'],
            'percent': _safe_percentage(item['count'], total),
        }
        for item in breakdown
    ]


def _location_breakdown(queryset, total):
    """
    Generate location breakdown with grouping logic.
    Groups Greater Seattle Area cities together.
    """
    location_counts = defaultdict(int)
    
    for app in queryset:
        grouped_location = _group_location(app.job.location)
        location_counts[grouped_location] += 1
    
    result = [
        {
            'value': location,
            'count': count,
            'percent': _safe_percentage(count, total),
        }
        for location, count in location_counts.items()
    ]
    
    return sorted(result, key=lambda x: x['count'], reverse=True)


def _group_location(location):
    """
    Group locations into meaningful categories for analysis.
    Greater Seattle Area cities are grouped together.
    """
    if not location:
        return 'Not specified'
    
    location_lower = location.lower()
    
    seattle_area_cities = [
        'seattle',
        'bellevue',
        'redmond',
        'kirkland',
        'kent',
        'renton',
        'everett',
        'tacoma',
        'bothell',
        'sammamish',
        'issaquah',
    ]
    
    for city in seattle_area_cities:
        if city in location_lower:
            return 'Greater Seattle Area'
    
    if 'remote' in location_lower or 'u.s.' in location_lower:
        return 'Remote (U.S.)'
    
    return location


def _salary_range_breakdown(queryset, field, total):
    """
    Generate salary range breakdown with bucketing.
    Buckets: <$150k, $150k-$180k, $180k-$200k, >$200k
    """
    buckets = {
        '< $150k': 0,
        '$150k - $180k': 0,
        '$180k - $200k': 0,
        '> $200k': 0,
    }
    
    for app in queryset:
        salary = getattr(app.job, field)
        
        if salary is None:
            continue
        
        if salary < 150000:
            buckets['< $150k'] += 1
        elif salary < 180000:
            buckets['$150k - $180k'] += 1
        elif salary < 200000:
            buckets['$180k - $200k'] += 1
        else:
            buckets['> $200k'] += 1
    
    result = [
        {
            'value': bucket,
            'count': count,
            'percent': _safe_percentage(count, total),
        }
        for bucket, count in buckets.items()
        if count > 0
    ]
    
    return sorted(result, key=lambda x: x['count'], reverse=True)


def _build_volume_timeline(queryset):
    """
    Build application volume timeline grouped by date.
    Returns list of {date, count} dicts for charting.
    """
    timeline = defaultdict(int)
    
    for app in queryset:
        local_date = timezone.localtime(app.applied_date).date()
        timeline[local_date] += 1
    
    result = [
        {'date': date.isoformat(), 'count': count}
        for date, count in sorted(timeline.items())
    ]
    
    return result


def _build_callback_timeline(queryset):
    """
    Build callback timeline showing when callbacks occurred (by applied_date).
    Includes all dates in range with zero counts for dates without callbacks.
    Returns list of {date, count} dicts for charting.
    """
    from datetime import timedelta
    
    callback_dates = defaultdict(int)
    
    for app in queryset:
        local_date = timezone.localtime(app.applied_date).date()
        callback_dates[local_date] += 1
    
    if not callback_dates:
        return []
    
    min_date = min(callback_dates.keys())
    max_date = max(callback_dates.keys())
    
    result = []
    current_date = min_date
    while current_date <= max_date:
        result.append({
            'date': current_date.isoformat(),
            'count': callback_dates.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return result


def _build_rejection_summary(queryset):
    """
    Build high-level rejection summary (top dimensions only).
    Returns dict with counts for top 3 values per dimension.
    """
    total = queryset.count()
    
    if total == 0:
        return None
    
    summary = {
        'total': total,
        'top_role': _top_n_breakdown(queryset, 'job__role', 3),
        'top_location': _top_n_location_breakdown(queryset, 3),
        'top_work_setting': _top_n_breakdown(queryset, 'job__work_setting', 3),
    }
    
    return summary


def _top_n_breakdown(queryset, field, n):
    """Get top N values for a dimension."""
    breakdown = queryset.values(field).annotate(
        count=Count('id')
    ).order_by('-count')[:n]
    
    return [
        {'value': item[field] or 'Not specified', 'count': item['count']}
        for item in breakdown
    ]


def _top_n_location_breakdown(queryset, n):
    """Get top N grouped locations."""
    location_counts = defaultdict(int)
    
    for app in queryset:
        grouped_location = _group_location(app.job.location)
        location_counts[grouped_location] += 1
    
    sorted_locations = sorted(
        location_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n]
    
    return [
        {'value': location, 'count': count}
        for location, count in sorted_locations
    ]


def _safe_percentage(numerator, denominator):
    """Calculate percentage safely (avoid division by zero)."""
    if denominator == 0:
        return 0
    return round((numerator / denominator) * 100, 1)
