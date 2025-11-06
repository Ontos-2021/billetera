from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class WalletTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = getattr(user, 'email', '')
        token['role'] = getattr(user, 'role', 'user') if hasattr(user, 'role') else 'user'
        token['kyc_level'] = getattr(user, 'kyc_level', 0) if hasattr(user, 'kyc_level') else 0
        return token
