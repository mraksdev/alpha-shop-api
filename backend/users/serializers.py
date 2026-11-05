from djoser.serializers import UserSerializer as DjoserUserSerializer


class UserSerializer(DjoserUserSerializer):
    """User serializer for djoser endpoints."""

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
        )
        read_only_fields = ('id', 'email')
