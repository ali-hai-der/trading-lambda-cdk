import requests
import traceback
import os

VALID_METHODS = ['update_contracts_table', 'capture_account_summary']
FASTAPI_BASE_URL = os.getenv('FASTAPI_BASE_URL')

def handler(event, context):

    method = event.get('method')

    if method not in VALID_METHODS:
        raise ValueError(f"Invalid method: {method}")
    
    if method == 'update_contracts_table':
        return update_contracts_table(event)
    elif method == 'capture_account_summary':
        return capture_account_summary(event)

def update_contracts_table(event):
    '''
    event: {
        'contracts_details': {
            'underlying_symbol': 'SPX',
            'underlying_type': 'index',
            'exchange': 'SMART'/'CBOE'/'CME'
        }
    }
    '''
    print(f"Updating contracts table: {event}")

    ## EC2 serving
    url = FASTAPI_BASE_URL + '/data/update-contracts-table'

    contracts_details = event.get('contracts_details')
    if not contracts_details:
        raise ValueError("contracts_details is required")

    try:
        requests.post(url, json=contracts_details)
    except Exception as e:
        print(f"Error updating contracts table: {traceback.format_exc()}")
        raise e
    
    return {'message': 'Contracts table updated'}

def capture_account_summary(event):
    
    account_number = event.get('account_number')
    
    url = FASTAPI_BASE_URL + '/account' + (f'?account_number={account_number}' if account_number else '')
    
    try:
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(f"Error capturing account summary: {response.text}")
        
        response_json = response.json()

        account_summary = response_json.get('account_summary') # noqa

        ## Update account summary in RDS
        
        
    except Exception:
        print(f"Error capturing account summary: {traceback.format_exc()}")
        raise
    