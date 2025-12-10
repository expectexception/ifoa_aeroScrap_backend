import os
from types import SimpleNamespace
from ninja.security import HttpBearer
from ninja.errors import HttpError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuth(HttpBearer):
    """JWT authentication for django-ninja using djangorestframework-simplejwt.
    
    This is the primary authentication method for all API endpoints.
    Users must login to get JWT tokens and include them in requests.
    """

    def authenticate(self, request, token):
        # Allow an admin API key for ingestion/automation flows.
        api_key = os.environ.get('ADMIN_API_KEY')
        if api_key and token == api_key:
            user_obj = SimpleNamespace(is_active=True, username='admin_api_key')
            request.user = user_obj
            return user_obj

        jwt_authenticator = JWTAuthentication()
        try:
            # Validate the token and get the user
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token)
            if user and user.is_active:
                # Attach user to request for use in endpoints
                request.user = user
                return user
            raise HttpError(401, 'Invalid or inactive user')
        except AuthenticationFailed as e:
            raise HttpError(401, str(e))
        except Exception as e:
            raise HttpError(401, 'Invalid token')
