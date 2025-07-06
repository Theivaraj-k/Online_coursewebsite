from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Avg, Q
from django.contrib import messages

from .models import Course, Module, Content, Enrollment, ContentProgress, Review, Category
from .forms import (CourseForm, ModuleForm, TextContentForm, VideoContentForm, 
                   PDFContentForm, ReviewForm)

# Course List Views
class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True)
        category_slug = self.kwargs.get('category_slug')
        search_query = self.request.GET.get('search')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        return context


# Course & Module Management (Instructor only)

class InstructorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user == self.get_object().instructor

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

class CourseUpdateView(InstructorRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'

class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('my_courses')

@login_required
def course_dashboard(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to access this page")
    
    enrollments = course.enrollment_set.filter(is_paid=True).order_by('-enrolled_at')
    modules = course.get_modules()
    
    context = {
        'course': course,
        'enrollments': enrollments,
        'modules': modules,
    }
    
    return render(request, 'courses/course_dashboard.html', context)

# Module Views
@login_required
def add_module(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, 'Module added successfully')
            return redirect('course_dashboard', slug=course_slug)
    else:
        form = ModuleForm()
    
    return render(request, 'courses/module_form.html', {
        'form': form,
        'course': course,
        'title': 'Add Module'
    })

@login_required
def update_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, 'Module updated successfully')
            return redirect('course_dashboard', slug=course_slug)
    else:
        form = ModuleForm(instance=module)
    
    return render(request, 'courses/module_form.html', {
        'form': form,
        'course': course,
        'module': module,
        'title': 'Update Module'
    })

@login_required
def delete_module(request, course_slug, module_id):
    course = get_object_or_404(Course, slug=course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        module.delete()
        messages.success(request, 'Module deleted successfully')
        return redirect('course_dashboard', slug=course_slug)
    
    return render(request, 'courses/module_confirm_delete.html', {
        'course': course,
        'module': module
    })

# Content Views
@login_required
def add_content(request, module_id, content_type):
    module = get_object_or_404(Module, id=module_id)
    course = module.course
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        if content_type == 'text':
            form = TextContentForm(request.POST)
        elif content_type == 'video':
            form = VideoContentForm(request.POST, request.FILES)
        elif content_type == 'pdf':
            form = PDFContentForm(request.POST, request.FILES)
        
        if form.is_valid():
            content = form.save(commit=False)
            content.module = module
            content.content_type = content_type
            content.save()
            messages.success(request, f'{content_type.capitalize()} content added successfully')
            return redirect('course_dashboard', slug=course.slug)
    else:
        if content_type == 'text':
            form = TextContentForm()
        elif content_type == 'video':
            form = VideoContentForm()
        elif content_type == 'pdf':
            form = PDFContentForm()
    
    context = {
        'form': form,
        'module': module,
        'course': course,
        'content_type': content_type,
        'title': f'Add {content_type.capitalize()} Content'
    }
    
    return render(request, 'courses/content_form.html', context)

@login_required
def update_content(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    module = content.module
    course = module.course
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        if content.content_type == 'text':
            form = TextContentForm(request.POST, instance=content)
        elif content.content_type == 'video':
            form = VideoContentForm(request.POST, request.FILES, instance=content)
        elif content.content_type == 'pdf':
            form = PDFContentForm(request.POST, request.FILES, instance=content)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Content updated successfully')
            return redirect('course_dashboard', slug=course.slug)
    else:
        if content.content_type == 'text':
            form = TextContentForm(instance=content)
        elif content.content_type == 'video':
            form = VideoContentForm(instance=content)
        elif content.content_type == 'pdf':
            form = PDFContentForm(instance=content)
    
    context = {
        'form': form,
        'content': content,
        'module': module,
        'course': course,
        'title': 'Update Content'
    }
    
    return render(request, 'courses/content_form.html', context)

@login_required
def delete_content(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    module = content.module
    course = module.course
    
    if request.user != course.instructor and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to perform this action")
    
    if request.method == 'POST':
        content.delete()
        messages.success(request, 'Content deleted successfully')
        return redirect('course_dashboard', slug=course.slug)
    
    return render(request, 'courses/content_confirm_delete.html', {
        'content': content,
        'module': module,
        'course': course
    })

# Learning Views
@login_required
def course_learn(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    # Check if user is enrolled
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=course, is_paid=True
    ).exists()
    
    if not is_enrolled:
        messages.warning(request, 'You need to enroll in this course first')
        return redirect('course_detail', slug=course.slug)
    
    modules = course.get_modules()
    
    # Get progress
    progress_data = {}
    for module in modules:
        module_progress = []
        for content in module.content_items.all():
            progress, created = ContentProgress.objects.get_or_create(
                user=request.user, content=content
            )
            module_progress.append({
                'content': content,
                'completed': progress.completed
            })
        progress_data[module.id] = module_progress
    
    # Calculate overall progress
    total_content = Content.objects.filter(module__course=course).count()
    completed_content = ContentProgress.objects.filter(
        user=request.user, content__module__course=course, completed=True
    ).count()
    
    overall_progress = 0
    if total_content > 0:
        overall_progress = int((completed_content / total_content) * 100)
    
    context = {
        'course': course,
        'modules': modules,
        'progress_data': progress_data,
        'overall_progress': overall_progress
    }
    
    return render(request, 'courses/course_learn.html', context)

@login_required
def content_detail(request, course_slug, content_id):
    course = get_object_or_404(Course, slug=course_slug)
    content = get_object_or_404(Content, id=content_id, module__course=course)
    
    # Check if content is preview or user is enrolled
    is_preview = content.is_preview
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=course, is_paid=True
    ).exists()
    
    if not (is_preview or is_enrolled):
        messages.warning(request, 'You need to enroll in this course to access this content')
        return redirect('course_detail', slug=course_slug)
    
    # Mark as accessed
    progress, created = ContentProgress.objects.get_or_create(
        user=request.user, content=content
    )
    
    # Get next and previous content
    module = content.module
    all_modules = list(course.get_modules())
    current_module_index = all_modules.index(module)
    
    module_contents = list(module.get_content_items())
    current_content_index = module_contents.index(content)
    
    prev_content = None
    next_content = None
    
    # Check for previous content in current module
    if current_content_index > 0:
        prev_content = module_contents[current_content_index - 1]
    # Check previous module
    elif current_module_index > 0:
        prev_module = all_modules[current_module_index - 1]
        prev_module_contents = list(prev_module.get_content_items())
        if prev_module_contents:
            prev_content = prev_module_contents[-1]
    
    # Check for next content in current module
    if current_content_index < len(module_contents) - 1:
        next_content = module_contents[current_content_index + 1]
    # Check next module
    elif current_module_index < len(all_modules) - 1:
        next_module = all_modules[current_module_index + 1]
        next_module_contents = list(next_module.get_content_items())
        if next_module_contents:
            next_content = next_module_contents[0]
    
    context = {
        'course': course,
        'module': module,
        'content': content,
        'progress': progress,
        'prev_content': prev_content,
        'next_content': next_content,
    }
    
    return render(request, 'courses/content_detail.html', context)

@login_required
def mark_content_complete(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    
    # Check if user is enrolled
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=content.module.course, is_paid=True
    ).exists()
    
    if not is_enrolled:
        return JsonResponse({'status': 'error', 'message': 'Not enrolled'})
    
    progress, created = ContentProgress.objects.get_or_create(
        user=request.user, content=content
    )
    
    completed = request.POST.get('completed') == 'true'
    progress.completed = completed
    progress.save()
    
    # Calculate overall progress
    course = content.module.course
    total_content = Content.objects.filter(module__course=course).count()
    completed_content = ContentProgress.objects.filter(
        user=request.user, content__module__course=course, completed=True
    ).count()
    
    overall_progress = 0
    if total_content > 0:
        overall_progress = int((completed_content / total_content) * 100)
    
    return JsonResponse({
        'status': 'success', 
        'completed': completed,
        'overall_progress': overall_progress
    })

# Review
@login_required
def add_review(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if user is enrolled and has paid
    is_enrolled = Enrollment.objects.filter(
        user=request.user, course=course, is_paid=True
    ).exists()
    
    if not is_enrolled:
        messages.warning(request, 'You can only review courses you are enrolled in')
        return redirect('course_detail', slug=course_slug)
    
    # Check if user already reviewed
    existing_review = Review.objects.filter(user=request.user, course=course).first()
    
    if request.method == 'POST':
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
            review_action = 'updated'
        else:
            form = ReviewForm(request.POST)
            review_action = 'added'
        
        if form.is_valid():
            review = form.save(commit=False)
            if not existing_review:
                review.user = request.user
                review.course = course
            review.save()
            messages.success(request, f'Your review has been {review_action} successfully')
            return redirect('course_detail', slug=course_slug)
    
    return redirect('course_detail', slug=course_slug)


from django.views.generic import DetailView

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()

        # Get all modules for the course
        modules = course.modules.all()

        # Collect all content items (PDFs) from those modules
        pdf_count = 0
        for module in modules:
            pdf_count += module.content_items.filter(content_type='pdf').count()

        context['pdf_count'] = pdf_count
        return context
    
