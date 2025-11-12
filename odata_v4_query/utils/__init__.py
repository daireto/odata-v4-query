"""Utility functions for applying OData query options to ORM/ODM queries.

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

from ._func import compute_skip_from_page, remove_pagination_options
from .beanie import apply_to_beanie_query
from .pymongo import get_query_from_options
from .sqlalchemy import apply_to_sqlalchemy_query

__all__ = [
    'apply_to_beanie_query',
    'apply_to_sqlalchemy_query',
    'compute_skip_from_page',
    'get_query_from_options',
    'remove_pagination_options',
]
