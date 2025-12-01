from django.shortcuts import render
from django.utils import timezone
from tracker.models import Interview


def upcoming_interviews(request):
    stage = request.GET.get('stage', None)
    now = timezone.now()
    
    interviews = Interview.objects.filter(scheduled_at__gt=now)
    
    if stage:
        interviews = interviews.filter(stage=stage)
    
    interviews = interviews.select_related(
        'application', 'application__job'
    ).order_by('scheduled_at')
    
    stages = Interview.Stage.choices
    
    context = {
        'interviews': interviews,
        'current_time': now,
        'stages': stages,
        'selected_stage': stage,
    }
    
    return render(request, 'upcoming_interviews.html', context)
