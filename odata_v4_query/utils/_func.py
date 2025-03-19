from odata_v4_query.definitions import DEFAULT_LIMIT
from odata_v4_query.query_parser import ODataQueryOptions


def compute_skip_from_page(options: ODataQueryOptions, default_limit: int = DEFAULT_LIMIT) -> None:
    """Computes $skip from $page.

    If ``$top`` is not provided, it defaults to the
    ``odata_v4_query.definitions.DEFAULT_LIMIT`` value.

    The ``$skip`` is computed as ``(page - 1) * top``.

    .. note::
        If ``$skip`` is provided, it is overwritten.
    """
    if options.page:
        options.top = options.top or default_limit
        options.skip = (options.page - 1) * options.top
