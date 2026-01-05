from collections import defaultdict
from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from tracker.models import Application, Job


def application_metrics(request):
    """
    Three-part analysis view:
    1. Overall summary (total/callback/rejected/closed counts and percentages)
    2. Callback analysis (dimensional breakdowns of successful applications)
    3. Rejection analysis (summary of rejection patterns)
    
    Supports dynamic filtering by date range and all job dimensions.
    """
    filters = _get_filters_from_request(request)
    selected_dimension = request.GET.get("dimension", "role")

    applications = Application.objects.select_related(
        "job", "status", "interview_process_status"
    ).filter(**_build_filter_query(filters))

    if filters["location"]:
        applications = _filter_by_grouped_location(applications, filters["location"])

    total_count = applications.count()
    callback_count = applications.filter(status__state="callback").count()
    rejected_count = applications.filter(status__state="rejected").count()
    closed_count = applications.filter(status__state="closed").count()
    no_response_count = applications.filter(status__isnull=True).count()

    overall_summary = {
        "total": total_count,
        "callbacks": {
            "count": callback_count,
            "percent": _safe_percentage(callback_count, total_count),
        },
        "rejected": {
            "count": rejected_count,
            "percent": _safe_percentage(rejected_count, total_count),
        },
        "closed": {
            "count": closed_count,
            "percent": _safe_percentage(closed_count, total_count),
        },
        "no_response": {
            "count": no_response_count,
            "percent": _safe_percentage(no_response_count, total_count),
        },
    }

    volume_timeline = _build_volume_timeline(applications)

    callbacks = applications.filter(status__state="callback")
    callback_analysis = _analyze_dimension_breakdowns(callbacks)
    callback_timeline = _build_callback_timeline_with_metrics(callbacks, applications)

    rejections = applications.filter(status__state="rejected")
    rejection_summary = _build_rejection_summary(rejections)
    
    dimension_deep_dive = _build_dimension_deep_dive(applications, selected_dimension)

    context = {
        "overall_summary": overall_summary,
        "volume_timeline": volume_timeline,
        "callback_analysis": callback_analysis,
        "callback_timeline": callback_timeline,
        "rejection_summary": rejection_summary,
        "dimension_deep_dive": dimension_deep_dive,
        "selected_dimension": selected_dimension,
        "filters": filters,
        "filter_options": _get_filter_options(),
    }

    return render(request, "application_metrics.html", context)


def _get_filters_from_request(request):
    """Extract filter parameters from request."""
    return {
        "start_date": request.GET.get("start_date"),
        "end_date": request.GET.get("end_date"),
        "role": request.GET.getlist("role"),
        "specialization": request.GET.getlist("specialization"),
        "level": request.GET.getlist("level"),
        "location": request.GET.getlist("location"),
        "work_setting": request.GET.getlist("work_setting"),
        "source": request.GET.getlist("source"),
    }


def _filter_by_grouped_location(queryset, selected_locations):
    """Filter applications by grouped location values."""
    filtered_ids = []
    
    for app in queryset:
        grouped_location = _group_location(app.job.location)
        if grouped_location in selected_locations:
            filtered_ids.append(app.id)
    
    return queryset.filter(id__in=filtered_ids)


def _build_filter_query(filters):
    """Build Django ORM filter dict from filter parameters."""
    query = {}
    
    if filters["start_date"]:
        query["applied_date__gte"] = filters["start_date"]
    if filters["end_date"]:
        query["applied_date__lte"] = filters["end_date"]
    if filters["role"]:
        query["job__role__in"] = filters["role"]
    if filters["specialization"]:
        query["job__specialization__in"] = filters["specialization"]
    if filters["level"]:
        query["job__level__in"] = filters["level"]
    if filters["work_setting"]:
        query["job__work_setting__in"] = filters["work_setting"]
    if filters["source"]:
        query["job__source__in"] = filters["source"]
    
    return query


def _get_filter_options():
    all_locations = Job.objects.values_list("location", flat=True).distinct()
    grouped_locations = sorted(set(_group_location(loc) for loc in all_locations))

    return {
        "roles": Job.objects.values_list("role", flat=True).distinct().order_by("role"),
        "specializations": Job.objects.exclude(specialization="").values_list("specialization", flat=True).distinct().order_by("specialization"),
        "levels": Job.objects.values_list("level", flat=True).distinct().order_by("level"),
        "locations": grouped_locations,
        "work_settings": Job.objects.values_list("work_setting", flat=True).distinct().order_by("work_setting"),
        "sources": Job.objects.values_list("source", flat=True).distinct().order_by("source"),
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
        "total": total,
        "role": _dimension_breakdown(queryset, "job__role", total),
        "specialization": _dimension_breakdown(queryset, "job__specialization", total),
        "level": _dimension_breakdown(queryset, "job__level", total),
        "location": _location_breakdown(queryset, total),
        "work_setting": _dimension_breakdown(queryset, "job__work_setting", total),
        "source": _dimension_breakdown(queryset, "job__source", total),
        "min_experience_years": _dimension_breakdown(queryset, "job__min_experience_years", total),
        "min_salary_range": _numeric_range_breakdown(
            queryset,
            "min_salary",
            total,
            base=100_000,
            interval=20_000,
            count=4,
        ),

        "max_salary_range": _numeric_range_breakdown(
            queryset,
            "max_salary",
            total,
            base=150_000,
            interval=20_000,
            count=4,
        ),
    }
    
    return analysis


