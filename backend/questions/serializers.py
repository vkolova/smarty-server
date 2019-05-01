from rest_framework import serializers

from .models import Answer, Question

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'content', 'is_correct')

    content = serializers.CharField(max_length=255)
    is_correct = serializers.BooleanField(default=False)    


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'content', 'points', 'answers', 'correct_answer')
        read_only_fields = ('id', 'correct_anser')
    
    content = serializers.CharField(max_length=500, min_length=None, allow_blank=False, trim_whitespace=False)
    points = serializers.IntegerField()
    answers = AnswerSerializer(required=False, many=True)

    # correct_answer = serializers.SerializerMethodField()

    # def get_correct_answer(self, obj):
    #     return obj.answers.get(is_correct=True)

