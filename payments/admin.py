from django.contrib import admin
from .models import Payment, Coupon, CouponUsage

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'amount', 'status', 'gateway', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('user__username', 'course__title', 'payment_id', 'order_id')
    readonly_fields = ('payment_id', 'order_id', 'created_at', 'updated_at')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_to', 'active', 'used_count')
    list_filter = ('active', 'valid_from', 'valid_to')
    search_fields = ('code',)
    list_editable = ('active',)

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'payment', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'user__username')