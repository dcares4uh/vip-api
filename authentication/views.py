from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from customer.models import Customer
from vendors.models import Vendor

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Create corresponding profile based on is_vendor flag
            if user.is_vendor:
                # Create vendor profile with minimal data
                Vendor.objects.create(
                    user=user,
                    business_name=f"{user.first_name}'s Business",  # Default business name
                    full_address="",
                    address_area="",
                    state="",
                    country=""
                )
            else:
                # Create customer profile with minimal data
                Customer.objects.create(
                    user=user,
                    full_address="",
                    address_area="",
                    state="",
                    country=""
                )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            })
        except serializers.ValidationError as e:
            error_msg = str(e.detail['non_field_errors'][0]) if 'non_field_errors' in e.detail else str(e.detail)
            return Response(
                {"error": error_msg}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_login_status(self, user):
        if user.last_login is None:
            return "User has not logged in yet"
        return user.last_login

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "is_vendor": user.is_vendor,
            "is_staff": user.is_staff,
            "last_login": self.get_login_status(user),
            "is_active": user.is_active,
            "date_joined": user.date_joined
        })

class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # Generate new tokens after password change
            refresh = RefreshToken.for_user(request.user)
            return Response({
                "message": "Password changed successfully",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)