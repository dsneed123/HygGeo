from django.contrib import admin
from .models import Project, Task, TaskComment, TaskAttachment, TaskLabel, TaskActivity


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'progress_percentage', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['team_members']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to_list', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'tags']
    filter_horizontal = ['assigned_to']
    date_hierarchy = 'due_date'

    def assigned_to_list(self, obj):
        return ', '.join([user.username for user in obj.assigned_to.all()[:3]])
    assigned_to_list.short_description = 'Assigned To'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at', 'is_system_message']
    list_filter = ['is_system_message', 'created_at']
    search_fields = ['comment', 'task__title']


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'task', 'uploaded_by', 'uploaded_at', 'get_file_size_display']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'description']


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_by', 'created_at']
    search_fields = ['name', 'description']


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'activity_type', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['description', 'task__title']
