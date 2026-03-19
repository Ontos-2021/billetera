from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from .jwt_serializers import WalletTokenObtainPairSerializer


class WalletTokenObtainPairView(TokenObtainPairView):
    serializer_class = WalletTokenObtainPairSerializer
    permission_classes = [AllowAny]
