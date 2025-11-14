from odata_v4_query.definitions import DEFAULT_LIMIT
from odata_v4_query.query_parser import ODataQueryOptions


def compute_skip_from_page(
    options: ODataQueryOptions,
    default_limit: int = DEFAULT_LIMIT,
) -> None:
    """Compute $skip from $page if $page is provided.

    Changes are applied in-place.

    If ``$top`` is not provided, it defaults to
    ``odata_v4_query.definitions.DEFAULT_LIMIT``.

    The ``$skip`` is computed as ``(page - 1) * top``.
    If it is provided, it is overwritten.

    Parameters
    ----------
    options : ODataQueryOptions
        Parsed query options.
    default_limit : int, optional
        Default limit to use if ``$top`` is not provided,
        by default ``odata_v4_query.definitions.DEFAULT_LIMIT``.

    """
    if options.page:
        options.top = options.top or default_limit
        options.skip = (options.page - 1) * options.top


def remove_pagination_options(options: ODataQueryOptions) -> None:
    """Remove pagination options from query.

    Changes are applied in-place.

    Parameters
    ----------
    options : ODataQueryOptions
        Parsed query options.

    """
    options.top = None
    options.skip = None
    options.page = None
