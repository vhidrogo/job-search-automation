from django.db import models


class InterviewPreparation(models.Model):
    """
    Interview type-specific preparation (questions, responses, strategy).
    One record per interview type per application.

    Fields:
        - interview: FK to the associated Interview.
        - predicted_questions: Predicted questions with STAR responses (markdown formatted).
        - interviewer_questions: Interviewer-aligned questions to ask (markdown formatted)
    """
    interview = models.OneToOneField(
        "Interview",
        on_delete=models.CASCADE,
        related_name="preparation"
    )
    
    predicted_questions = models.TextField(
        help_text="3-5 predicted questions with intent + STAR answers (markdown)"
    )
    
    interviewer_questions = models.TextField(
        help_text="5 strategic questions with 'why this works' explanations (markdown)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [["interview"]]

    def __str__(self):
        return str(self.interview)