def _dimension_breakdown(queryset, field, total):
    """
    Generate breakdown for a single dimension.
    Returns list of dicts with value, count, and percent, sorted by count descending.
    """
    breakdown = queryset.values(field).annotate(
        count=Count("id")
    ).order_by("-count")
    
    return [
        {
            "value": item[field] or "Not specified",
            "count": item["count"],
            "percent": _safe_percentage(item["count"], total),
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
            "value": location,
            "count": count,
            "percent": _safe_percentage(count, total),
        }
        for location, count in location_counts.items()
    ]
    
    return sorted(result, key=lambda x: x["count"], reverse=True)


def _group_location(location):
    """
    Group locations into meaningful categories for analysis.
    Greater Seattle Area cities are grouped together.
    """
    if not location:
        return "Not specified"
    
    if location == "Remote (U.S.)":
        return location
    
    city = location.split(",")[0].lower()
    
    seattle_area_cities = {
        "seattle",
        "bellevue",
        "redmond",
        "kirkland",
        "kent",
        "renton",
        "everett",
        "tacoma",
        "bothell",
        "sammamish",
        "issaquah",
        "tukwila",
        "silverdale",
        "seatac",
        "joint base lewis-mcchord",
        "bremerton",
    }

    if city in seattle_area_cities:
        return "Greater Seattle Area"
    
    chicago_area_cities = {
        "chicago",
        "aurora",
        "deerfield",
        "lombard",
        "oak brook",
        "oakbrook terrace",
        "schaumburg",
        "skokie",
    }

    if city in chicago_area_cities:
        return "Greater Chicago Area"
    
    milwaukee_area_cities = {
        "milwaukee",
        "racine",
        "brookfield",
        "menomonee falls",
        "mequon",
        "pewaukee",
    }

    if city in milwaukee_area_cities:
        return "Greater Milwaukee Area"
    
    return location


def _numeric_range_breakdown(
    queryset,
    field,
    total,
    *,
    base,
    interval,
    count,
    formatter=lambda x: f"${int(x/1000)}k",
):
    """
    Generic numeric range bucketing.

    Example:
      base=100_000, interval=20_000, count=4
      -> <100k, 100-120k, 120-140k, >=140k
    """
    assert count >= 2

    # Build bucket boundaries
    edges = [base + i * interval for i in range(count)]
    buckets = {}

    # Labels
    buckets[f"< {formatter(base)}"] = 0
    for start, end in zip(edges[:-1], edges[1:]):
        buckets[f"{formatter(start)} - {formatter(end)}"] = 0
    buckets[f">= {formatter(edges[-1])}"] = 0

    for app in queryset:
        value = getattr(app.job, field)
        if value is None:
            continue

        if value < base:
            buckets[f"< {formatter(base)}"] += 1
        elif value >= edges[-1]:
            buckets[f">= {formatter(edges[-1])}"] += 1
        else:
            idx = (value - base) // interval
            start = edges[int(idx)]
            end = start + interval
            buckets[f"{formatter(start)} - {formatter(end)}"] += 1

    result = [
        {
            "value": label,
            "count": count,
            "percent": _safe_percentage(count, total),
        }
        for label, count in buckets.items()
        if count > 0
    ]

    return sorted(result, key=lambda x: x["count"], reverse=True)


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
        {"date": date.isoformat(), "count": count}
        for date, count in sorted(timeline.items())
    ]
    
    return result


