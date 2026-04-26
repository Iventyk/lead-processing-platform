from src.config.settings import settings
import jwt


def create_token():
    payload = {"id": 1}

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    print(token)


if __name__ == "__main__":
    create_token()
