# Chapter 3: Database Manager

Welcome back! In [Chapter 2: Database Models (SQLAlchemy)](02_database_models__sqlalchemy_.md), we designed the blueprints (`Fund`, `Filing`, `Holding` classes) for how our financial data should be structured in the database. We have the plans, but how do we actually connect to the database "building" and start using those plans to store or retrieve information?

## The Problem: Connecting and Talking to the Database

Imagine you have the architectural blueprints for a library (our Database Models). You also have boxes of books arriving (raw data from the [Data Collector (EdgarCollector)](01_data_collector__edgarcollector_.md)). Now, you need someone who knows:

1.  How to unlock the library doors (connect to the database).
2.  How to issue library cards (provide sessions) so people can check books in or out (add or read data).
3.  How to manage the flow of people entering and leaving efficiently (manage connections).

Simply having the blueprints isn't enough. We need a dedicated manager for the database interactions.

## Meet the Database Manager: Your Project's Librarian

Think of the `DatabaseManager` as your project's head librarian. It doesn't store the data itself (that's the database's job) and it doesn't define the data structure (that's the [Database Models (SQLAlchemy)](02_database_models__sqlalchemy_.md)'s job). Its main responsibilities are:

1.  **Connecting:** It knows the secret handshake (database address, username, password) to connect to the database system (like MySQL).
2.  **Providing Access:** It hands out temporary "library cards" called **sessions**. Other parts of the project use these sessions to perform actions like adding new fund information or querying existing holdings.
3.  **Managing Connections:** It efficiently manages the actual network connections to the database, often reusing them (using a connection pool) to save time and resources.
4.  **Hiding Complexity:** It uses the powerful SQLAlchemy library under the hood but provides a simpler interface, so other parts of the project don't need to worry about the nitty-gritty details of database connection logic.

Essentially, the `DatabaseManager` is the central gateway for all database interactions in our project.

## Key Concepts Explained

Let's break down some terms related to the Database Manager:

*   **Database Engine:** The actual database software running on a server, like MySQL or PostgreSQL. This is the "library building" itself.
*   **Connection String/URL:** A special string containing all the information needed to connect to the database: the type of database, username, password, server address (host), port number, and the specific database name. It's like the library's full address and the key to the front door. Example: `mysql+mysqlconnector://user:password@hostname:port/database_name`
*   **SQLAlchemy Engine:** A core object created by SQLAlchemy using the Connection String. It represents the connection pathway to a *specific* database and manages a **connection pool**. Think of it as the library's main entrance and security system.
*   **Connection Pool:** Instead of opening a brand new connection to the database every single time we need one (which is slow), the SQLAlchemy Engine maintains a "pool" of ready-to-use connections. When we need one, the Engine lends one out from the pool; when we're done, it goes back into the pool. This is like having a set of pre-validated entry passes at the library entrance for efficiency.
*   **Session (SQLAlchemy Session):** The primary tool for interacting with the database *through* the Engine. You get a Session from the `DatabaseManager`. Think of it as your temporary library card. You use the Session to:
    *   Add new objects (like a new `Fund`) to be saved.
    *   Query the database for existing objects.
    *   Mark objects for deletion.
    The Session keeps track of all your intended changes within a single "conversation" or transaction. When you're ready, you tell the session to `commit` (save) these changes permanently to the database. If something goes wrong, you can `rollback` (cancel) the changes.

## How to Use the Database Manager

Using the `DatabaseManager` is quite straightforward. You mostly interact with it in two ways: creating an instance and getting a session.

**1. Create a Database Manager Instance:**

```python
# File: (Example usage, e.g., in a script or service)
from src.database.manager import DatabaseManager

# Create an instance of the manager
# This automatically reads connection settings and sets up the engine.
db_manager = DatabaseManager()

print("Database Manager initialized.")
# Expected Outcome: The manager connects to the database using settings
# found in the environment or configuration files. If successful, it prints
# the message. If it fails (e.g., wrong password), it might raise an error.
```

When you create `DatabaseManager()`, it automatically looks for the database connection details (using [Application Configuration (Settings)](08_application_configuration__settings_.md)) and sets up the SQLAlchemy Engine and Session factory behind the scenes.

**2. Get a Database Session:**

This is the most common way you'll use the manager.

