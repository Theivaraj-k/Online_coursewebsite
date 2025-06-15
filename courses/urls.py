from django.urls import path
from . import views

urlpatterns = [
    # Course list and detail
    path('', views.CourseListView.as_view(), name='course_list'),
    path('category/<slug:category_slug>/', views.CourseListView.as_view(), name='course_by_category'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    
    # Course management (instructor)
    path('create/new/', views.CourseCreateView.as_view(), name='course_create'),
    path('<slug:slug>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    path('<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('<slug:slug>/dashboard/', views.course_dashboard, name='course_dashboard'),
    
    # Module management
    path('<slug:course_slug>/modules/add/', views.add_module, name='add_module'),
    path('<slug:course_slug>/modules/<int:module_id>/update/', views.update_module, name='update_module'),
    path('<slug:course_slug>/modules/<int:module_id>/delete/', views.delete_module, name='delete_module'),
    
    # Content management
    path('modules/<int:module_id>/content/<str:content_type>/add/', views.add_content, name='add_content'),
    path('content/<int:content_id>/update/', views.update_content, name='update_content'),
    path('content/<int:content_id>/delete/', views.delete_content, name='delete_content'),
    
    # Learning
    path('<slug:slug>/learn/', views.course_learn, name='course_learn'),
    path('<slug:course_slug>/content/<int:content_id>/', views.content_detail, name='content_detail'),
    path('content/<int:content_id>/complete/', views.mark_content_complete, name='mark_content_complete'),
    
    # Reviews
    path('<slug:course_slug>/review/', views.add_review, name='add_review'),
]