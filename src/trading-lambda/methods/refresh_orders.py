import traceback

import aws.rds
import requests
from constants import constants


def refresh_orders(event):
    """ """
    print(f"Refreshing orders: {event}")

    url = constants.FASTAPI_BASE_URL + "/data/refresh-orders"

    try:
        aws.rds.execute("TRUNCATE TABLE orders")

    except Exception as e:
        print(f"Error truncating orders: {e}")
        return {
            "message": "Order refresh failed: Error truncating orders",
            "error": traceback.format_exc(),
        }

    try:
        requests.patch(url, headers={constants.LAMBDA_API_KEY_HEADER_NAME: constants.LAMBDA_API_KEY})
    except Exception as e:
        print(f"Error refreshing orders: {e}")
        return {
            "message": "Order refresh failed: Error refreshing orders",
            "error": traceback.format_exc(),
        }

    return {"message": "Orders refreshed"}
