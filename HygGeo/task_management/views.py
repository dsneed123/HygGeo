from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Project, Task, TaskComment, TaskActivity
from .forms import ProjectForm, TaskForm, TaskCommentForm


def is_staff_or_team_member(user):
    """Check if user is staff or team member of any project"""
    return user.is_staff or Project.objects.filter(team_members=user).exists()


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_dashboard(request):
    """Main dashboard for task management"""
    user = request.user

    # Get user's projects
    if user.is_staff:
        projects = Project.objects.all()
        my_tasks = Task.objects.all()
    else:
        projects = Project.objects.filter(Q(owner=user) | Q(team_members=user)).distinct()
        my_tasks = Task.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()

    # Task statistics
    total_tasks = my_tasks.count()
    pending_tasks = my_tasks.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks = my_tasks.filter(status='completed').count()
    overdue_tasks = my_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress', 'blocked']
    ).count()

    # Recent tasks
    recent_tasks = my_tasks.order_by('-created_at')[:5]

    # Upcoming deadlines
    upcoming_deadlines = my_tasks.filter(
        due_date__gte=timezone.now(),
        status__in=['todo', 'in_progress']
    ).order_by('due_date')[:5]

    context = {
        'projects': projects,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'upcoming_deadlines': upcoming_deadlines,
    }

    return render(request, 'task_management/dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def calendar_view(request):
    """Calendar view for tasks"""
    user = request.user

    # Get filter parameters
    project_id = request.GET.get('project')
    status = request.GET.get('status')

    # Get tasks based on user permissions
    if user.is_staff:
        tasks = Task.objects.all()
        projects = Project.objects.all()
    else:
        tasks = Task.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()
        projects = Project.objects.filter(Q(owner=user) | Q(team_members=user)).distinct()

    # Apply filters
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if status:
        tasks = tasks.filter(status=status)

    context = {
        'projects': projects,
        'selected_project': project_id,
        'selected_status': status,
    }

    return render(request, 'task_management/calendar.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def calendar_events_api(request):
    """API endpoint for calendar events"""
    user = request.user

    # Get tasks based on user permissions
    if user.is_staff:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()

    # Apply filters
    project_id = request.GET.get('project')
    status = request.GET.get('status')

    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if status:
        tasks = tasks.filter(status=status)

    # Build events for FullCalendar
    events = []
    for task in tasks:
        event = {
            'id': task.id,
            'title': task.title,
            'start': task.start_date.isoformat() if task.start_date else task.created_at.isoformat(),
            'end': task.due_date.isoformat() if task.due_date else None,
            'backgroundColor': task.get_status_color(),
            'borderColor': task.get_priority_color(),
            'url': f'/task-management/tasks/{task.id}/',
            'extendedProps': {
                'priority': task.priority,
                'status': task.status,
                'project': task.project.name if task.project else 'No Project',
            }
        }
        events.append(event)

    return JsonResponse(events, safe=False)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def kanban_view(request):
    """Kanban board view"""
    user = request.user

    # Get filter parameters
    project_id = request.GET.get('project')

    # Get tasks based on user permissions
    if user.is_staff:
        tasks = Task.objects.all()
        projects = Project.objects.all()
    else:
        tasks = Task.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()
        projects = Project.objects.filter(Q(owner=user) | Q(team_members=user)).distinct()

    # Apply project filter
    if project_id:
        tasks = tasks.filter(project_id=project_id)

    # Group tasks by status
    todo_tasks = tasks.filter(status='todo')
    in_progress_tasks = tasks.filter(status='in_progress')
    in_review_tasks = tasks.filter(status='in_review')
    completed_tasks = tasks.filter(status='completed')
    blocked_tasks = tasks.filter(status='blocked')

    context = {
        'projects': projects,
        'selected_project': project_id,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'in_review_tasks': in_review_tasks,
        'completed_tasks': completed_tasks,
        'blocked_tasks': blocked_tasks,
    }

    return render(request, 'task_management/kanban.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_list(request):
    """List all tasks with filters"""
    user = request.user

    # Get tasks based on user permissions
    if user.is_staff:
        tasks = Task.objects.all()
        projects = Project.objects.all()
    else:
        tasks = Task.objects.filter(Q(created_by=user) | Q(assigned_to=user)).distinct()
        projects = Project.objects.filter(Q(owner=user) | Q(team_members=user)).distinct()

    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    project_id = request.GET.get('project')
    search = request.GET.get('search')

    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if search:
        tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))

    tasks = tasks.order_by('-created_at')

    context = {
        'tasks': tasks,
        'projects': projects,
        'selected_status': status,
        'selected_priority': priority,
        'selected_project': project_id,
        'search_query': search,
    }

    return render(request, 'task_management/task_list.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_detail(request, pk):
    """Task detail view"""
    task = get_object_or_404(Task, pk=pk)

    # Check permissions
    user = request.user
    if not user.is_staff:
        if task.created_by != user and user not in task.assigned_to.all():
            messages.error(request, "You don't have permission to view this task.")
            return redirect('task_management:task_list')

    # Handle comment submission
    if request.method == 'POST':
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='commented',
                description=f"{request.user.username} added a comment"
            )

            messages.success(request, 'Comment added successfully.')
            return redirect('task_management:task_detail', pk=task.pk)
    else:
        comment_form = TaskCommentForm()

    context = {
        'task': task,
        'comment_form': comment_form,
        'activities': task.activities.all()[:20],
    }

    return render(request, 'task_management/task_detail.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_create(request):
    """Create new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save many-to-many relationships

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='created',
                description=f"{request.user.username} created this task"
            )

            messages.success(request, 'Task created successfully.')
            return redirect('task_management:task_detail', pk=task.pk)
    else:
        form = TaskForm(user=request.user)

    context = {'form': form, 'action': 'Create'}
    return render(request, 'task_management/task_form.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_edit(request, pk):
    """Edit existing task"""
    task = get_object_or_404(Task, pk=pk)

    # Check permissions
    if not request.user.is_staff and task.created_by != request.user:
        messages.error(request, "You don't have permission to edit this task.")
        return redirect('task_management:task_detail', pk=task.pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save()

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='updated',
                description=f"{request.user.username} updated this task"
            )

            messages.success(request, 'Task updated successfully.')
            return redirect('task_management:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)

    context = {'form': form, 'task': task, 'action': 'Edit'}
    return render(request, 'task_management/task_form.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def task_delete(request, pk):
    """Delete task"""
    task = get_object_or_404(Task, pk=pk)

    # Check permissions
    if not request.user.is_staff and task.created_by != request.user:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('task_management:task_detail', pk=task.pk)

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_management:task_list')

    context = {'task': task}
    return render(request, 'task_management/task_confirm_delete.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def project_list(request):
    """List all projects"""
    user = request.user

    if user.is_staff:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(Q(owner=user) | Q(team_members=user)).distinct()

    # Add task counts
    projects = projects.annotate(task_count=Count('tasks'))

    context = {'projects': projects}
    return render(request, 'task_management/project_list.html', context)


@login_required
@user_passes_test(is_staff_or_team_member, login_url='/')
def project_detail(request, slug):
    """Project detail view"""
    project = get_object_or_404(Project, slug=slug)

    # Check permissions
    user = request.user
    if not user.is_staff:
        if project.owner != user and user not in project.team_members.all():
            messages.error(request, "You don't have permission to view this project.")
            return redirect('task_management:project_list')

    tasks = project.tasks.all()

    # Task statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    context = {
        'project': project,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress': progress,
    }

    return render(request, 'task_management/project_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='/')
def project_create(request):
    """Create new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()

            messages.success(request, 'Project created successfully.')
            return redirect('task_management:project_detail', slug=project.slug)
    else:
        form = ProjectForm()

    context = {'form': form, 'action': 'Create'}
    return render(request, 'task_management/project_form.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='/')
def project_edit(request, slug):
    """Edit existing project"""
    project = get_object_or_404(Project, slug=slug)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('task_management:project_detail', slug=project.slug)
    else:
        form = ProjectForm(instance=project)

    context = {'form': form, 'project': project, 'action': 'Edit'}
    return render(request, 'task_management/project_form.html', context)
