from typing import Any

from pymongo import ASCENDING, DESCENDING

from odata_v4_query.query_parser import ODataQueryOptions

from .filter_parsers.mongo_filter_parser import MongoDBFilterNodeParser


class PyMongoQuery(dict):
    """Simple PyMongo query dictionary implementation
    supporting the ``skip``, ``limit``, ``filter``, ``sort``
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

    def __init__(self, **kwargs):
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

    .. note::
        The ``$count``, ``$expand`` and ``$format`` options
        won't be applied. You need to handle them manually.

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
    """
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
        query.filter = {
            '$or': [
                {field: {'$regex': options.search}} for field in search_fields
            ]
        }

    if options.orderby:
        sort_args = []
        for item in options.orderby:
            direction = DESCENDING if item.direction == 'desc' else ASCENDING
            sort_args.append((item.field, direction))
        query.sort = sort_args

    if options.select and parse_select:
        query.projection = options.select

    return query
