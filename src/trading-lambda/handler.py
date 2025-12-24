from methods.capture_account_summary import capture_account_summary
from methods.refresh_orders import refresh_orders
from methods.truncate_orders import truncate_orders
from methods.update_contracts_table import update_contracts_table

VALID_METHODS = [
    "update_contracts_table",
    "capture_account_summary",
    "refresh_orders",
    "truncate_orders",
]


def handler(event, context):
    """Lambda handler function - entry point for AWS Lambda."""
    method = event.get("method")

    if method not in VALID_METHODS:
        raise ValueError(f"Invalid method: {method}")

    if method == "update_contracts_table":
        return update_contracts_table(event)
    elif method == "capture_account_summary":
        return capture_account_summary(event)
    elif method == "refresh_orders":
        return refresh_orders(event)
    elif method == "truncate_orders":
        return truncate_orders(event)
