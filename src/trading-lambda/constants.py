import os

# Only load .env file for local testing (safe to call in Lambda - will just do nothing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, that's okay - we're in Lambda
    pass


class Constants:
    LAMBDA_API_KEY_HEADER_NAME = "api-key"
    FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL")
    LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY")
    RDS_SECRET_NAME = "/quantecho/trading-cluster-secret-postgre"


constants = Constants()
