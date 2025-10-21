from resume.models.resume import Resume


def build_experience_bullets_for_prompt(resume: Resume) -> str:
    """Format experience bullets from a resume into a flat list for LLM prompts.
    
    This helper queries all non-excluded experience bullets for a resume
    and formats them as a simple numbered list. Used by ResumeWriter
    (for skill generation) and ResumeMatcher (for requirement evaluation).
    
    Args:
        resume: The Resume instance to extract bullets from.
        
    Returns:
        Formatted string with bullets as a numbered list.
    """
    bullets = resume.experience_bullets.filter(exclude=False).select_related(
        'experience_role'
    ).order_by('experience_role__id', 'order')
    
    if not bullets.exists():
        return "No experience bullets available."
    
    bullet_lines = []
    for idx, bullet in enumerate(bullets, start=1):
        bullet_lines.append(f"{idx}. {bullet.display_text()}")
    
    return "\n".join(bullet_lines)
