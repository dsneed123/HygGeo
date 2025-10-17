from django import forms
from django.contrib.auth.models import User
from django.db import models as django_models
from .models import Project, Task, TaskComment


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'slug', 'description', 'status', 'color', 'team_members',
                  'start_date', 'end_date', 'progress_percentage']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-control'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'priority', 'status',
                  'due_date', 'start_date', 'estimated_hours', 'actual_hours', 'tags',
                  'send_reminder', 'reminder_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., frontend, bug, urgent'}),
            'send_reminder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter projects based on user permissions
        if self.user:
            if self.user.is_staff:
                self.fields['project'].queryset = Project.objects.all()
            else:
                self.fields['project'].queryset = Project.objects.filter(
                    django_models.Q(owner=self.user) | django_models.Q(team_members=self.user)
                ).distinct()

            # Filter assignable users to staff and project team members
            self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Add a comment...'
            })
        }
