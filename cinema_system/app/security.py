from itsdangerous import URLSafeTimedSerializer


def generate_token(user_id, role, secret_key):
    """Issue a signed token compatible with the auth middleware."""
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps({
        'user_id': str(user_id),
        'role': str(role).upper(),
    })
