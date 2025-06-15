import json
import stripe
import razorpay
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.utils import timezone

from courses.models import Course, Enrollment
from .models import Payment, Coupon, CouponUsage

# Initialize payment gateways
stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except:
    razorpay_client = None

@login_required
def checkout(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    
    # Check if already enrolled and paid
    enrollment = Enrollment.objects.filter(user=request.user, course=course)
    if enrollment.exists() and enrollment.first().is_paid:
        messages.info(request, 'You are already enrolled in this course')
        return redirect('course_learn', slug=course_slug)
    
    # Get payment amount and apply discounts
    amount = course.get_actual_price()
    discount_amount = Decimal('0.00')
    coupon_code = request.GET.get('coupon')
    applied_coupon = None
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount_amount = (Decimal(coupon.discount_percentage) / Decimal('100')) * amount
                amount = amount - discount_amount
                applied_coupon = coupon
            else:
                messages.warning(request, 'This coupon is invalid or expired')
        except Coupon.DoesNotExist:
            messages.warning(request, 'Invalid coupon code')
    
    context = {
        'course': course,
        'amount': amount,
        'original_amount': course.get_actual_price(),
        'discount_amount': discount_amount,
        'applied_coupon': applied_coupon,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    
    return render(request, 'payments/checkout.html', context)

@login_required
def apply_coupon(request, course_slug):
    coupon_code = request.GET.get('coupon')
    if not coupon_code:
        return JsonResponse({'success': False, 'message': 'No coupon code provided'})
    
    course = get_object_or_404(Course, slug=course_slug)
    amount = course.get_actual_price()
    
    try:
        coupon = Coupon.objects.get(code=coupon_code)
        if coupon.is_valid():
            discount_amount = (Decimal(coupon.discount_percentage) / Decimal('100')) * amount
            new_amount = amount - discount_amount
            
            return JsonResponse({
                'success': True,
                'discount_amount': str(discount_amount),
                'new_amount': str(new_amount),
                'message': f'Coupon applied: {coupon.discount_percentage}% off'
            })
        else:
            return JsonResponse({'success': False, 'message': 'This coupon is invalid or expired'})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

@login_required
def create_stripe_session(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    
    amount = course.get_actual_price()
    discount_amount = Decimal('0.00')
    coupon_code = request.GET.get('coupon')
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount_amount = (Decimal(coupon.discount_percentage) / Decimal('100')) * amount
                amount = amount - discount_amount
        except Coupon.DoesNotExist:
            pass
    
    success_url = request.build_absolute_uri(
        reverse('payment_success', kwargs={'course_slug': course_slug})
    )
    cancel_url = request.build_absolute_uri(
        reverse('payment_cancel', kwargs={'course_slug': course_slug})
    )
    
    # Create Stripe checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                    },
                    'unit_amount': int(amount * 100),  # convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'course_id': course.id,
                'user_id': request.user.id,
                'coupon_code': coupon_code if coupon_code else '',
                'discount_amount': str(discount_amount),
            }
        )
        
        # Create a pending payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            payment_id=session.id,
            amount=amount,
            currency='usd',
            status='pending',
            gateway='stripe',
            discount_applied=bool(coupon_code),
            discount_amount=discount_amount,
        )
        
        return JsonResponse({'id': session.id})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def create_razorpay_order(request, course_slug):
    if not razorpay_client:
        return JsonResponse({'error': 'Razorpay not configured'}, status=400)
    
    course = get_object_or_404(Course, slug=course_slug)
    
    amount = course.get_actual_price()
    discount_amount = Decimal('0.00')
    coupon_code = request.GET.get('coupon')
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount_amount = (Decimal(coupon.discount_percentage) / Decimal('100')) * amount
                amount = amount - discount_amount
        except Coupon.DoesNotExist:
            pass
    
    # Create Razorpay order
    try:
        razorpay_amount = int(amount * 100)  # convert to paisa
        razorpay_order = razorpay_client.order.create({
            'amount': razorpay_amount,
            'currency': 'INR',
            'notes': {
                'course_id': str(course.id),
                'user_id': str(request.user.id),
                'coupon_code': coupon_code if coupon_code else '',
                'discount_amount': str(discount_amount),
            }
        })
        
        # Create a pending payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            payment_id='pending',  # temporary
            order_id=razorpay_order['id'],
            amount=amount,
            currency='inr',
            status='pending',
            gateway='razorpay',
            discount_applied=bool(coupon_code),
            discount_amount=discount_amount,
        )
        
        return JsonResponse({
            'id': razorpay_order['id'],
            'amount': razorpay_amount,
            'currency': 'INR',
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@login_required
def payment_success(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    session_id = request.GET.get('session_id')
    payment_id = request.GET.get('razorpay_payment_id')
    
    if session_id:  # Stripe
        try:
            payment = Payment.objects.get(payment_id=session_id)
            
            # Verify with Stripe API
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                payment.status = 'completed'
                payment.save()
                
                # Create or update enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'is_paid': True, 'payment_id': session_id}
                )
                
                if not created:
                    enrollment.is_paid = True
                    enrollment.payment_id = session_id
                    enrollment.save()
                
                # Process coupon usage
                if payment.discount_applied and session.metadata.get('coupon_code'):
                    try:
                        coupon = Coupon.objects.get(code=session.metadata.get('coupon_code'))
                        coupon.used_count += 1
                        coupon.save()
                        
                        CouponUsage.objects.create(
                            coupon=coupon,
                            user=request.user,
                            payment=payment
                        )
                    except Coupon.DoesNotExist:
                        pass
                
                messages.success(request, 'Payment successful! You are now enrolled in the course.')
                return redirect('course_learn', slug=course_slug)
            else:
                messages.error(request, 'Payment verification failed. Please contact support.')
                return redirect('checkout', course_slug=course_slug)
        
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found. Please contact support.')
            return redirect('checkout', course_slug=course_slug)
        
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('checkout', course_slug=course_slug)
    
    elif payment_id:  # Razorpay
        try:
            order_id = request.GET.get('razorpay_order_id')
            signature = request.GET.get('razorpay_signature')
            payment = Payment.objects.get(order_id=order_id)
            
            # Verify with Razorpay API
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            if razorpay_client.utility.verify_payment_signature(params_dict):
                payment.payment_id = payment_id
                payment.status = 'completed'
                payment.save()
                
                # Create or update enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'is_paid': True, 'payment_id': payment_id}
                )
                
                if not created:
                    enrollment.is_paid = True
                    enrollment.payment_id = payment_id
                    enrollment.save()
                
                # Process coupon usage if applicable
                if payment.discount_applied:
                    notes = razorpay_client.order.fetch(order_id)['notes']
                    if notes.get('coupon_code'):
                        try:
                            coupon = Coupon.objects.get(code=notes.get('coupon_code'))
                            coupon.used_count += 1
                            coupon.save()
                            
                            CouponUsage.objects.create(
                                coupon=coupon,
                                user=request.user,
                                payment=payment
                            )
                        except Coupon.DoesNotExist:
                            pass
                
                messages.success(request, 'Payment successful! You are now enrolled in the course.')
                return redirect('course_learn', slug=course_slug)
            else:
                messages.error(request, 'Payment verification failed. Please contact support.')
                return redirect('checkout', course_slug=course_slug)
        
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found. Please contact support.')
            return redirect('checkout', course_slug=course_slug)
        
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('checkout', course_slug=course_slug)
    
    else:
        messages.error(request, 'Invalid payment session')
        return redirect('checkout', course_slug=course_slug)

@login_required
def payment_cancel(request, course_slug):
    messages.warning(request, 'Your payment was cancelled')
    return redirect('checkout', course_slug=course_slug)

@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_history.html', {'payments': payments})