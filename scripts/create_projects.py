"""
Utility to bulk create ExperienceProject objects from a list of dictionaries.

Usage:
    python manage.py shell
    >>> from create_projects import create_projects_from_data
    >>> projects = [{"short_name": "...", ...}, ...]
    >>> create_projects_from_data(projects, role_key="navit")
"""

from typing import List, Dict, Any

from resume.models import ExperienceProject, ExperienceRole


def create_projects_from_data(
    projects: List[Dict[str, Any]], 
    role_key: str,
    verbose: bool = True
) -> List['ExperienceProject']:
    """
    Create ExperienceProject objects from a list of dictionaries.
    
    Args:
        projects: List of project dictionaries with keys matching ExperienceProject fields
        role_key: The key identifier for the ExperienceRole to associate with projects
        verbose: Whether to print progress messages
    
    Returns:
        List of created ExperienceProject objects
    
    Raises:
        ExperienceRole.DoesNotExist: If the specified ExperienceRole does not exist
        ValueError: If required fields are missing from project dictionaries
    """
    # Fetch the ExperienceRole
    try:
        experience_role = ExperienceRole.objects.get(key=role_key)
        if verbose:
            print(f"Found role: {experience_role}")
    except ExperienceRole.DoesNotExist:
        raise ExperienceRole.DoesNotExist(
            f"ExperienceRole with key '{role_key}' does not exist. "
            f"Please create it first or check the key."
        )
    
    required_fields = ['short_name', 'problem_context', 'actions', 'tools', 'outcomes', 'impact_area']
    
    # Validate all projects first
    projects_to_create = []
    for i, project_data in enumerate(projects, 1):
        if verbose:
            print(f"Validating project: {project_data['short_name']}")

        missing_fields = [field for field in required_fields if field not in project_data]
        if missing_fields:
            raise ValueError(
                f"Project {i} is missing required fields: {', '.join(missing_fields)}"
            )
        
        # Build the project object (not yet saved)
        project = ExperienceProject(
            experience_role=experience_role,
            short_name=project_data['short_name'],
            problem_context=project_data['problem_context'],
            actions=project_data['actions'],
            tools=project_data['tools'],
            outcomes=project_data['outcomes'],
            impact_area=project_data['impact_area']
        )
        projects_to_create.append(project)
    
    # Bulk create all projects in one database operation
    created_projects = ExperienceProject.objects.bulk_create(projects_to_create)
    
    if verbose:
        print(f"\nSuccessfully created {len(created_projects)} projects for role '{role_key}'")
    
    return created_projects
