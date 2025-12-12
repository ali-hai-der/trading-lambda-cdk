import traceback

import aws.rds


def truncate_orders(event):
    """ """
    print(f"Truncating orders: {event}")

    try:
        aws.rds.execute("TRUNCATE TABLE orders")
    except Exception as e:
        print(f"Error truncating orders: {e}")
        return {"message": "Error truncating orders", "error": traceback.format_exc()}

    return {"message": "Orders truncated"}
