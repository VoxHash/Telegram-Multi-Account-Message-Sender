"""
Database service with SQLite initialization and session management.
"""

import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator, Any, Dict
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from .settings import get_settings
from .logger import get_logger
from ..models import (
    BaseModel, Account, Campaign, Recipient, SendLog
)


class DatabaseService:
    """Database service for managing SQLite database operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger()
        self.engine: Optional[Engine] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connection and create tables."""
        if self._initialized:
            return
        
        try:
            # Ensure app data directory exists
            app_data_dir = Path(self.settings.app_data_dir)
            app_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create database engine
            database_url = self.settings.database_url
            if database_url.startswith("sqlite:///"):
                # SQLite specific configuration
                db_path = self.settings.get_database_path()
                db_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.engine = create_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30,
                    },
                    echo=self.settings.debug,
                )
            else:
                # PostgreSQL/MySQL configuration
                self.engine = create_engine(
                    database_url,
                    echo=self.settings.debug,
                    pool_pre_ping=True,
                )
            
            # Add event listeners
            self._setup_event_listeners()
            
            # Create all tables
            self.create_tables()
            
            self._initialized = True
            self.logger.info(f"Database initialized: {database_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Set up database event listeners."""
        if not self.engine:
            return
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and compatibility."""
            if self.settings.database_url.startswith("sqlite:///"):
                cursor = dbapi_connection.cursor()
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Set journal mode to WAL for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Set synchronous mode for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Set cache size
                cursor.execute("PRAGMA cache_size=10000")
                # Set temp store to memory
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
    
    def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            # Import all models to ensure they are registered with SQLModel
            from ..models import Account, Campaign, Recipient, SendLog, MessageTemplate
            from ..models.recipient import RecipientList, RecipientListRecipient
            SQLModel.metadata.create_all(self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            SQLModel.metadata.drop_all(self.engine)
            self.logger.warning("All database tables dropped")
        except Exception as e:
            self.logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        return Session(self.engine)
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Session, None]:
        """Get an async database session."""
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self._initialized = False
            self.logger.info("Database connection closed")
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.exec(select(1)).first()
                return {
                    "status": "healthy",
                    "connected": True,
                    "engine": str(self.engine.url) if self.engine else None,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "engine": str(self.engine.url) if self.engine else None,
            }
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables."""
        if not self.engine:
            return {}
        
        try:
            with self.get_session() as session:
                # Get table names
                tables = SQLModel.metadata.tables.keys()
                
                # Get row counts for each table
                table_counts = {}
                for table_name in tables:
                    try:
                        table = SQLModel.metadata.tables[table_name]
                        count_result = session.exec(select(table.c.id)).all()
                        table_counts[table_name] = len(count_result)
                    except Exception as e:
                        table_counts[table_name] = f"Error: {e}"
                
                return {
                    "tables": list(tables),
                    "table_counts": table_counts,
                }
        except Exception as e:
            return {"error": str(e)}
    
    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the database."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        if not self.settings.database_url.startswith("sqlite:///"):
            raise NotImplementedError("Backup only supported for SQLite databases")
        
        if backup_path is None:
            backup_path = Path(self.settings.app_data_dir) / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # For SQLite, we can simply copy the file
        import shutil
        db_path = self.settings.get_database_path()
        shutil.copy2(db_path, backup_path)
        
        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def restore_database(self, backup_path: Path) -> None:
        """Restore database from backup."""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        if not self.settings.database_url.startswith("sqlite:///"):
            raise NotImplementedError("Restore only supported for SQLite databases")
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Close current connection
        self.close()
        
        # Copy backup to current database location
        import shutil
        db_path = self.settings.get_database_path()
        shutil.copy2(backup_path, db_path)
        
        # Reinitialize
        self.initialize()
        
        self.logger.info(f"Database restored from: {backup_path}")


# Global database service instance
db_service = DatabaseService()


def get_db_service() -> DatabaseService:
    """Get database service instance."""
    return db_service


def initialize_database() -> None:
    """Initialize the database."""
    db_service.initialize()


def get_session() -> Session:
    """Get a database session."""
    return db_service.get_session()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[Session, None]:
    """Get an async database session."""
    async with db_service.get_async_session() as session:
        yield session


def close_database() -> None:
    """Close database connection."""
    db_service.close()


def health_check() -> Dict[str, Any]:
    """Check database health."""
    return db_service.health_check()


def backup_database(backup_path: Optional[Path] = None) -> Path:
    """Create a database backup."""
    return db_service.backup_database(backup_path)


def restore_database(backup_path: Path) -> None:
    """Restore database from backup."""
    db_service.restore_database(backup_path)
