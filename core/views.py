from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from .models import User, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer, LoginSerializer, UserProfileSearchSerializer, FriendRequestListSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.utils.timezone import now
from datetime import timedelta


class UserSignupViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = User.objects.all()
        search_keyword = self.request.query_params.get('search', None)
        if search_keyword:
            queryset = queryset.filter(Q(email__iexact=search_keyword) | Q(username__icontains=search_keyword))
        return queryset
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'search':
            return UserProfileSearchSerializer
        return UserSerializer
    
    def get_queryset(self):
        if self.action == 'search':
            return User.objects.exclude(id=self.request.user.id)
        return User.objects.filter(id=self.request.user.id)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    @action(detail=False, methods=['get'])
    def search(self, request):
        queryset = self.get_queryset()
        search_query = request.query_params.get('search', '')
        if '@' in search_query:
            users = queryset.filter(email__iexact=search_query)
        else:
            users = queryset.filter(username__icontains=search_query)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class FriendRequestViewSet(viewsets.ModelViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    methods = ['post', 'get', 'patch']
    
    def get_serializer_class(self):
        if self.action == 'friends':
            return UserProfileSearchSerializer
        elif self.action == 'create':
            return FriendRequestSerializer
        return FriendRequestListSerializer
    
    def get_queryset(self):
        if self.action == 'request_pending':
            return self.queryset.filter(to_user=self.request.user, status='pending')
        return self.queryset

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(from_user=request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args):
        from_user = request.user
        to_user_id = request.data.get('to_user')
        existing_request = FriendRequest.objects.filter(from_user=from_user, to_user_id=to_user_id).first()
        if existing_request:
            return Response("A friend request from this user to the specified user already exists.", status=status.HTTP_400_BAD_REQUEST)
        
        now_minus_1_minute = now() - timedelta(minutes=1)
        last_4_requests = request.user.sent_requests.order_by('-created_at')[:4]
        if len(last_4_requests) > 0 and last_4_requests[0].created_at > now_minus_1_minute:
            return Response({"message": "You cannot send more than 3 requests within a minute."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(from_user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        status = request.data.get('status')
        if status not in ['accepted', 'rejected']:
            return Response({"message": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        if instance.to_user != request.user:
            return Response({"message": "You do not have permission to perform this action."}, status=status.HTTP_400_BAD_REQUEST)
        instance.status = status
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def friends(self, request):
        user = request.user
        friends = User.objects.filter(
            Q(received_requests__from_user=user, received_requests__status='accepted') |
            Q(sent_requests__to_user=user, sent_requests__status='accepted')
        ).distinct()
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def request_pending(self, request):
        pending_requests = self.get_queryset()
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)

