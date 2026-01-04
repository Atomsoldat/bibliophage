"""Vector database repository module.

Provides a connection pool manager for pgvector database operations.
Extends the base PostgresRepository with vector-specific functionality.

References:
    - https://github.com/pgvector/pgvector-python
    - https://www.psycopg.org/psycopg3/docs/advanced/pool.html

"""
import logging

from pgvector.psycopg import register_vector_async

from postgres_repository import PostgresRepository

logger = logging.getLogger(__name__)


async def _configure_vector_connection(conn):
    """Configure a connection for pgvector operations.

    This callback is called for each connection in the pool to register
    the pgvector types with psycopg.

    Args:
        conn: The async connection to configure

    """
    await register_vector_async(conn)


class VectorDatabase(PostgresRepository):
    """Vector database connection manager using pgvector.

    Extends PostgresRepository with vector-specific connection configuration.
    The repository handles connection pooling and query execution.

    Usage:
        # Create an instance (typically once at application startup)
        vector_db = VectorDatabase(
            connection_url="postgresql://user:pass@localhost/vectordb"
        )

        # the caller defines a callback function
        async def get_results(cursor):
            # do stuff with the passed cursor
            return await cursor.fetchall()

        # the caller passes the callback function to our database
        # repository here, the repository handles all the cleanup
        # for the database connection
        results = await vector_db.execute(
            'SELECT true, 42, "Hello World!"',
            # call passed callback
            get_results
        )

        # TODO: Call this function when our application terminates
        await vector_db.close_pool()
    """

    def __init__(
        self,
        connection_url: str,
        min_size: int = 4,
        max_size: int = 100,
    ):
        """Initialise the vector database repository.

        Args:
            connection_url: PostgreSQL connection string
            min_size: Minimum number of connections in the pool
            max_size: Maximum number of connections in the pool

        """
        super().__init__(
            connection_url=connection_url,
            configure_callback=_configure_vector_connection,
            min_size=min_size,
            max_size=max_size,
        )

    async def ensure_initialised(self):
        """Initialise the database connection pool if not already initialised.

        This method is called automatically by execute() and doesn't typically
        need to be called manually. The pool configuration is loaded from
        application settings.

        Creates a PostgresRepository instance configured with pgvector support.

        Raises:
            Exception: Any exception from pool creation, opening, or connection acquisition

        """
        if self._pool is None:
            await super().ensure_initialised()
            logger.info("Vector Database initialised successfully")

    async def close_pool(self):
        """Close the database connection pool.

        This should be called when the application shuts down to cleanly
        close the psycopg connection pool.
        """
        if self._pool is not None:
            await super().close_pool()
            logger.info("Vector Database connection pool closed")
