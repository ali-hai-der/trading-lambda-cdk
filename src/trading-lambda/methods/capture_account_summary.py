import traceback

import aws.rds
import requests
from constants import constants


def parse_account_summary(account_summary):
    lookup_tags = {
        "AvailableFunds": "available_funds",
        "NetLiquidation": "net_liquidation",
        "ExcessLiquidity": "excess_liquidity",
        "MaintMarginReq": "maintenance_margin",
    }

    account_summary_data = {}

    for row in account_summary:
        tag = row.get("tag")

        if tag in lookup_tags:
            value = row.get("value")
            if value:
                account_summary_data[lookup_tags[tag]] = float(value)

    return account_summary_data


def capture_account_summary(event):
    account_number = event.get("account_number")

    url = (
        constants.FASTAPI_BASE_URL
        + "/account"
        + (f"?account_number={account_number}" if account_number else "")
    )

    try:
        response = requests.get(
            url,
            headers={constants.LAMBDA_API_KEY_HEADER_NAME: constants.LAMBDA_API_KEY},
        )

        if response.status_code != 200:
            raise ValueError(f"Error capturing account summary: {response.text}")

        response_json = response.json()

        account_summary = response_json.get("account_summary")  # noqa
        spx_price = aws.rds.get_index_price("SPX")
        vix_price = aws.rds.get_index_price("VIX")
        account_history_snapshot = parse_account_summary(account_summary)

        if (
            account_summary
            and len(account_summary) > 0
            and account_summary[0].get("account")
        ):
            account_number = account_summary[0].get("account")
            account_history_snapshot.update({"account": account_number})
        else:
            return {
                "status": 202,
                "message": "No account summary data found",
                "account_summary": account_summary,
            }

        unrealized_pl = aws.rds.get_current_unrealized_pl(account_number)

        account_history_snapshot.update(
            {
                "spx": float(spx_price),
                "vix": float(vix_price),
                "unrealized_pl": unrealized_pl,
            }
        )

        gross_positions, unique_contracts = (
            aws.rds.get_gross_positions_and_unique_contracts(account_number)
        )

        account_history_snapshot.update(
            {
                "gross_positions": int(gross_positions or 0),
                "unique_contracts": int(unique_contracts or 0),
            }
        )

        aws.rds.insert_or_update(
            "account_history",
            account_history_snapshot,
            account_history_snapshot.keys(),
            statement_type="INSERT",
        )

        return {
            "status": 200,
            "message": "Account summary captured successfully",
            "account_summary": account_history_snapshot,
        }

    except Exception:
        print(f"Error capturing account summary: {traceback.format_exc()}")
        return {
            "status": 500,
            "message": "Error capturing account summary: \n" + traceback.format_exc(),
        }
