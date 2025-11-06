from rest_framework_simplejwt.views import TokenObtainPairView
from .jwt_serializers import WalletTokenObtainPairSerializer


class WalletTokenObtainPairView(TokenObtainPairView):
    serializer_class = WalletTokenObtainPairSerializer
