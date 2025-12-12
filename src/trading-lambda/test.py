from methods.capture_account_summary import capture_account_summary
from methods.update_contracts_table import update_contracts_table


def test_update_contracts_table():
    update_contracts_table(
        {
            "contracts_details": {
                "underlying_symbol": "SPX",
                "underlying_type": "index",
                "exchange": "SMART",
            }
        }
    )


def test_capture_account_summary():
    response = capture_account_summary({})
    print(response)


if __name__ == "__main__":
    # test_update_contracts_table()
    test_capture_account_summary()
