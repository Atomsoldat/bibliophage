"""Vector database repository module.

Provides a singleton connection pool manager for pgvector database operations.
Uses psycopg3's async connection pooling

References:
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html
    - https://www.psycopg.org/psycopg3/docs/advanced/async.html
    - https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-class
"""
import logging
from psycopg import Connection, Cursor
from psycopg_pool import AsyncConnectionPool

from config import get_settings

logger = logging.getLogger(__name__)

# Module-level state for the singleton connection pool
_pool = None


class VectorDatabase:
    """Singleton vector database connection manager using pgvector.

    Manages a connection pool to the vector database and provides methods
    for executing queries. The pool is automatically initialized on first use.

    Usage:
        # the caller defines a callback function
        async def get_results(cursor):
            # do stuff with the passed cursor
            return await cursor.fetchall()

        # the caller passes the callback function to our database
        # repository here, the repository handles all the cleanup
        # for the database connection
        results = await VectorDatabase.execute(
            'SELECT true, 42, "Hello World!"',
            # call passed callback
            get_results
        )
    """
    @classmethod
    async def ensure_initialised(cls):
        """Initialize the database connection pool if not already initialized.

        This method is called automatically by execute() and doesn't typically
        need to be called manually. The pool configuration is loaded from
        application settings.

        If initialization fails (network issues, bad credentials, etc.), the pool
        is reset to allow retry on the next call.

        Raises:
            Exception: Any exception from pool creation, opening, or connection acquisition

        Thread-safe for async contexts - multiple concurrent calls will only
        initialize the pool once.
        """
        global _pool
        if _pool is None:
            try:
                settings = get_settings()
                connectionString = settings.database.vector_db_url
                _pool = AsyncConnectionPool(
                    open = False,
                    conninfo = connectionString,
                    min_size = 4,
                    max_size = 100,
                    # return connections to the pool when calling close()
                    close_returns = True,
                    # kwargs stands for keyword args, this is a python convention
                    # all of these arguments will be passed to every connect() invocation
                    kwargs = {
                        # we can still explicitly start transactions by using a transaction block
                        # https://www.psycopg.org/psycopg3/docs/basic/transactions.html#transaction-context
                        "autocommit": True
                    }
                )
                await _pool.open()
                # wait until min_size connections are available default timeout 30s
                await _pool.wait()
                logger.info("Vector Database connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize vector database pool: {e}")
                _pool = None
                raise

    @classmethod
    async def execute(cls, sql_command: str, callback):
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

            results = await VectorDatabase.execute("SELECT * FROM users", process_results)
        """
        await cls.ensure_initialised()
        async with _pool.connection() as conn:
            # a cursor is an iterator over the results returned by the query
            # the rows contained in the result set of the cursor can be accessed
            # via various methods (fetchOne(), fetchAll(), ...)
            # this cursor is unnamed and all data returned will be immediately
            # transferred to the client
            # for large SELECTs, using a server side named cursor will be better
            cursor = await conn.execute(sql_command)
            return await callback(cursor)
    
    # TODO: Call this function when our application terminates
    @classmethod
    async def close_pool(cls):
        """Close the database connection pool.

        This should be called when the application shuts down to cleanly
        close the psycopg connection pool.
        """
        global _pool

        if _pool is not None:
            await _pool.close(timeout = 10.0)
            _pool = None
            logger.info("Vector Database connection pool closed")