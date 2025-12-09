from collections import defaultdict
from datetime import timedelta

from django.shortcuts import render
from django.db.models import Count

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
        'location': _dimension_breakdown(queryset, 'job__location', total),
        'work_setting': _dimension_breakdown(queryset, 'job__work_setting', total),
        'min_experience_years': _dimension_breakdown(queryset, 'job__min_experience_years', total),
        'salary_range': _salary_range_breakdown(queryset, total),
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


def _salary_range_breakdown(queryset, total):
    """
    Generate salary range breakdown with bucketing.
    Buckets: <$150k, $150k-$180k, $180k-$200k, >$200k
    """
    buckets = {
        '<$150k': 0,
        '$150k-$180k': 0,
        '$180k-$200k': 0,
        '>$200k': 0,
    }
    
    for app in queryset:
        avg_salary = None
        if app.job.min_salary and app.job.max_salary:
            avg_salary = (app.job.min_salary + app.job.max_salary) / 2
        elif app.job.min_salary:
            avg_salary = app.job.min_salary
        elif app.job.max_salary:
            avg_salary = app.job.max_salary
        
        if avg_salary is None:
            continue
        
        if avg_salary < 150000:
            buckets['<$150k'] += 1
        elif avg_salary < 180000:
            buckets['$150k-$180k'] += 1
        elif avg_salary < 200000:
            buckets['$180k-$200k'] += 1
        else:
            buckets['>$200k'] += 1
    
    # Convert to list format, sorted by count
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
    Build application volume timeline grouped by week.
    Returns list of {date, count} dicts for charting.
    """
    timeline = defaultdict(int)
    
    for app in queryset:
        # Group by week (Monday as start of week)
        week_start = app.applied_date - timedelta(days=app.applied_date.weekday())
        timeline[week_start] += 1
    
    # Convert to sorted list
    result = [
        {'date': date.isoformat(), 'count': count}
        for date, count in sorted(timeline.items())
    ]
    
    return result


def _build_callback_timeline(queryset):
    """
    Build callback timeline showing when callbacks occurred (by applied_date).
    Returns list of {date, count} dicts for charting.
    """
    timeline = defaultdict(int)
    
    for app in queryset:
        timeline[app.applied_date] += 1
    
    # Convert to sorted list
    result = [
        {'date': date.isoformat(), 'count': count}
        for date, count in sorted(timeline.items())
    ]
    
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
        'top_location': _top_n_breakdown(queryset, 'job__location', 3),
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


def _safe_percentage(numerator, denominator):
    """Calculate percentage safely (avoid division by zero)."""
    if denominator == 0:
        return 0
    return round((numerator / denominator) * 100, 1)
