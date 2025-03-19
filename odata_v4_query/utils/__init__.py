"""Utility functions for applying OData query options
to ORM/ODM queries.

You to need to install the required dependencies for the
ORM/ODM you want to use.

**Dependencies**

- ``beanie`` for Beanie ODM utils.
- ``pymongo`` for PyMongo ODM utils.
- ``sqlalchemy`` for SQLAlchemy ORM utils.

**Example usage**

>>> from odata_v4_query import ODataQueryParser
>>> from odata_v4_query.utils.beanie import apply_to_beanie_query
>>> # Create parser instance
>>> parser = ODataQuery_parser()
>>> # Parse a complete URL
>>> options = parser.parse_url('https://example.com/odata?$count=true&$top=10&$skip=20')
>>> # Apply options to Beanie query
>>> query = apply_to_beanie_query(options, User)
"""