```python
# (Continuing from above...)

# Ask the manager for a new session (like getting a library card)
db_session = db_manager.get_session()

print("Obtained a database session.")

# Now you can use 'db_session' to talk to the database...
# (Example: Add a new fund - requires Fund model from Chapter 2)
# from src.models.database import Fund
# new_fund = Fund(ticker="TESTFUND", name="My Test Fund", fund_type="fund_of_funds")
# db_session.add(new_fund) # Tell the session we want to add this
# db_session.commit()     # Save the changes to the database!

# IMPORTANT: Always close the session when you're done!
db_session.close()
print("Session closed.")

# Expected Outcome: A Session object is created and returned.
# You can then use this session object with SQLAlchemy methods
# (like add, query, commit, rollback) to interact with the database.
# Finally, the session is closed, releasing the connection back to the pool.
```

The `get_session()` method provides you with that temporary "library card" (the `Session` object) needed to perform database operations. Remember to `close()` the session when you're finished to return the underlying connection to the pool.

**3. Helper Method: `add_with_commit`**

The `DatabaseManager` also provides a convenient helper method for a common pattern: adding a single object and immediately saving (committing) it.

```python
# (Continuing from above...)
from src.models.database import Fund # Assuming Fund model is defined

# Get a fresh session
session_for_add = db_manager.get_session()

try:
    # Create a new Fund object (using blueprint from Chapter 2)
    another_fund = Fund(ticker="XYZFUND", name="Another Test Fund", fund_type="underlying_fund")

    # Use the helper method to add and commit in one step
    saved_fund = db_manager.add_with_commit(session_for_add, another_fund)

    if saved_fund:
        print(f"Successfully added and saved fund: {saved_fund.ticker}")
    else:
        print("Failed to add fund.")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Always close the session
    session_for_add.close()

# Expected Outcome: The 'XYZFUND' object is added to the session,
# the session commits the change to the database, and the method
# returns the saved object (possibly updated with a database ID).
# If an error occurs during the database operation, it catches it,
# rolls back the change, logs the error, and returns None.
```

This helper simplifies the common add-and-save operation and includes basic error handling (logging and rollback).

## Under the Hood: How Does it Work?

Let's trace the steps when you create and use the `DatabaseManager`:

1.  **Initialization (`__init__`)**:
    *   You create `DatabaseManager()`.
    *   It reads the database connection URL (e.g., `mysql+mysqlconnector://user:pass@host:port/db_name`) from the project's [Application Configuration (Settings)](08_application_configuration__settings_.md).
    *   It uses SQLAlchemy's `create_engine(DATABASE_URL)` function. This function parses the URL, understands it's for MySQL, and sets up the core **Engine** object, which manages the low-level database connections (the **connection pool**).
    *   It then creates a **Session factory** (`sessionmaker(bind=self.engine)`). This factory knows how to create new `Session` objects that are linked to our specific Engine.

2.  **Getting a Session (`get_session`)**:
    *   You call `db_manager.get_session()`.
    *   The manager uses the Session factory created during initialization.
    *   The factory produces a new `Session` object. This Session borrows a connection from the Engine's connection pool.
    *   This `Session` object is returned to your code.

3.  **Using the Session**:
    *   Your code (e.g., a [Data Loading & Management Scripts](04_data_loading___management_scripts.md) or the [Fund Service](05_fund_service.md)) uses this Session object to add, query, update, or delete data using the [Database Models (SQLAlchemy)](02_database_models__sqlalchemy_.md).
    *   When you call `session.commit()`, the Session gathers all the tracked changes and sends the corresponding SQL commands (like `INSERT`, `UPDATE`, `DELETE`) to the database over the borrowed connection.
    *   When you call `session.close()`, the Session releases the database connection back to the Engine's pool, making it available for reuse.

Here's a diagram showing the initialization and session retrieval:

```mermaid
sequenceDiagram
    participant YourScript as Your Script
    participant DBMgr as DatabaseManager
    participant Settings
    participant SQLAlchemyEngine as Engine (Pool)
    participant SQLAlchemySessionMaker as Session Factory
    participant DBSession as Session

    YourScript->>DBMgr: Create instance: `DatabaseManager()`
    DBMgr->>Settings: Read DB URL (e.g., from .env)
    Settings-->>DBMgr: Return DB URL
    DBMgr->>SQLAlchemyEngine: `create_engine(DB_URL)`
    Note over SQLAlchemyEngine: Engine setup, connection pool ready
    SQLAlchemyEngine-->>DBMgr: Engine instance created
    DBMgr->>SQLAlchemySessionMaker: `sessionmaker(bind=Engine)`
    SQLAlchemySessionMaker-->>DBMgr: Session Factory created
    DBMgr-->>YourScript: `DatabaseManager` instance ready

    YourScript->>DBMgr: `get_session()`
    DBMgr->>SQLAlchemySessionMaker: Call factory `()`
    SQLAlchemySessionMaker->>SQLAlchemyEngine: Request connection from pool
    SQLAlchemyEngine-->>SQLAlchemySessionMaker: Provide connection
    SQLAlchemySessionMaker-->>DBSession: Create new `Session` object
    DBSession-->>DBMgr: Return new `Session`
    DBMgr-->>YourScript: Return `Session` instance
```

