import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import boto3
import pandas as pd
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


class RDSConnectionManager:
    """
    Manages connections to an RDS PostgreSQL database using credentials from AWS Secrets Manager.

    Example usage:
        # Basic usage
        db = RDSConnectionManager(secret_name='/quantecho/trading-cluster-secret-postgre', database='ibkr')
        db.connect()
        results = db.query("SELECT * FROM trades WHERE symbol = %s", ('AAPL',))
        db.disconnect()

        # Using context manager (recommended)
        with RDSConnectionManager(secret_name='/quantecho/trading-cluster-secret-postgre', database='ibkr') as db:
            results = db.query("SELECT * FROM trades")
    """

    def __init__(
        self,
        secret_name: str,
        database: Optional[str] = None,
        region_name: str = "us-east-1",
        autocommit: bool = True,
        connect_timeout: int = 10,
        connect_instant: bool = False,
    ):
        """
        Initialize the RDS connection manager.

        Args:
            secret_name: Name/ARN of the secret in AWS Secrets Manager
            database: Database name to connect to (optional, can connect without specifying)
            region_name: AWS region for Secrets Manager
            autocommit: Whether to autocommit transactions
            connect_timeout: Connection timeout in seconds
        """
        self.secret_name = secret_name
        self.database = database
        self.region_name = region_name
        self.autocommit = autocommit
        self.connect_timeout = connect_timeout

        self.connection: Optional[psycopg2.extensions.connection] = None
        self._db_config: Optional[Dict[str, Any]] = None

        if connect_instant:
            self.connect()

    def _get_secret(self) -> Dict[str, Any]:
        """Retrieve database credentials from AWS Secrets Manager."""
        if self._db_config is not None:
            return self._db_config

        try:
            client = boto3.client("secretsmanager", region_name=self.region_name)
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_string = response.get("SecretString")

            if not secret_string:
                raise ValueError(f"Secret {self.secret_name} has no SecretString")

            self._db_config = json.loads(secret_string)
            logger.info(f"Successfully retrieved secret: {self.secret_name}")
            return self._db_config

        except Exception as e:
            logger.error(f"Error retrieving secret {self.secret_name}: {e}")
            raise

    def connect(self) -> None:
        """
        Establish connection to the RDS database.

        Raises:
            Exception: If connection fails
        """
        if self.connection and not self.connection.closed:
            logger.warning("Connection already established")
            return

        try:
            config = self._get_secret()

            connection_params = {
                "host": config["host"],
                "port": config.get("port", 5432),
                "user": config["username"],
                "password": config["password"],
                "connect_timeout": self.connect_timeout,
            }

            # Add database if specified
            if self.database:
                connection_params["dbname"] = self.database

            self.connection = psycopg2.connect(**connection_params)
            self.connection.autocommit = self.autocommit

            db_info = f" to database '{self.database}'" if self.database else ""
            logger.info(f"Successfully connected to RDS{db_info}")

        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        self.connection = None

    def is_connected(self) -> bool:
        """Check if database connection is active."""
        return self.connection is not None and not self.connection.closed

    def query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = True,
        return_pandas: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query.

        Args:
            query: SQL query string (use %s for parameter placeholders)
            params: Tuple of parameters for the query
            fetch: Whether to fetch and return results (True for SELECT, False for INSERT/UPDATE/DELETE)

        Returns:
            List of dictionaries for SELECT queries, None for other queries

        Example:
            # SELECT query
            results = db.query("SELECT * FROM trades WHERE symbol = %s", ('AAPL',))

            # INSERT query
            db.query(
                "INSERT INTO trades (symbol, quantity, price) VALUES (%s, %s, %s)",
                ('AAPL', 100, 150.25),
                fetch=False
            )
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to database. Call connect() first.")

        cursor = None
        try:
            # Use RealDictCursor to return results as dictionaries
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(query, params or ())

            if fetch:
                results = cursor.fetchall()
                logger.debug(
                    f"Query executed successfully, fetched {len(results)} rows"
                )
                if return_pandas:
                    return pd.DataFrame([dict(row) for row in results])
                else:
                    return [dict(row) for row in results]
            else:
                affected_rows = cursor.rowcount
                if not self.autocommit:
                    self.connection.commit()
                logger.debug(
                    f"Query executed successfully, affected {affected_rows} rows"
                )
                return None

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            if not self.autocommit:
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute a query multiple times with different parameters (bulk insert/update).

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows

        Example:
            data = [
                ('AAPL', 100, 150.25),
                ('GOOGL', 50, 2800.50),
                ('MSFT', 75, 310.75)
            ]
            db.execute_many(
                "INSERT INTO trades (symbol, quantity, price) VALUES (%s, %s, %s)",
                data
            )
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to database. Call connect() first.")

        cursor = None
        try:
            cursor = self.connection.cursor()
            affected_rows = cursor.executemany(query, params_list)

            if not self.autocommit:
                self.connection.commit()

            logger.debug(
                f"Bulk query executed successfully, affected {affected_rows} rows"
            )
            return affected_rows

        except Exception as e:
            logger.error(f"Error executing bulk query: {e}")
            if not self.autocommit:
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    def begin_transaction(self) -> None:
        """Begin a transaction (useful when autocommit=False)."""
        if not self.is_connected():
            raise ConnectionError("Not connected to database.")
        # In PostgreSQL, transactions begin implicitly or with explicit BEGIN
        if self.connection.autocommit:
            self.connection.autocommit = False
        logger.debug("Transaction started")

    def commit(self) -> None:
        """Commit the current transaction."""
        if not self.is_connected():
            raise ConnectionError("Not connected to database.")
        self.connection.commit()
        logger.debug("Transaction committed")

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if not self.is_connected():
            raise ConnectionError("Not connected to database.")
        self.connection.rollback()
        logger.debug("Transaction rolled back")

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Example:
            with db.transaction():
                db.query("INSERT INTO trades ...", fetch=False)
                db.query("UPDATE accounts ...", fetch=False)
                # Automatically commits if no exception, rolls back on error
        """
        try:
            if self.autocommit:
                self.connection.autocommit(False)
            self.begin_transaction()
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            if self.autocommit:
                self.connection.autocommit(True)

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Get the underlying psycopg2 connection object.
        Use with caution - prefer using query() methods.
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to database.")
        return self.connection

    def __enter__(self):
        """Context manager entry - automatically connects."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically disconnects."""
        self.disconnect()
        return False

    def __del__(self):
        """Destructor - ensure connection is closed."""
        self.disconnect()
