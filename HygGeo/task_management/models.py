from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Project(models.Model):
    """Project to group related tasks"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    COLOR_CHOICES = [
        ('#2d5a3d', 'Hygge Green'),
        ('#4285F4', 'Blue'),
        ('#e74c3c', 'Red'),
        ('#9b59b6', 'Purple'),
        ('#f39c12', 'Orange'),
        ('#16a085', 'Teal'),
        ('#e67e22', 'Carrot'),
        ('#34495e', 'Dark Gray'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#2d5a3d')

    # Team members
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    team_members = models.ManyToManyField(User, related_name='projects', blank=True)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Progress tracking
    progress_percentage = models.IntegerField(default=0, help_text='Percentage complete (0-100)')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('task_management:project_detail', kwargs={'slug': self.slug})

    def get_task_count(self):
        return self.tasks.count()

    def get_completed_task_count(self):
        return self.tasks.filter(status='completed').count()

    def calculate_progress(self):
        """Auto-calculate progress based on completed tasks"""
        total = self.get_task_count()
        if total == 0:
            return 0
        completed = self.get_completed_task_count()
        return int((completed / total) * 100)


class Task(models.Model):
    """Individual task with assignments and tracking"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic info
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

    # Assignment
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)

    # Task properties
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')

    # Dates and time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Additional tracking
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                         help_text='Estimated hours to complete')
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text='Actual hours spent')

    # Tags and categorization
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')

    # Reminders
    send_reminder = models.BooleanField(default=False)
    reminder_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('task_management:task_detail', kwargs={'pk': self.pk})

    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False

    def get_priority_color(self):
        """Return color based on priority"""
        colors = {
            'low': '#2ecc71',
            'medium': '#f39c12',
            'high': '#e74c3c',
            'urgent': '#c0392b',
        }
        return colors.get(self.priority, '#95a5a6')

    def get_status_color(self):
        """Return color based on status"""
        colors = {
            'todo': '#95a5a6',
            'in_progress': '#3498db',
            'in_review': '#9b59b6',
            'completed': '#27ae60',
            'blocked': '#e74c3c',
            'cancelled': '#7f8c8d',
        }
        return colors.get(self.status, '#95a5a6')

    def get_assigned_users_display(self):
        """Return comma-separated list of assigned users"""
        return ', '.join([user.username for user in self.assigned_to.all()])

    def mark_complete(self):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class TaskComment(models.Model):
    """Comments and updates on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Comment types
    is_system_message = models.BooleanField(default=False,
                                           help_text='System-generated message (e.g., status change)')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"


class TaskAttachment(models.Model):
    """File attachments for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='task_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.filename} - {self.task.title}"

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class TaskLabel(models.Model):
    """Custom labels for tasks"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3498db')
    description = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TaskActivity(models.Model):
    """Track all task activity for audit trail"""
    ACTIVITY_TYPES = [
        ('created', 'Task Created'),
        ('updated', 'Task Updated'),
        ('assigned', 'User Assigned'),
        ('unassigned', 'User Unassigned'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('commented', 'Comment Added'),
        ('attachment_added', 'Attachment Added'),
        ('completed', 'Task Completed'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional old/new values for tracking changes
    old_value = models.CharField(max_length=500, blank=True)
    new_value = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Task activities'

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.task.title}"
