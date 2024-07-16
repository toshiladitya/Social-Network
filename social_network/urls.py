from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from core.views import UserSignupViewSet, FriendRequestViewSet, LoginAPIView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'signup', UserSignupViewSet, basename='user_signup')
router.register(r'friend-requests', FriendRequestViewSet, basename='friend_request')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('', include(router.urls)),
]
