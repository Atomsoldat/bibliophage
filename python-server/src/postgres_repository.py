"""Generic PostgreSQL repository module.

Provides a base repository class for PostgreSQL database operations using psycopg3's
async connection pooling. This can be extended for specific use cases like vector
databases, document storage, etc.

References:
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html
    - https://www.psycopg.org/psycopg3/docs/advanced/async.html
    - https://www.psycopg.org/psycopg3/docs/api/pool.html#the-connectionpool-class

"""

import importlib.resources
import logging
from collections.abc import Callable

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
        configure_callback: Callable[[Connection], None] | None = None,
        min_size: int = 4,
        max_size: int = 100,
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
        self._pool: AsyncConnectionPool | None = None

    async def ensure_initialised(self) -> None:
        """Initialise the database connection pool if not already initialised.

        We call this subroutine once during server startup to open the connection pool
        That way we don't have to think about that before executing code
        Each class inheriting from this one will have its own pool in it
        And will need its own invocation of this function

        Raises:
            Exception: Any exception from pool creation, opening, or connection acquisition

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
                        "autocommit": True,
                    },
                }

                # Add configure callback if provided
                if self._configure_callback is not None:
                    pool_kwargs["configure"] = self._configure_callback

                self._pool = AsyncConnectionPool(**pool_kwargs)
                await self._pool.open()
                # wait until min_size connections are available (default timeout 30s)
                await self._pool.wait()
                logger.info("PostgreSQL connection pool initialised successfully")
            except Exception as e:
                logger.error(f"Failed to initialise PostgreSQL pool: {e}")
                self._pool = None
                raise

    async def execute(self, sql_command: str, *, params=None, callback):
        """Execute a SQL command and pass the cursor to a callback function.

        The connection stays open while the callback executes, then automatically
        returns to the pool when the callback completes.

        Args:
            sql_command: The SQL command to execute (may contain %s placeholders)
            params: Optional tuple/list of parameters for parameterized queries
            callback: An async function that receives the cursor and processes it

        Returns:
            The return value of the callback function

        Example:
            # Simple query
            async def process_results(cursor):
                return await cursor.fetchall()

            results = await repo.execute("SELECT * FROM skeletons", callback=process_results)

            # Parameterized query
            results = await repo.execute(
                "SELECT * FROM skeletons WHERE id = %s",
                params=(skeleton_id,),
                callback=process_results
            )

        """
        await self.ensure_initialised()
        async with self._pool.connection() as conn:
            # a cursor is an iterator over the results returned by the query
            # the rows contained in the result set of the cursor can be accessed
            # via various methods (fetchOne(), fetchAll(), ...)
            if params is not None:
                cursor = await conn.execute(sql_command, params)
            else:
                cursor = await conn.execute(sql_command)
            return await callback(cursor)

    async def execute_script(self, sql_script: str) -> None:
        """Execute a multi-statement SQL script.

        Intended for DDL such as schema initialisation: there are no parameters
        and no result set to return. The pool runs in autocommit mode, so each
        statement in the script is committed individually as psycopg3 sends it.

        Use execute() for single parameterised queries and execute_transaction()
        when several statements must succeed or fail together.

        Args:
            sql_script: One or more SQL statements separated by semicolons.

        """
        await self.ensure_initialised()
        async with self._pool.connection() as conn:
            await conn.execute(sql_script)

    async def execute_transaction(self, callback):
        """Acquire a connection, open a transaction, and pass the connection to a callback.

        All statements executed on the connection inside the callback are wrapped in a
        single BEGIN/COMMIT block. On any exception the transaction is rolled back and
        the error is re-raised.

        Use this instead of execute() when multiple statements must succeed or fail
        together (e.g. inserting into a main table and its junction tables).

        Args:
            callback: An async function that receives the connection and executes
                      one or more statements on it.

        Returns:
            The return value of the callback function

        Example:
            async def insert_document_and_tags(conn):
                cursor = await conn.execute(insert_sql, params)
                row = await cursor.fetchone()
                document_id = str(row[0])
                await conn.execute(tags_sql, {"document_id": document_id, ...})
                return document_id

            document_id = await repo.execute_transaction(insert_document_and_tags)

        """
        await self.ensure_initialised()
        async with self._pool.connection() as conn:
            async with conn.transaction():
                return await callback(conn)

    async def initialise_db_schema(self, ddl_filename: str) -> None:
        """Create tables defined in db_schema/{ddl_filename} if they do not yet exist.

        The SQL is shipped as package data alongside the Python code so it
        travels with the application no matter how it is installed or invoked.

        Args:
            ddl_filename: Name of the SQL file inside the db_schema package
                          (e.g. "documents.sql", "vectors.sql")

        """
        ddl_schema_dir = importlib.resources.files("db_schema")
        ddl_file = ddl_schema_dir.joinpath(ddl_filename)
        ddl = ddl_file.read_text(encoding="utf-8")
        await self.execute_script(ddl)
        logger.info("Schema initialisation executed (%s)", ddl_filename)

    async def close_pool(self) -> None:
        """Close the database connection pool.

        This should be called when the application shuts down to cleanly
        close the psycopg connection pool.
        """
        if self._pool is not None:
            await self._pool.close(timeout=10.0)
            self._pool = None
            # we let the caller handle that
            # logger.info("PostgreSQL connection pool closed")
