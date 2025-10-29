"""
PDF Generation Test Script

Generates test PDFs for different resume templates without requiring LLM API calls.
Useful for:
- Visual regression testing after CSS/template changes
- Developing new templates with realistic content
- Validating bullet counts per role configuration
- Iterating on formatting without incurring API costs

Usage:
    python manage.py shell < scripts/generate_test_pdfs.py

The script will:
1. Create test data (templates, jobs, resumes, bullets, skills)
2. Generate PDFs for each configured template
3. Open each PDF automatically for review
4. Clean up test data from the database

PDFs are saved to test_output/ directory (add to .gitignore).
"""

import subprocess
import sys

from resume.models import (
    ExperienceRole,
    Resume,
    ResumeExperienceBullet,
    ResumeSkillBullet,
    ResumeTemplate,
    TemplateRoleConfig,
)
from tracker.models import Job, JobLevel, JobRole, WorkSetting


OUTPUT_DIR = "test_output"

def reset_db():
    models = [
        ExperienceRole,
        Resume,
        ResumeExperienceBullet,
        ResumeSkillBullet,
        ResumeTemplate,
        TemplateRoleConfig,
        Job
    ]

    for model in models:
        model.objects.all().delete()

def create_test_data(role, level, template_path, style_path, max_bullets, bullets):
    template = ResumeTemplate.objects.create(
        target_role=role,
        target_level=level,
        template_path=template_path,
        style_path=style_path,
    )

    job = Job.objects.create(
        company="Test Corp",
        listing_job_title=f"{role} {level}",
        role=role,
        level=level,
        location="Seattle, WA",
        work_setting=WorkSetting.REMOTE,
    )

    resume = Resume.objects.create(
        template=template,
        job=job,
        match_ratio=0.85,
    )

    for i in range(len(bullets)):
        if len(bullets[i]) > max_bullets[i]:
            raise ValueError(f"Too many experience bullets for role {i + 1}. Count is {len(bullets[i])} but should not exceed {max_bullets[i]}.")

        experience_role = ExperienceRole.objects.create(
            key=f"test_role_{i}",
            company="Previous Company",
            title="Software Engineer",
        )

        TemplateRoleConfig.objects.create(
            template=template,
            experience_role=experience_role,
            order=i + 1,
            max_bullet_count=max_bullets[i],
        )

        for j in range(len(bullets[i])):
            ResumeExperienceBullet.objects.create(
                resume=resume,
                experience_role=experience_role,
                order=j + 1,
                text=bullets[i][j],
            )

    skills = {
        "Languages": "Python, Java, JavaScript, SQL, HTML, CSS",
        "Frameworks": "Django, React",
        "Databases": "PostgreSQL, DynamoDB",
        "Cloud & DevOps": "AWS, GCP, Docker",
    }

    for category, skills_text in skills.items():
        ResumeSkillBullet.objects.create(
            resume=resume,
            category=category,
            skills_text=skills_text,
        )

    return job

tests = [
    {
        "target_role": JobRole.SOFTWARE_ENGINEER,
        "target_level": JobLevel.I,
        "template_path": "html/software_engineer_i.html",
        "style_path": "css/resume_standard.css",
        "max_bullets_per_role": [4, 4],
        "bullets": [
            [
                "Owned end-to-end migration of interactive financial dashboards, reducing load times by 90% and code complexity by 60%, by integrating Plotly Dash visualizations into a scalable Django platform with abstracted query layers.",
                "Designed and implemented scalable goal-setting, rewards, and transaction syncing systems, ensuring data consistency and reliability, by developing RESTful APIs using Python (Django) and PostgreSQL.",
                "Delivered an extensible async notification framework using Django, Celery, and object-oriented design patterns, enabling automated, real-time goal progress alerts across multiple goal types.",
                "Improved admin tooling performance by optimizing ORM queries with raw SQL, reducing load times from 12s to under 2s while maintaining data integrity and traceability.",
            ],
            [
                "Led development of scalable microservices and APIs supporting Prime Rewards lifecycle management, enabling real-time promotion tracking across North America, Europe, and Asia-Pacific using Java, DynamoDB, and AWS.",
                "Improved operational efficiency by delivering full-stack features in Vue.js and Java for internal promotion management tools, streamlining CRUD operations on promotions, incentives, and rewards.",
                "Ensured backend system reliability and scalability by deploying microservices across three AWS regions and integrating asynchronous workflows to meet strict availability SLAs.",
                "Eliminated manual test account provisioning and deactivation by engineering a centralized configuration store, improving development velocity and operational stability.",
            ]
        ]
    },
    {
        "target_role": JobRole.SOFTWARE_ENGINEER,
        "target_level": JobLevel.II,
        "template_path": "html/software_engineer_ii.html",
        "style_path": "css/resume_compact.css",
        "max_bullets_per_role": [4, 4, 2, 2],
        "bullets": [
            [
                "Owned end-to-end migration of interactive financial dashboards, reducing load times by 90% and code complexity by 60%, by integrating Plotly Dash visualizations into a scalable Django platform with abstracted query layers.",
                "Designed and implemented scalable goal-setting, rewards, and transaction syncing systems, ensuring data consistency and reliability, by developing RESTful APIs using Python (Django) and PostgreSQL.",
                "Delivered an extensible async notification framework using Django, Celery, and object-oriented design patterns, enabling automated, real-time goal progress alerts across multiple goal types.",
                "Improved admin tooling performance by optimizing ORM queries with raw SQL, reducing load times from 12s to under 2s while maintaining data integrity and traceability.",
            ],
            [
                "Led development of scalable microservices and APIs supporting Prime Rewards lifecycle management, enabling real-time promotion tracking across North America, Europe, and Asia-Pacific using Java, DynamoDB, and AWS.",
                "Improved operational efficiency by delivering full-stack features in Vue.js and Java for internal promotion management tools, streamlining CRUD operations on promotions, incentives, and rewards.",
                "Ensured backend system reliability and scalability by deploying microservices across three AWS regions and integrating asynchronous workflows to meet strict availability SLAs.",
                "Eliminated manual test account provisioning and deactivation by engineering a centralized configuration store, improving development velocity and operational stability.",
            ],
            [
                "Delivered on-time executive dashboards for Amazon Transportation Services by optimizing SQL queries and data pipelines, reducing query execution time by 30% to meet early-morning SLAs.",
                "Built scalable data pipelines using Amazon S3, Glue, and Redshift, reducing third-party vendor onboarding time and enabling operational growth through standardized SOPs.",
            ],
            [
                "Saved 5+ hours weekly by developing a desktop GUI application using Python (tkinter) and SQL to automate PDF report generation.",
                "Improved large-scale data processing efficiency by applying Python chunking techniques to handle datasets exceeding 20M records."
            ],
        ]
    },
]

def main():
    for config in tests:
        role, level, template_path, style_path, max_bullets, bullets = config.values()
        print(f"Running PDF test for role: {role}, level: {level}, template_path: {template_path}, style_path: {style_path}")
        reset_db()
        print("Creating test data...")
        job = create_test_data(role, level, template_path, style_path, max_bullets, bullets)
        print("Generating PDF...")
        pdf_path = job.generate_resume_pdf(OUTPUT_DIR)
        print(f"PDF generated at: {pdf_path}")
        reset_db()
        subprocess.run(["open", pdf_path])

try:
    main()
except Exception as e:
    print(f"Test failed due to exception: {e}")
    reset_db()
    sys.exit(1)

print(f"Test complete - check the PDF at {OUTPUT_DIR}\n")