def _build_callback_timeline_with_metrics(callbacks_queryset, all_applications_queryset):
    """
    Build callback timeline showing when callbacks occurred (by applied_date).
    Includes running application count and callback rate for each callback date.
    Returns list of {date, count, running_total, callback_rate} dicts for charting.
    """
    callback_dates = defaultdict(int)
    
    for app in callbacks_queryset:
        local_date = timezone.localtime(app.applied_date).date()
        callback_dates[local_date] += 1
    
    if not callback_dates:
        return []
    
    # Build running total of applications up to each date
    all_apps_by_date = []
    for app in all_applications_queryset:
        local_date = timezone.localtime(app.applied_date).date()
        all_apps_by_date.append(local_date)
    
    all_apps_by_date.sort()
    
    min_date = min(callback_dates.keys())
    max_date = max(callback_dates.keys())
    
    result = []
    running_total = 0
    running_callbacks = 0
    
    current_date = min_date
    while current_date <= max_date:
        # Count applications up to and including current date
        apps_up_to_date = sum(1 for d in all_apps_by_date if d <= current_date)
        
        # Count callbacks up to and including current date
        callbacks_up_to_date = sum(
            count for date, count in callback_dates.items() if date <= current_date
        )
        
        callback_count = callback_dates.get(current_date, 0)
        
        # Calculate callback rate at this point in time
        callback_rate = _safe_percentage(callbacks_up_to_date, apps_up_to_date)
        
        result.append({
            "date": current_date.isoformat(),
            "count": callback_count,
            "running_total": apps_up_to_date,
            "callback_rate": callback_rate
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
        "total": total,
        "top_role": _top_n_breakdown(queryset, "job__role", 3),
        "top_location": _top_n_location_breakdown(queryset, 3),
        "top_work_setting": _top_n_breakdown(queryset, "job__work_setting", 3),
        "top_source": _top_n_breakdown(queryset, "job__source", 3),
    }
    
    return summary


def _top_n_breakdown(queryset, field, n):
    """Get top N values for a dimension."""
    breakdown = queryset.values(field).annotate(
        count=Count("id")
    ).order_by("-count")[:n]
    
    return [
        {"value": item[field] or "Not specified", "count": item["count"]}
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
        {"value": location, "count": count}
        for location, count in sorted_locations
    ]


def _safe_percentage(numerator, denominator):
    """Calculate percentage safely (avoid division by zero)."""
    if denominator == 0:
        return 0
    return round((numerator / denominator) * 100, 1)


def _build_dimension_deep_dive(queryset, dimension):
    """
    Build detailed breakdown for a single dimension showing:
    - Total applications
    - Callbacks (with callback rate %)
    - Rejected
    - Closed
    - No Response
    for each value in the dimension.
    """
    dimension_map = {
        "role": "job__role",
        "specialization": "job__specialization",
        "level": "job__level",
        "location": None,
        "source": "job__source",
    }
    
    field = dimension_map.get(dimension)
    
    if dimension == "location":
        return _build_location_deep_dive(queryset)
    
    value_stats = defaultdict(lambda: {
        "total": 0,
        "callbacks": 0,
        "rejected": 0,
        "closed": 0,
        "no_response": 0,
    })
    
    for app in queryset:
        value = getattr(app.job, field.split("__")[1]) or "Not specified"
        value_stats[value]["total"] += 1
        
        if hasattr(app, "status"):
            state = app.status.state
            if state == "callback":
                value_stats[value]["callbacks"] += 1
            elif state == "rejected":
                value_stats[value]["rejected"] += 1
            elif state == "closed":
                value_stats[value]["closed"] += 1
        else:
            value_stats[value]["no_response"] += 1
    
    result = [
        {
            "value": value,
            "total": stats["total"],
            "callbacks": stats["callbacks"],
            "callback_rate": _safe_percentage(stats["callbacks"], stats["total"]),
            "rejected": stats["rejected"],
            "closed": stats["closed"],
            "no_response": stats["no_response"],
        }
        for value, stats in value_stats.items()
    ]
    
    return sorted(result, key=lambda x: x["total"], reverse=True)


def _build_location_deep_dive(queryset):
    """Build location deep dive with grouping."""
    location_stats = defaultdict(lambda: {
        "total": 0,
        "callbacks": 0,
        "rejected": 0,
        "closed": 0,
        "no_response": 0,
    })
    
    for app in queryset:
        grouped_location = _group_location(app.job.location)
        location_stats[grouped_location]["total"] += 1
        
        if hasattr(app, "status"):
            state = app.status.state
            if state == "callback":
                location_stats[grouped_location]["callbacks"] += 1
            elif state == "rejected":
                location_stats[grouped_location]["rejected"] += 1
            elif state == "closed":
                location_stats[grouped_location]["closed"] += 1
        else:
            location_stats[grouped_location]["no_response"] += 1
    
    result = [
        {
            "value": location,
            "total": stats["total"],
            "callbacks": stats["callbacks"],
            "callback_rate": _safe_percentage(stats["callbacks"], stats["total"]),
            "rejected": stats["rejected"],
            "closed": stats["closed"],
            "no_response": stats["no_response"],
        }
        for location, stats in location_stats.items()
    ]
    
    return sorted(result, key=lambda x: x["total"], reverse=True)
