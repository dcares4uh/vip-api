from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import razorpay
import logging
from sales.models import Sales
from .models import RazorpayPayment, PaymentStatus

logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sale_id):
        """
        Initiates a payment by creating a Razorpay order and a Payment record.
        Returns details needed for the frontend to proceed with payment.
        """
        sale = get_object_or_404(Sales, id=sale_id)
        
        # Check if a payment already exists for this sale
        try:
            existing_payment = sale.razorpay_payment  # Access the Payment via the related_name
            return Response(
                {"error": "Payment already initiated for this sale"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RazorpayPayment.DoesNotExist:
            # No payment exists, proceed with initiation
            pass
        
        # Create Razorpay order
        order_amount = int(sale.final_price * 100)  # Convert to paise
        order_data = {
            'amount': order_amount,
            'currency': 'INR',
            'payment_capture': '1'  # Auto capture
        }
        
        try:
            razorpay_order = razorpay_client.order.create(data=order_data)
            
            # Create Payment record
            payment = RazorpayPayment.objects.create(
                sale=sale,
                amount=sale.final_price,
                razorpay_order_id=razorpay_order['id'],
                status=PaymentStatus.PENDING
            )
            
            response_data = {
                'sale_id': str(sale.id),
                'payment_id': str(payment.id),
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'order_id': razorpay_order['id'],
                'amount': order_amount,
                'callback_url': request.build_absolute_uri(f'/api/payments/callback/{payment.id}/'),
                'business_name': sale.vendor.business_name if sale.vendor else 'Admin'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error initiating payment for sale {sale_id}: {str(e)}")
            return Response(
                {"error": f"Failed to initiate payment: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class PaymentCallbackView(APIView):
    def post(self, request, payment_id):
        """
        Handles Razorpay payment callback, verifies payment signature,
        and updates Payment, Sale, and Number statuses.
        """
        payment = get_object_or_404(RazorpayPayment, id=payment_id)
        
        # Extract Razorpay parameters
        params_dict = {
            'razorpay_payment_id': request.data.get('razorpay_payment_id'),
            'razorpay_order_id': request.data.get('razorpay_order_id'),
            'razorpay_signature': request.data.get('razorpay_signature')
        }
        
        # Validate required parameters
        if not all(params_dict.values()):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Missing required Razorpay parameters"
            payment.save()
            logger.error(f"Missing Razorpay parameters for payment {payment_id}")
            return Response(
                {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'error': payment.failure_reason
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify payment signature
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Update payment details
            payment.razorpay_payment_id = params_dict['razorpay_payment_id']
            payment.razorpay_signature = params_dict['razorpay_signature']
            payment.status = PaymentStatus.COMPLETED
            payment.payment_method = razorpay_client.payment.fetch(
                params_dict['razorpay_payment_id']
            ).get('method')
            payment.save()
            
            # Update sale and number status
            payment.sale.status = 'completed'
            payment.sale.number.is_sold = True
            payment.sale.number.status = 'SOLD'
            payment.sale.save()
            payment.sale.number.save()
            
            return Response(
                {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'message': 'Payment completed successfully'
                },
                status=status.HTTP_200_OK
            )
            
        except razorpay.errors.SignatureVerificationError:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Signature verification failed"
            payment.save()
            logger.error(f"Payment signature verification failed for payment {payment_id}")
            return Response(
                {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'error': payment.failure_reason
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            payment.save()
            logger.error(f"Payment processing error for payment {payment_id}: {str(e)}")
            return Response(
                {
                    'payment_id': str(payment.id),
                    'status': payment.status,
                    'error': payment.failure_reason
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id):
        """
        Retrieves the status and details of a specific payment.
        """
        payment = get_object_or_404(RazorpayPayment, id=payment_id)
        response_data = {
            'payment_id': str(payment.id),
            'sale_id': str(payment.sale.id),
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'created_at': payment.created_at,
            'updated_at': payment.updated_at,
            'failure_reason': payment.failure_reason
        }
        return Response(response_data, status=status.HTTP_200_OK)