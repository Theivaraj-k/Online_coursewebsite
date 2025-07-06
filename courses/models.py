from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instructor_courses')
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    students = models.ManyToManyField(User, through='Enrollment', related_name='enrolled_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_modules(self):
        return self.modules.order_by('order')

    def get_first_module(self):
        return self.modules.order_by('order').first()

    def get_student_count(self):
        return self.students.count()

    def get_actual_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def get_content_items(self):
        return self.content_items.order_by('order')

class Content(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('text', 'Text'),
        ('assignment', 'Assignment'),
    )

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='content_items')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    text_content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='course_videos/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='course_pdfs/', blank=True, null=True)
    is_preview = models.BooleanField(default=False)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"

class ContentProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'content']

    def __str__(self):
        return f"{self.user.username} - {self.content.title}"

class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username}'s review on {self.course.title}"
    


    from django.shortcuts import render
from django.views.generic import DetailView
from .models import Course