## Diving Deeper into the Code (`src/database/manager.py`)

Let's look at the key parts of the `DatabaseManager` implementation.

**1. Initialization and Connection Setup:**

```python
# File: src/database/manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models.database import Base # Needed for create_tables
from src.config import Settings # To get DB settings
import os

class DatabaseManager:
    def __init__(self):
        # ... setup logger ...
        self.settings = Settings() # Load settings (reads .env)
        self._initialize_connection() # Call helper to connect

    def _initialize_connection(self):
        """Initialize database connection from settings."""
        # Get the database URL from settings
        # (Settings class logic handles finding DATABASE_URL env var or building it)
        database_url = self.settings.database_url

        # Create the SQLAlchemy engine using the URL
        self.engine = create_engine(
            database_url,
            pool_recycle=3600, # Optional: Recycle connections periodically
            pool_pre_ping=True # Optional: Check connection validity
            # ... other args ...
        )

        # Create the session factory bound to our engine
        self.Session = sessionmaker(bind=self.engine)
```

*   The `__init__` method creates a `Settings` object to load configuration.
*   It calls `_initialize_connection`, which retrieves the crucial `database_url`.
*   `create_engine(database_url, ...)` sets up the core engine and connection pool based on the URL provided.
*   `sessionmaker(bind=self.engine)` creates the factory (`self.Session`) that will produce individual session objects, all tied to the engine we just created.

**2. Getting a Session:**

```python
# File: src/database/manager.py
# (Inside the DatabaseManager class)

    def get_session(self) -> Session:
        """Get a new database session."""
        # Simply call the factory to create and return a new session
        return self.Session()
```

*   This method is very simple! It just calls the session factory (`self.Session()`) that was configured during initialization. The factory takes care of getting a connection from the pool and creating the `Session` object.

**3. Helper: Add and Commit:**

```python
# File: src/database/manager.py
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
# (Inside the DatabaseManager class)

    def add_with_commit(self, session: Session, obj: Base) -> Optional[Base]:
        """Add an object to the database and commit."""
        try:
            session.add(obj)  # Stage the object for addition
            session.commit()  # Try to save changes to DB
            session.refresh(obj) # Update the object with DB data (like ID)
            return obj
        except SQLAlchemyError as e:
            # Log the error if saving fails
            self.logger.error(f"Error adding to database: {str(e)}")
            session.rollback() # Cancel the changes
            return None # Indicate failure
```

*   This method encapsulates the common `add -> commit -> refresh` pattern.
*   It includes `try...except` block to catch potential database errors during the `commit`.
*   If an error occurs, it rolls back the transaction (`session.rollback()`) so the database isn't left in a partially changed state, logs the error, and returns `None`.

## Conclusion

You've now met the `DatabaseManager`, our project's librarian! You learned:

*   Why we need it: To handle database connections and provide a consistent way to interact with the database.
*   What it does: Connects using settings, creates a SQLAlchemy Engine and Session factory, and provides `Session` objects (library cards) on demand.
*   Key concepts: Engine, Connection Pool, Session.
*   How to use it: Create an instance, call `get_session()` to get a session for database operations, and remember to `close()` the session.
*   How it simplifies things: It hides the complexity of connection management and provides helpful methods like `add_with_commit`.

The `DatabaseManager` acts as the essential bridge between our application's logic and the database itself. Now that we know how to define data structures ([Database Models (SQLAlchemy)](02_database_models__sqlalchemy_.md)) and how to connect and get a session (`DatabaseManager`), how do we actually put these together to load the data gathered by our [Data Collector (EdgarCollector)](01_data_collector__edgarcollector_.md)?

**Next Up:** Let's explore the scripts responsible for using the Collector, Manager, and Models to populate our database in [Chapter 4: Data Loading & Management Scripts](04_data_loading___management_scripts.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)