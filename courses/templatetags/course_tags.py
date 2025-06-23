from django import template
from courses.models import Category

register = template.Library()

@register.simple_tag
def get_all_categories():
    """Return all course categories"""
    return Category.objects.all()

@register.filter
def in_category(courses, category_slug):
    """Filter courses by category"""
    if not category_slug:
        return courses
    return courses.filter(category__slug=category_slug)

@register.simple_tag(takes_context=True)
def get_filtered_category_name(context, category_slug):
    """Get the name of the filtered category"""
    if not category_slug:
        return "All Courses"
    categories = context.get('categories', [])
    for category in categories:
        if category.slug == category_slug:
            return category.name
    return "Courses"


@register.filter
def filter_by_slug(categories, slug):
    """Filter categories by slug"""
    return [cat for cat in categories if cat.slug == slug]