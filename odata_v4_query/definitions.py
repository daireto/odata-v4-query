"""Definitions for OData V4 query options."""

DEFAULT_LIMIT = 100
"""Default limit."""

DEFAULT_FORMAT_OPTIONS = ('json', 'xml', 'csv', 'tsv')
"""Default format options."""

DEFAULT_OPERATORS = {
    # comparison
    'eq': 2,
    'ne': 2,
    'gt': 2,
    'ge': 2,
    'lt': 2,
    'le': 2,
    'in': 2,
    'nin': 2,
    # logical
    'and': 2,
    'or': 2,
    'not': 1,
    'nor': 1,
    # collection
    'has': 2,
}
"""Default operators."""

DEFAULT_FUNCTIONS = {
    'startswith': 2,
    'endswith': 2,
    'contains': 2,
}
"""Default functions."""

OPERATOR_PRECEDENCE = {
    # comparison
    'eq': 4,
    'ne': 4,
    'gt': 4,
    'ge': 4,
    'lt': 4,
    'le': 4,
    'in': 4,
    'nin': 4,
    # collection
    'has': 4,
    # logical
    'not': 3,
    'nor': 3,
    'and': 2,
    'or': 1,
}
"""Operator precedence."""

ODATA_COMPARISON_OPERATORS = ('eq', 'ne', 'gt', 'ge', 'lt', 'le', 'in', 'nin')
"""OData comparison operators."""

ODATA_LOGICAL_OPERATORS = ('and', 'or', 'not', 'nor')
"""OData logical operators."""
