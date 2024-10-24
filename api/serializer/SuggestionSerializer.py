from rest_framework import serializers
from api.model.Suggestion import Suggestion
from api.serializer.LessonSerializer import LessonSerializer

class SuggestionSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)  # Use nested serializer
    class Meta:
        model = Suggestion
        fields = ['id', 'lesson', 'insights', 'content', 'old_content']
