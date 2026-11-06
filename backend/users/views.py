from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting for login attempts to prevent brute force attacks"""
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limiting for registration to prevent spam/bot attacks"""
    scope = 'register'


class RefreshRateThrottle(AnonRateThrottle):
    """Rate limiting for token refresh to prevent abuse"""
    scope = 'refresh'


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    JWT token view that sets tokens in HttpOnly cookies
    More secure than localStorage - prevents XSS attacks
    """
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Set access token in HttpOnly cookie
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,  # HTTPS only in production
                samesite='Lax',
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            )
            
            # Set refresh token in HttpOnly cookie
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            )
            
            # Remove tokens from response body (they're in cookies now)
            # Don't include user data here - frontend should call /api/auth/me/ after login
            response.data = {
                'detail': 'Successfully logged in'
            }
        
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Refresh JWT token from HttpOnly cookie
    """
    throttle_classes = [RefreshRateThrottle]
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Add refresh token to request data
        request.data['refresh'] = refresh_token
        
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                access_token = response.data.get('access')
                
                # Set new access token in cookie
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='Lax',
                    max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                )
                
                # If rotation is enabled, update refresh token cookie
                if 'refresh' in response.data:
                    refresh_token = response.data.get('refresh')
                    response.set_cookie(
                        key='refresh_token',
                        value=refresh_token,
                        httponly=True,
                        secure=not settings.DEBUG,
                        samesite='Lax',
                        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    )
                
                response.data = {'detail': 'Token refreshed successfully'}
            
            return response
            
        except (InvalidToken, TokenError) as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout by clearing HttpOnly cookies
    """
    response = Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    throttle_classes = [RegisterRateThrottle]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get current user info with subscription tier"""
    
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

