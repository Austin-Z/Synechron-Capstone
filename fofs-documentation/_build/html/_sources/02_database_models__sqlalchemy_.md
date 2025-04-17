# Chapter 2: Database Models (SQLAlchemy)

Welcome back! In [Chapter 1: Data Collector (EdgarCollector)](01_data_collector__edgarcollector_.md), we learned how our `EdgarCollector` acts like a researcher, grabbing raw financial data (like fund holdings) from the SEC EDGAR database and saving it, often as simple CSV files.

## The Problem: From Raw Data to Organized Knowledge

Imagine you have a pile of notes (our CSV files) from your research. Each note contains details about a fund's holdings on a specific date. Now, you want to ask questions like:

*   "Show me all the holdings for fund 'MDIZX' from its latest filing."
*   "Which funds hold shares of Apple ('AAPL')?"
*   "Find all the 'Fund of Funds' – funds that mainly invest in other funds."

Just having separate CSV files makes answering these questions difficult. You'd have to manually open files, search through them, and piece things together. It's inefficient and prone to errors.

We need a way to store this data *structurally*, like organizing those notes into labeled file folders inside specific drawers in a filing cabinet. This way, we know exactly where to look for information about funds, their filings over time, and the specific investments (holdings) within each filing.

This is where **Database Models** come in.

## Meet the Blueprints: Our Database Models

Think of Database Models as **detailed blueprints** for organizing information in our database. Just like a builder needs blueprints to construct a house correctly, we need models to build our database tables correctly.

In our project, we use a powerful Python tool called **SQLAlchemy**. It helps us define these blueprints using familiar Python code (classes) instead of writing complex database commands directly.

**Key Ideas:**

