import traceback

import requests
from constants import constants


def update_contracts_table(event):
    """
    event: {
        'contracts_details': {
            'underlying_symbol': 'SPX',
            'underlying_type': 'index',
            'exchange': 'SMART'/'CBOE'/'CME'
        }
    }
    """
    print(f"Updating contracts table: {event}")

    ## EC2 serving
    url = constants.FASTAPI_BASE_URL + "/data/update-contracts-table"

    contracts_details = event.get("contracts_details")
    if not contracts_details:
        raise ValueError("contracts_details is required")

    data = {
        "contracts_details": contracts_details,
    }

    try:
        requests.post(
            url,
            json=data,
            headers={constants.LAMBDA_API_KEY_HEADER_NAME: constants.LAMBDA_API_KEY},
        )
    except Exception as e:
        print(f"Error updating contracts table: {traceback.format_exc()}")
        raise e

    return {"message": "Contracts table updated"}
