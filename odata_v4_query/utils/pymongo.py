"""Utility function for applying OData query options to a PyMongo query.

See ``get_query_from_options()`` for more information.
"""

try:
    from pymongo import ASCENDING, DESCENDING
except ImportError as e:  # pragma: no cover
    missing_dep_msg = (
        'The pymongo dependency is not installed. '
        'Install it with `pip install odata-v4-query[pymongo]` '
        'or install it directly with `pip install pymongo`.'
    )
    raise ImportError(missing_dep_msg) from e  # pragma: no cover

from typing import Any

from odata_v4_query.query_parser import ODataQueryOptions

from ._func import compute_skip_from_page
from .filter_parsers.mongo_filter_parser import MongoDBFilterNodeParser


class PyMongoQuery(dict):
    """Simple PyMongo query dictionary implementation.

    Supports the ``skip``, ``limit``, ``filter``, ``sort``
    and ``projection`` options.

    Examples
    --------
    >>> query = PyMongoQuery(
    ...     skip=1,
    ...     limit=10,
    ...     filter_={'name': 'John'},
    ...     sort=[('age', pymongo.ASCENDING)],
    ...     projection=['name', 'age'],
    ... )
    >>> query.skip
    1
    >>> query['skip']
    1
    >>> query.limit = 2
    >>> query.limit
    2
    >>> query['limit']
    2
    >>> query['limit'] = 3
    >>> query.limit
    3
    >>> db.users.find(
    ...     skip=query.skip,
    ...     limit=query.limit,
    ...     filter=query.filter,
    ...     sort=query.sort,
    ...     projection=query.projection,
    ... )
    >>> db.users.find(**query)

    """

    skip: int | None = None
    limit: int | None = None
    filter: dict[str, Any] | None = None
    sort: list[tuple[str, int]] | None = None
    projection: list[str] | None = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.skip = kwargs.get('skip')
        self.limit = kwargs.get('limit')
        self.filter = kwargs.get('filter')
        self.sort = kwargs.get('sort')
        self.projection = kwargs.get('projection')

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        super().__setitem__(name, value)

    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)
        super().__setattr__(key, value)


def get_query_from_options(
    options: ODataQueryOptions,
    search_fields: list[str] | None = None,
    parse_select: bool = False,
) -> PyMongoQuery:
    """Get a PyMongo query from OData query options.

    Parameters
    ----------
    options : ODataQueryOptions
        Parsed query options.
    search_fields : list[str] | None, optional
        Fields to search in if ``$search`` is used, by default None.
    parse_select : bool, optional
        If True, ``$select`` is parsed and applied as a projection,
        by default False.

    Returns
    -------
    PyMongoQuery
        PyMongo query.

    Notes
    -----
    #### Pagination
    If ``$page`` option is provided, ``$skip`` is overwritten
    using ``odata_v4_query.utils.compute_skip_from_page()``.
    If ``$top`` is not provided, it defaults to
    ``odata_v4_query.definitions.DEFAULT_LIMIT``.

    #### Search
    The ``$search`` option is only supported if ``search_fields``
    is provided.

    #### Select and projection
    The ``$select`` option is only supported if ``parse_select``
    is True.

    #### Unsupported options
    The ``$count``, ``$expand`` and ``$format`` options are
    not supported.

    #### Unsupported functions
    The following functions are not supported:
    - ``substring``
    - ``tolower``
    - ``toupper``

    Examples
    --------
    Usage:
    >>> from odata_v4_query import ODataQueryParser
    >>> from odata_v4_query.utils.pymongo import get_query_from_options
    >>> parser = ODataQueryParser()
    >>> options = parser.parse_query_string('$top=10&$skip=20')
    >>> query = get_query_from_options(options)

    Apply query to collection:
    >>> db.users.find(**query)
    >>> # or
    >>> db.users.find(
    ...     skip=query.skip,
    ...     limit=query.limit,
    ...     filter=query.filter,
    ...     sort=query.sort,
    ...     projection=query.projection,
    ... )

    Parsing ``$search`` option:
    >>> query = get_query_from_options(
    ...     options,
    ...     search_fields=['name', 'email']
    ... )

    Parsing ``$select`` option:
    >>> query = get_query_from_options(
    ...     options,
    ...     parse_select=True
    ... )

    """
    compute_skip_from_page(options)

    query = PyMongoQuery()

    if options.skip:
        query.skip = options.skip

    if options.top:
        query.limit = options.top

    if options.filter_:
        parser = MongoDBFilterNodeParser()
        filters = parser.parse(options.filter_)
        query.filter = filters

    if options.search and search_fields:
        search_filter = {
            '$or': [{field: {'$regex': options.search}} for field in search_fields],
        }
        if query.filter:
            query.filter = {'$and': [query.filter, search_filter]}
        else:
            query.filter = search_filter

    if options.orderby:
        sort_args = []
        for item in options.orderby:
            direction = DESCENDING if item.direction == 'desc' else ASCENDING
            sort_args.append((item.field, direction))
        query.sort = sort_args

    if options.select and parse_select:
        query.projection = options.select

    return query
