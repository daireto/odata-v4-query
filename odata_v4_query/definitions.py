"""Definitions for OData V4 query options."""

DEFAULT_LIMIT = 100

DEFAULT_ORDERBY_DIRECTION = 'asc'

DEFAULT_FORMAT_OPTIONS = ('json', 'xml', 'csv', 'tsv')

# comparison
EQ = 'eq'
NE = 'ne'
GT = 'gt'
GE = 'ge'
LT = 'lt'
LE = 'le'
IN = 'in'
NIN = 'nin'

# logical
AND = 'and'
OR = 'or'
NOT = 'not'
NOR = 'nor'

# collection
HAS = 'has'

# functions
STARTSWITH = 'startswith'
ENDSWITH = 'endswith'
CONTAINS = 'contains'
SUBSTRING = 'substring'
TOLOWER = 'tolower'
TOUPPER = 'toupper'

COMPARISON_OPERATORS = (EQ, NE, GT, GE, LT, LE, IN, NIN)

LOGICAL_OPERATORS = (AND, OR, NOT, NOR)

FUNCTION_ARITY = {
    STARTSWITH: 2,
    ENDSWITH: 2,
    CONTAINS: 2,
    SUBSTRING: 3,
    TOLOWER: 1,
    TOUPPER: 1,
}

OPERATOR_ARITY = {
    # comparison
    EQ: 2,
    NE: 2,
    GT: 2,
    GE: 2,
    LT: 2,
    LE: 2,
    IN: 2,
    NIN: 2,
    # logical
    AND: 2,
    OR: 2,
    NOT: 1,
    NOR: 1,
    # collection
    HAS: 2,
}

OPERATOR_PRECEDENCE = {
    # comparison
    EQ: 4,
    NE: 4,
    GT: 4,
    GE: 4,
    LT: 4,
    LE: 4,
    IN: 4,
    NIN: 4,
    # collection
    HAS: 4,
    # logical
    NOT: 3,
    NOR: 3,
    AND: 2,
    OR: 1,
}
