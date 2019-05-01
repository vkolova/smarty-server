from django.db import models


class Question(models.Model):
    content = models.TextField(max_length=1000, help_text='Question text')
    points = models.IntegerField(default=1)

    def correct_answer(self):
        return self.answers.get(is_correct=True).id

class Answer(models.Model):
    content = models.TextField(max_length=500, help_text='Answer text')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', help_text='Question')
    is_correct = models.BooleanField(default=False)