1.  **SQLAlchemy:** A popular Python library that acts as a translator. It lets us work with databases using Python objects and methods, translating our actions into the specific language the database understands (SQL).
2.  **Models:** These are Python classes we define (like `Fund`, `Filing`, `Holding`). Each class represents a specific *type* of information we want to store.
3.  **Tables:** SQLAlchemy uses our model classes to create corresponding tables in the actual database. If the `Fund` model is the blueprint, the `funds` table in the database is the actual structure built from that blueprint.
4.  **Columns:** Inside each model class, we define attributes that correspond to columns in the database table. For example, our `Fund` model might have columns for `ticker`, `name`, and `fund_type`.
5.  **Data Types:** We specify what kind of data each column should hold (e.g., `String` for text like a ticker, `Integer` for whole numbers like an ID, `Float` for decimal numbers like a holding's value, `DateTime` for dates). This ensures data consistency.
6.  **Relationships:** This is a crucial part! Models define how different tables are connected. For example, a `Filing` record belongs to one specific `Fund`, and each `Holding` record belongs to one specific `Filing`. SQLAlchemy helps us define and manage these connections easily.

## Defining Our Blueprints with SQLAlchemy

Let's look at how we define these blueprints in our code, using simplified examples from `src/models/database.py`.

**1. The `Fund` Blueprint:**

This model defines how we store basic information about each mutual fund.

```python
# File: src/models/database.py (Simplified)
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Base class for all our models
Base = declarative_base()

class Fund(Base):
    """Blueprint for the 'funds' table."""
    __tablename__ = 'funds' # The actual table name in the database

    # Define the columns (like fields in a spreadsheet)
    id = Column(Integer, primary_key=True) # Unique ID for each fund
    ticker = Column(String(10), unique=True, nullable=False) # Fund ticker (e.g., 'MDIZX')
    name = Column(String(255), nullable=False) # Full name of the fund
    fund_type = Column(Enum('fund_of_funds', 'underlying_fund', name='fund_type')) # Type of fund

    # Define the relationship: A Fund can have many Filings
    filings = relationship("Filing", back_populates="fund")

    def __repr__(self): # How to represent a Fund object when printed
        return f"<Fund(ticker='{self.ticker}', name='{self.name}')>"
```

*   `Base = declarative_base()`: We start by creating a `Base` class provided by SQLAlchemy. All our models will inherit from this.
*   `class Fund(Base):`: We define our `Fund` model as a Python class inheriting from `Base`.
*   `__tablename__ = 'funds'`: This explicitly tells SQLAlchemy that this class maps to a database table named `funds`.
*   `id = Column(...)`, `ticker = Column(...)`, etc.: These lines define the columns in the `funds` table. We specify the data type (`Integer`, `String`, `Enum`) and constraints (`primary_key=True`, `unique=True`, `nullable=False`).
*   `filings = relationship(...)`: This is crucial! It tells SQLAlchemy that a `Fund` object is related to `Filing` objects. The `back_populates="fund"` part links it back to a corresponding relationship defined in the `Filing` model, creating a two-way connection.

**2. The `Filing` Blueprint:**

This model represents the metadata for a specific NPORT filing submitted by a fund.

```python
# File: src/models/database.py (Simplified)
from sqlalchemy import ForeignKey, UniqueConstraint # Import necessary types

class Filing(Base):
    """Blueprint for the 'filings' table."""
    __tablename__ = 'filings'

    id = Column(Integer, primary_key=True)
    # Link to the 'funds' table: Each filing belongs to ONE fund.
    fund_id = Column(Integer, ForeignKey('funds.id'), nullable=False)
    filing_date = Column(DateTime, nullable=False) # When the report was filed
    period_end_date = Column(DateTime, nullable=False) # The date the holdings data is for

    # Define relationships
    # Link back to the Fund model
    fund = relationship("Fund", back_populates="filings")
    # A Filing can have many Holdings
    holdings = relationship("Holding", back_populates="filing")

    # Prevent duplicate filings for the same fund and period
    __table_args__ = (UniqueConstraint('fund_id', 'period_end_date'),)
```

*   `fund_id = Column(Integer, ForeignKey('funds.id'), ...)`: This is the **foreign key**. It's a column in the `filings` table that stores the `id` of the `Fund` this filing belongs to. It physically links the `filings` table back to the `funds` table.
*   `fund = relationship("Fund", ...)`: This complements the `ForeignKey`. It allows us to easily access the related `Fund` object directly from a `Filing` object in our Python code (e.g., `my_filing.fund`).
*   `holdings = relationship("Holding", ...)`: Similarly, this defines that one `Filing` can contain many `Holding` records.
*   `__table_args__ = (UniqueConstraint(...),)`: This adds a database rule: you cannot have two rows in the `filings` table with the same `fund_id` and `period_end_date`.

**3. The `Holding` Blueprint:**

This model defines the structure for storing each individual investment (stock, bond, other fund) listed within a filing.

```python
# File: src/models/database.py (Simplified)

class Holding(Base):
    """Blueprint for the 'holdings' table."""
    __tablename__ = 'holdings'

    id = Column(Integer, primary_key=True)
    # Link to the 'filings' table: Each holding belongs to ONE filing.
    filing_id = Column(Integer, ForeignKey('filings.id'), nullable=False)
    cusip = Column(String(9)) # Investment identifier
    ticker = Column(String(10)) # Investment ticker (e.g., 'AAPL')
    name = Column(String(255)) # Name of the investment
    value = Column(Float) # Market value of the holding
    percentage = Column(Float) # Percentage of the fund's assets
    asset_type = Column(String(50)) # Type of asset (e.g., 'Equity', 'Gov Bond')

    # Link back to the Filing model
    filing = relationship("Filing", back_populates="holdings")
```

*   Again, we see a `ForeignKey('filings.id')` linking each `Holding` record back to the specific `Filing` it came from.
*   The `relationship("Filing", ...)` allows us to navigate from a `Holding` object back to its parent `Filing` object (e.g., `my_holding.filing`).

We also have a `FundRelationship` model (see `src/models/database.py`) specifically designed to track when one fund (the parent) holds another fund (the child) as part of its investments, which is key for analyzing Funds of Funds.

## How It Works: From Python Class to Database Table

You don't usually interact with these model classes directly to *create* the tables. Instead, you define them like we saw above. Then, other parts of the system use these definitions:

1.  **Table Creation:** Tools like the [Database Manager](03_database_manager.md) or [Database Migrations (Alembic)](07_database_migrations__alembic_.md) read these model definitions. They instruct SQLAlchemy to connect to the database and generate the necessary SQL commands (like `CREATE TABLE funds (...)`, `CREATE TABLE filings (...)`, etc.) to build the actual tables based on our blueprints.
2.  **Data Handling:** When we load data (using [Data Loading & Management Scripts](04_data_loading___management_scripts.md)), we create *instances* (objects) of these model classes in Python. For example, to add the 'MDIZX' fund:
    ```python
    # This is Python code, NOT SQL!
    new_fund = Fund(ticker='MDIZX', name='Meridian Small Cap Growth Fund')
    # Code using the Database Manager would then save this object:
    # db_manager.add_with_commit(session, new_fund)
    ```
    SQLAlchemy, guided by the [Database Manager](03_database_manager.md), translates creating this `new_fund` object and saving it into an `INSERT INTO funds (ticker, name) VALUES ('MDIZX', 'Meridian Small Cap Growth Fund')` SQL command, which is sent to the database.

## Under the Hood: SQLAlchemy's Magic

Let's visualize how creating a new `Fund` record works using these models:

```{mermaid}
sequenceDiagram
    participant UserScript as Data Loading Script
    participant Models as Fund Class (Blueprint)
    participant DBSession as SQLAlchemy Session
    participant SQLAlchemyORM as SQLAlchemy ORM Engine
    participant Database

    UserScript->>Models: Create Fund object: `fund = Fund(ticker='MDIZX', ...)`
    UserScript->>DBSession: Add object to session: `session.add(fund)`
    Note over DBSession: Object is now 'pending'
    UserScript->>DBSession: Commit transaction: `session.commit()`
    DBSession->>SQLAlchemyORM: Process 'pending' Fund object
    SQLAlchemyORM->>SQLAlchemyORM: Generate SQL: `INSERT INTO funds ...`
    SQLAlchemyORM->>Database: Execute SQL INSERT command
    Database-->>SQLAlchemyORM: Confirm insertion (e.g., return new ID)
    SQLAlchemyORM-->>DBSession: Commit successful
    Note over Models: Fund object might get updated (e.g., with the new ID)
    DBSession-->>UserScript: Commit finished
```

1.  Your script creates a standard Python object using one of our model classes (e.g., `Fund`).
2.  You add this object to a SQLAlchemy `Session` (managed by our [Database Manager](03_database_manager.md)). The session tracks changes.
3.  When you `commit` the session, SQLAlchemy looks at the objects you added.
4.  It uses the model definition (the blueprint) to figure out which table (`funds`) and columns (`ticker`, `name`) correspond to the object's data.
5.  It generates the appropriate SQL command (`INSERT INTO ...`).
6.  It sends this command to the database to actually store the data.

The beauty is that we mostly interact with Python objects, and SQLAlchemy handles the translation to and from the database language (SQL).

**Key Code Reference (`src/models/database.py`):**

```python
# File: src/models/database.py
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey # etc.

# The foundation for all models
Base = declarative_base()

# Our model classes inherit from Base
class Fund(Base):
    __tablename__ = 'funds'
    # ... columns ...
    # Relationship defined here links Fund -> Filing
    filings = relationship("Filing", back_populates="fund")

class Filing(Base):
    __tablename__ = 'filings'
    # Foreign key links Filing -> Fund (table-level link)
    fund_id = Column(Integer, ForeignKey('funds.id'), nullable=False)
    # ... other columns ...
    # Relationship defined here links Filing -> Fund (object-level link)
    fund = relationship("Fund", back_populates="filings")
    # Relationship defined here links Filing -> Holding
    holdings = relationship("Holding", back_populates="filing")

class Holding(Base):
    __tablename__ = 'holdings'
    # Foreign key links Holding -> Filing
    filing_id = Column(Integer, ForeignKey('filings.id'), nullable=False)
    # ... other columns ...
    # Relationship links Holding -> Filing
    filing = relationship("Filing", back_populates="holdings")

# ... FundRelationship model ...
```

This file is the central place where the structure of our database is defined in Python code. The `Base`, `Column`, `ForeignKey`, and `relationship` components are the core SQLAlchemy tools we use to build these blueprints.

## Conclusion

You've now learned about Database Models and how we use SQLAlchemy to define them. These models are crucial blueprints that dictate how our collected financial data is structured and stored in the database.

*   Models (`Fund`, `Filing`, `Holding`, `FundRelationship`) are Python classes defining table structures.
*   SQLAlchemy translates these Python definitions into database tables and helps us interact with data using Python objects.
*   `Columns`, `Data Types`, `ForeignKeys`, and `Relationships` are key components for defining structure and connections.

These blueprints ensure our data is organized, consistent, and easily accessible for analysis. But how do we actually connect to the database and use these models to add or retrieve data? That's the job of the Database Manager.

**Next Up:** Let's meet the component responsible for managing the database connection and executing operations in [Chapter 3: Database Manager](03_database_manager.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)