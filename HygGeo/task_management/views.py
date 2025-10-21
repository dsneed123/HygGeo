from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Project, Task, TaskComment, TaskActivity
from .forms import ProjectForm, TaskForm, TaskCommentForm


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_staff


@login_required
@user_passes_test(is_admin, login_url='/')
def task_dashboard(request):
    """Main dashboard for task management - Admin only"""
    # Get all projects and tasks (admin access)
    projects = Project.objects.all()
    my_tasks = Task.objects.all()

    # Task statistics
    total_tasks = my_tasks.count()
    pending_tasks = my_tasks.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks = my_tasks.filter(status='completed').count()
    overdue_tasks = my_tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress', 'blocked']
    ).count()

    # Task counts by status for charts
    todo_tasks = my_tasks.filter(status='todo').count()
    in_progress_tasks = my_tasks.filter(status='in_progress').count()
    in_review_tasks = my_tasks.filter(status='in_review').count()
    blocked_tasks = my_tasks.filter(status='blocked').count()

    # Task counts by priority
    low_priority_tasks = my_tasks.filter(priority='low').count()
    medium_priority_tasks = my_tasks.filter(priority='medium').count()
    high_priority_tasks = my_tasks.filter(priority='high').count()
    urgent_priority_tasks = my_tasks.filter(priority='urgent').count()

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
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'in_review_tasks': in_review_tasks,
        'blocked_tasks': blocked_tasks,
        'low_priority_tasks': low_priority_tasks,
        'medium_priority_tasks': medium_priority_tasks,
        'high_priority_tasks': high_priority_tasks,
        'urgent_priority_tasks': urgent_priority_tasks,
        'recent_tasks': recent_tasks,
        'upcoming_deadlines': upcoming_deadlines,
    }

    return render(request, 'task_management/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def calendar_view(request):
    """Calendar view for tasks - Admin only"""
    # Get filter parameters
    project_id = request.GET.get('project')
    status = request.GET.get('status')

    # Get all tasks and projects (admin access)
    tasks = Task.objects.all()
    projects = Project.objects.all()

    # Apply filters
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if status:
        tasks = tasks.filter(status=status)

    context = {
        'tasks': tasks,
        'projects': projects,
        'selected_project': project_id,
        'selected_status': status,
    }

    return render(request, 'task_management/calendar.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def calendar_events_api(request):
    """API endpoint for calendar events - Admin only"""
    # Get all tasks (admin access)
    tasks = Task.objects.all()

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
@user_passes_test(is_admin, login_url='/')
def kanban_view(request):
    """Kanban board view - Admin only"""
    # Get filter parameters
    project_id = request.GET.get('project')
    priority = request.GET.get('priority')
    assigned_to = request.GET.get('assigned_to')

    # Get all tasks and projects (admin access)
    tasks = Task.objects.all()
    projects = Project.objects.all()

    # Get all admin users for filtering
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_staff=True)

    # Apply filters
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if priority:
        tasks = tasks.filter(priority=priority)
    if assigned_to:
        tasks = tasks.filter(assigned_to=assigned_to)

    # Group tasks by status
    todo_tasks = tasks.filter(status='todo')
    in_progress_tasks = tasks.filter(status='in_progress')
    in_review_tasks = tasks.filter(status='in_review')
    completed_tasks = tasks.filter(status='completed')
    blocked_tasks = tasks.filter(status='blocked')

    context = {
        'projects': projects,
        'users': users,
        'selected_project': project_id,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'in_review_tasks': in_review_tasks,
        'completed_tasks': completed_tasks,
        'blocked_tasks': blocked_tasks,
    }

    return render(request, 'task_management/kanban.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def task_list(request):
    """List all tasks with filters - Admin only"""
    # Get all tasks and projects (admin access)
    tasks = Task.objects.all()
    projects = Project.objects.all()

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
@user_passes_test(is_admin, login_url='/')
def task_detail(request, pk):
    """Task detail view - Admin only"""
    task = get_object_or_404(Task, pk=pk)

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
@user_passes_test(is_admin, login_url='/')
def task_create(request):
    """Create new task - Admin only"""
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
@user_passes_test(is_admin, login_url='/')
def task_edit(request, pk):
    """Edit existing task - Admin only"""
    task = get_object_or_404(Task, pk=pk)

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
@user_passes_test(is_admin, login_url='/')
def task_delete(request, pk):
    """Delete task - Admin only"""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_management:task_list')

    context = {'task': task}
    return render(request, 'task_management/task_confirm_delete.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def task_toggle_complete(request, pk):
    """Quick toggle task completion status - Admin only"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    task = get_object_or_404(Task, pk=pk)

    # Toggle status
    if task.status == 'completed':
        task.status = 'todo'
        task.completed_at = None
        message = f"{request.user.username} marked task as incomplete"
    else:
        task.status = 'completed'
        task.completed_at = timezone.now()
        message = f"{request.user.username} completed this task"

    task.save()

    # Log activity
    TaskActivity.objects.create(
        task=task,
        user=request.user,
        activity_type='status_changed',
        description=message
    )

    return JsonResponse({
        'success': True,
        'status': task.status,
        'completed': task.status == 'completed'
    })


@login_required
@user_passes_test(is_admin, login_url='/')
def project_list(request):
    """List all projects - Admin only"""
    # Get all projects (admin access)
    projects = Project.objects.all()

    # Apply filters
    status = request.GET.get('status')
    sort = request.GET.get('sort', '-created_at')

    if status:
        projects = projects.filter(status=status)

    # Add task counts
    projects = projects.annotate(task_count=Count('tasks'))

    # Apply sorting
    if sort:
        projects = projects.order_by(sort)

    context = {'projects': projects}
    return render(request, 'task_management/project_list.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def project_detail(request, slug):
    """Project detail view - Admin only"""
    project = get_object_or_404(Project, slug=slug)

    tasks = project.tasks.all()

    # Task statistics by status
    todo_count = tasks.filter(status='todo').count()
    in_progress_count = tasks.filter(status='in_progress').count()
    in_review_count = tasks.filter(status='in_review').count()
    completed_count = tasks.filter(status='completed').count()
    blocked_count = tasks.filter(status='blocked').count()
    total_tasks = tasks.count()

    context = {
        'project': project,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'in_review_count': in_review_count,
        'completed_count': completed_count,
        'blocked_count': blocked_count,
    }

    return render(request, 'task_management/project_detail.html', context)


@login_required
@user_passes_test(is_admin, login_url='/')
def project_create(request):
    """Create new project - Admin only"""
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
@user_passes_test(is_admin, login_url='/')
def project_edit(request, slug):
    """Edit existing project - Admin only"""
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
