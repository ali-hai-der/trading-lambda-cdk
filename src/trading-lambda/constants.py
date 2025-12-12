import os

from dotenv import load_dotenv

# Load environment variables from .env file for local testing
load_dotenv()


class Constants:
    FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL")
    LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY")
    RDS_SECRET_NAME = "/quantecho/trading-cluster-secret-postgre"


constants = Constants()
