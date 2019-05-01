from django.contrib import admin

from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    verbose_name = 'Answer'
    verbose_name_plural = 'Answers'
    fields = ('id',  'content', 'is_correct')
    readonly_fields = ('id',)
    extra = 0

class QuestionAdmin(admin.ModelAdmin):
    model = Question
    fields = ('id', 'content', 'points')
    list_display = ('id', 'content', 'points')
    readonly_fields = ('id',)
    ordering = ('-id',)
    inlines = (AnswerInline,)

class AnswerAdmin(admin.ModelAdmin):
    model = Answer
    fields = ('id', 'content')
    list_display = ('id', 'content', 'is_correct')
    readonly_fields = ('id',)
    ordering = ('-id',)

    # def question_text(self, obj):
    #     return obj.content

admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)