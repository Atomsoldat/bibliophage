"""Generic PostgreSQL repository module.

Provides a base repository class for PostgreSQL database operations using psycopg3's
async connection pooling. This can be extended for specific use cases like vector
databases, document storage, etc.

References:
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html
    - https://www.psycopg.org/psycopg3/docs/advanced/async.html
    - https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-class
"""
import logging
from typing import Callable, Optional
from psycopg import Connection
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)


class PostgresRepository:
    """Base repository for PostgreSQL database operations.

    Manages a connection pool and provides methods for executing queries.
    The pool is automatically initialised on first use.

    This class is designed to be extended for specific database use cases.
    Subclasses can provide connection-specific configuration via the
    configure_callback parameter.

    Usage:
        # Direct usage
        repo = PostgresRepository("postgresql://user:pass@localhost/db")

        async def get_results(cursor):
            return await cursor.fetchall()

        results = await repo.execute('SELECT * FROM users', get_results)

        # Or extend for specific use cases
        class MyDatabase(PostgresRepository):
            def __init__(self):
                super().__init__(
                    connection_url="postgresql://...",
                    configure_callback=my_setup_function
                )
    """

    def __init__(
        self,
        connection_url: str,
        configure_callback: Optional[Callable[[Connection], None]] = None,
        min_size: int = 4,
        max_size: int = 100
    ):
        """Initialise the repository with connection parameters.

        Args:
            connection_url: PostgreSQL connection string
            configure_callback: Optional function to configure each connection
                               (e.g., for registering custom types)
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool
        """
        self._connection_url = connection_url
        self._configure_callback = configure_callback
        self._min_size = min_size
        self._max_size = max_size
        self._pool: Optional[AsyncConnectionPool] = None

    async def ensure_initialised(self):
        """Initialise the database connection pool if not already initialised.

        This method is called automatically by execute() and doesn't typically
        need to be called manually.

        If initialization fails (network issues, bad credentials, etc.), the pool
        is reset to allow retry on the next call.

        Raises:
            Exception: Any exception from pool creation, opening, or connection acquisition

        Thread-safe for async contexts - multiple concurrent calls will only
        initialise the pool once.
        """
        if self._pool is None:
            try:
                pool_kwargs = {
                    "open": False,
                    "conninfo": self._connection_url,
                    "min_size": self._min_size,
                    "max_size": self._max_size,
                    "close_returns": True,
                    "kwargs": {
                        "autocommit": True
                    }
                }

                # Add configure callback if provided
                if self._configure_callback is not None:
                    pool_kwargs["configure"] = self._configure_callback

                self._pool = AsyncConnectionPool(**pool_kwargs)
                await self._pool.open()
                # wait until min_size connections are available (default timeout 30s)
                await self._pool.wait()
                logger.info(f"PostgreSQL connection pool initialised successfully")
            except Exception as e:
                logger.error(f"Failed to initialise PostgreSQL pool: {e}")
                self._pool = None
                raise

    async def execute(self, sql_command: str, callback):
        """Execute a SQL command and pass the cursor to a callback function.

        The connection stays open while the callback executes, then automatically
        returns to the pool when the callback completes.

        Args:
            sql_command: The SQL command to execute
            callback: An async function that receives the cursor and processes it

        Returns:
            The return value of the callback function

        Example:
            async def process_results(cursor):
                return await cursor.fetchall()

            results = await repo.execute("SELECT * FROM users", process_results)
        """
        await self.ensure_initialised()
        async with self._pool.connection() as conn:
            # a cursor is an iterator over the results returned by the query
            # the rows contained in the result set of the cursor can be accessed
            # via various methods (fetchOne(), fetchAll(), ...)
            cursor = await conn.execute(sql_command)
            return await callback(cursor)

    async def close_pool(self):
        """Close the database connection pool.

        This should be called when the application shuts down to cleanly
        close the psycopg connection pool.
        """
        if self._pool is not None:
            await self._pool.close(timeout=10.0)
            self._pool = None
            logger.info("PostgreSQL connection pool closed")
