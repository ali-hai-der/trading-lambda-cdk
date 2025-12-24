from aws.db_manager import RDSConnectionManager
from constants import constants

# Lazy-load RDS client to avoid connection attempts during module import
_rds_client = None


def _get_rds_client():
    """Get or create RDS client instance (lazy initialization)."""
    global _rds_client
    if _rds_client is None:
        _rds_client = RDSConnectionManager(constants.RDS_SECRET_NAME, database="ibkr")
    return _rds_client


def execute(query_text, params=None, fetch=True):
    rds_client = _get_rds_client()
    with rds_client:
        return rds_client.query(
            query_text, params=params, return_pandas=True, fetch=fetch
        )


symbol_to_contract_id = {"SPX": "416904", "VIX": "13455763"}


def get_index_price(index_symbol: str):
    if index_symbol not in symbol_to_contract_id:
        raise ValueError(f"Invalid index symbol, Not implemented: {index_symbol}")

    query = f"""
    select mid from live_prices where contract_id = '{symbol_to_contract_id[index_symbol]}' and security_type = 'IND'
    order by quote_timestamp desc
    limit 1
    """
    df = execute(query)
    if df.empty:
        return None
    return df.iloc[0]["mid"]


def get_gross_positions_and_unique_contracts(account_number: str):
    query = """
    select COALESCE(sum(abs(quantity)), 0) as gross_positions, COUNT(DISTINCT contract_id) as unique_contracts
    from positions
    where account = %s
    and status = 'open'
    """

    df = execute(query, (str(account_number),))

    if df.empty:
        return 0, 0
    gross_positions = df.iloc[0]["gross_positions"]
    unique_contracts = df.iloc[0]["unique_contracts"]
    return (
        gross_positions if gross_positions is not None else 0,
        unique_contracts if unique_contracts is not None else 0,
    )


def get_current_unrealized_pl(account_number: str):
    query = """
    select sum(p.quantity * p.multiplier * (lp.mid - p.open_price)) as unrealized_pl 
    from positions p left join live_prices lp 
    on p.contract_id = lp.contract_id 
    where p.account = %s and p.status = 'open'
    """

    df = execute(query, (str(account_number),))
    if df.empty:
        return 0
    return float(df.iloc[0]["unrealized_pl"])


def insert_or_update(
    table_name: str,
    data: dict,
    attributes: list,
    statement_type: str = "INSERT",
    return_query: bool = False,
):
    if type(data) is dict:
        data = [data]

    if not data:
        return

    # Build list of all values for parameterized query
    all_values = []
    for item in data:
        for attr in attributes:
            all_values.append(item.get(attr))

    # Create placeholders for each row: (%s, %s, %s, ...)
    num_cols = len(attributes)
    placeholders_per_row = "(" + ", ".join(["%s"] * num_cols) + ")"

    # Create placeholders for all rows: (%s, %s), (%s, %s), ...
    all_placeholders = ", ".join([placeholders_per_row] * len(data))

    query = f"{statement_type} INTO {table_name} ({', '.join(attributes)}) VALUES {all_placeholders}"

    if return_query:
        return query, tuple(all_values)

    execute(query, params=tuple(all_values), fetch=False)
