from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<slug:course_slug>/', views.checkout, name='checkout'),
    path('apply-coupon/<slug:course_slug>/', views.apply_coupon, name='apply_coupon'),
    path('create-stripe-session/<slug:course_slug>/', views.create_stripe_session, name='create_stripe_session'),
    path('create-razorpay-order/<slug:course_slug>/', views.create_razorpay_order, name='create_razorpay_order'),
    path('success/<slug:course_slug>/', views.payment_success, name='payment_success'),
    path('cancel/<slug:course_slug>/', views.payment_cancel, name='payment_cancel'),
    path('history/', views.payment_history, name='payment_history'),
]