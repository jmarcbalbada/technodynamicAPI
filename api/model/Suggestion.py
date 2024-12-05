from django.db import models
from api.model.Lesson import Lesson
from api.model.Notification import Notification

class Suggestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE )
    insights = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    old_content = models.TextField()
    ai_delimiter = models.TextField(null=True, blank=True)

    # notif is required
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='notification', 
        null=False, 
        default=1
    )

    def __str__(self):
        return f"Suggestion for Lesson {self.lesson.lessonNumber}"
    