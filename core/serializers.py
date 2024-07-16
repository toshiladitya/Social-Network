from rest_framework import serializers
from .models import User, FriendRequest

class UserProfileSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(email=validated_data['email'],
                                        password=validated_data['password'],
                                        username=validated_data.get('username'))
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

class FriendRequestListSerializer(serializers.ModelSerializer):
    from_user = UserProfileSearchSerializer()
    to_user = UserProfileSearchSerializer()
    class Meta:
        model = FriendRequest
        fields = [
            'id',
            'from_user',
            'to_user',
            'status'
        ]


class FriendRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = FriendRequest
        fields = [
            'id',
            'from_user',
            'to_user',
            'status'
        ]
