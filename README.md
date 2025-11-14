<!-- omit in toc -->
# OData V4 Query

<p align="center">
    <a href="https://pypi.org/project/odata-v4-query" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/odata-v4-query" alt="Supported Python versions">
    </a>
    <a href="https://pypi.org/project/odata-v4-query" target="_blank">
        <img src="https://img.shields.io/pypi/v/odata-v4-query" alt="Package version">
    </a>
    <a href="https://github.com/daireto/odata-v4-query/actions" target="_blank">
        <img src="https://github.com/daireto/odata-v4-query/actions/workflows/publish.yml/badge.svg" alt="Publish">
    </a>
    <a href='https://coveralls.io/github/daireto/odata-v4-query?branch=main'>
        <img src='https://coveralls.io/repos/github/daireto/odata-v4-query/badge.svg?branch=main' alt='Coverage Status' />
    </a>
    <a href="/LICENSE" target="_blank">
        <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
    </a>
</p>

A lightweight, simple and fast parser for OData V4 query options supporting
standard query parameters. Provides helper functions to apply OData V4 query
options to ORM/ODM queries such as SQLAlchemy, PyMongo and Beanie.

<!-- omit in toc -->
## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Utility Functions](#utility-functions)
    - [Beanie](#beanie)
    - [PyMongo](#pymongo)
    - [SQLAlchemy](#sqlalchemy)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- Support for the following OData V4 standard query parameters:
    - `$count` - Include count of items
    - `$expand` - Expand related entities
    - `$filter` - Filter results
    - `$format` - Response format (json, xml, csv, tsv)
    - `$orderby` - Sort results
    - `$search` - Search items
    - `$select` - Select specific fields
    - `$skip` - Skip N items
    - `$top` - Limit to N items
    - `$page` - Page number

- Comprehensive filter expression support:
    - Comparison operators: `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `in`, `nin`
    - Logical operators: `and`, `or`, `not`, `nor`
    - Collection operators: `has`
    - String functions: `startswith`, `endswith`, `contains`, `substring`, `tolower`, `toupper`
    - Nested field filtering: `user/name`, `profile/address/city`

- Utility functions to apply options to ORM/ODM queries.
    - See [utility functions](#utility-functions) for more information.

## Requirements

- `Python 3.10+`
- `beanie 1.23+ (optional, for Beanie ODM utils)`
- `pymongo 4.3+ (optional, for PyMongo utils)`
- `sqlalchemy 2.0+ (optional, for SQLAlchemy utils)`

## Installation

You can simply install odata-v4-query from
[PyPI](https://pypi.org/project/odata-v4-query/):
```bash
pip install odata-v4-query
```

To install all the optional dependencies to use all the ORM/ODM utils:
```bash
pip install odata-v4-query[all]
```

You can also install the dependencies for a specific ORM/ODM util:
```bash
pip install odata-v4-query[beanie]
pip install odata-v4-query[pymongo]
pip install odata-v4-query[sqlalchemy]
```

## Quick Start

```python
from odata_v4_query import ODataQueryParser, ODataFilterParser

# Create parser instance
parser = ODataQueryParser()

# Parse a complete URL
options = parser.parse_url('https://example.com/odata?$count=true&$top=10&$skip=20')

# Parse just the query string
options = parser.parse_query_string("$filter=name eq 'John' and age gt 25")

# Parse filter expressions
filter_parser = ODataFilterParser()
ast = filter_parser.parse("name eq 'John' and age gt 25")

# Evaluate filter expressions
filter_parser.evaluate(ast)

# Filter with nested fields
options = parser.parse_query_string("$filter=user/name eq 'Alice'")
options = parser.parse_query_string("$filter=profile/address/city eq 'Chicago'")
```

## Utility Functions

You to need to install the [required dependencies](#requirements) for the
ORM/ODM you want to use.

> [!NOTE]
> If the `$page` option is used, it is converted to `$skip` and `$top`.
> If `$top` is not provided, it defaults to 100. The `$skip` is computed as
> `(page - 1) * top`. If `$skip` is provided, it is overwritten.

### Beanie

Use the `apply_to_beanie_query()` function to apply options to a Beanie query.

```python
from beanie import Document
from odata_v4_query import ODataQueryParser
from odata_v4_query.utils.beanie import apply_to_beanie_query

class User(Document):
    name: str
    email: str
    age: int

# Create parser instance
parser = ODataQuery_parser()

# Parse a complete URL
options = parser.parse_query_string("$top=10&$skip=20&$filter=name eq 'John'")

# Apply options to a new query
query = apply_to_beanie_query(options, User)

# Apply options to an existing query
query = User.find()
query = apply_to_beanie_query(options, query)
```

Nested field filtering is supported using the `/` separator for accessing nested
document fields. Both single-level and multi-level nesting are supported:

```python
# Single-level: Filter by nested field
options = parser.parse_query_string("$filter=profile/city eq 'Chicago'")
query = apply_to_beanie_query(options, User)

# Multi-level: Filter by deeply nested field
options = parser.parse_query_string("$filter=profile/address/city eq 'Chicago'")
query = apply_to_beanie_query(options, User)

# Use with string functions
options = parser.parse_query_string("$filter=startswith(profile/city, 'Chi')")
query = apply_to_beanie_query(options, User)
```

The `$search` option is only supported if `search_fields` is provided.

```python
options = parser.parse_query_string('$search=John')

# Search "John" in "name" and "email" fields
query = apply_to_beanie_query(options, User, search_fields=['name', 'email'])
```

The `$select` option is only supported if `parse_select` is True.
If `projection_model` is provided, the results are projected with a Pydantic
model, otherwise a dictionary.

```python
from pydantic import BaseModel

class UserProjection(BaseModel):
    name: str
    email: str

options = parser.parse_query_string("$select=name,email")

# Project as a dictionary (default)
query = apply_to_beanie_query(options, User, parse_select=True)

# Project using a Pydantic model
query = apply_to_beanie_query(
    options, User, parse_select=True, projection_model=UserProjection
)
```

> [!NOTE]
> The `$expand` and `$format` options won't be applied.
> You may need to handle them manually. Also, the `substring`, `tolower` and
> `toupper` functions are not supported.

### PyMongo

Use the `get_query_from_options()` function to get a MongoDB query from options
to be applied to a PyMongo query.

```python
from pymongo import MongoClient, ASCENDING, DESCENDING
from odata_v4_query import ODataQueryParser
from odata_v4_query.utils.pymongo import PyMongoQuery, get_query_from_options

client = MongoClient()
db = client['db']

# Create parser instance
parser = ODataQuery_parser()

# Parse a complete URL
options = parser.parse_query_string("$top=10&$skip=20&$filter=name eq 'John'")

# Get a PyMongo query from options
query = get_query_from_options(options)

# Apply query to collection
db.users.find(**query)

# Using keyword arguments
db.users.find(
    skip=query.skip,
    limit=query.limit,
    filter=query.filter,
    sort=query.sort,
    projection=query.projection,
)
```

Nested field filtering is supported using the `/` separator for accessing nested
document fields. Both single-level and multi-level nesting are supported:

```python
# Single-level: Filter by nested field
options = parser.parse_query_string("$filter=profile/city eq 'Chicago'")
query = get_query_from_options(options)

# Multi-level: Filter by deeply nested field
options = parser.parse_query_string("$filter=profile/address/city eq 'Chicago'")
query = get_query_from_options(options)

# Use with string functions
options = parser.parse_query_string("$filter=contains(profile/city, 'ago')")
query = get_query_from_options(options)
```

The `$search` option is only supported if `search_fields` is provided.
It overrides the `$filter` option.

```python
options = parser.parse_query_string('$search=John')

# Search "John" in "name" and "email" fields
query = get_query_from_options(options, search_fields=['name', 'email'])
```

The `$select` option is only supported if `parse_select` is True.

```python
options = parser.parse_query_string("$select=name,email")

# Parse $select option
query = get_query_from_options(options, parse_select=True)
```

> [!NOTE]
> The `$count`, `$expand` and `$format` options won't be applied.
> You may need to handle them manually. Also, the `substring`, `tolower` and
> `toupper` functions are not supported.

### SQLAlchemy

Use the `apply_to_sqlalchemy_query()` function to apply options to a SQLAlchemy
query.

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from odata_v4_query import ODataQueryParser
from odata_v4_query.utils.sqlalchemy import apply_to_sqlalchemy_query

class User(DeclarativeBase):
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()

# Create parser instance
parser = ODataQuery_parser()

# Parse a complete URL
options = parser.parse_query_string("$top=10&$skip=20&$filter=name eq 'John'")

# Apply options to a new query
query = apply_to_sqlalchemy_query(options, User)

# Apply options to an existing query
query = select(User)
query = apply_to_sqlalchemy_query(options, query)
```

Nested field filtering is supported using the `/` separator for filtering on
related entities. Both single-level and multi-level nesting are supported:

```python
# Single-level: Filter by related entity field
options = parser.parse_query_string("$filter=user/name eq 'Alice'")
query = apply_to_sqlalchemy_query(options, Post)

# Multi-level: Filter by deeply nested field
options = parser.parse_query_string("$filter=user/profile/address/city eq 'Chicago'")
query = apply_to_sqlalchemy_query(options, Post)

# Use with string functions
options = parser.parse_query_string("$filter=tolower(user/name) eq 'alice'")
query = apply_to_sqlalchemy_query(options, Post)

# Multi-level with functions
options = parser.parse_query_string("$filter=startswith(user/profile/address/city, 'Chi')")
query = apply_to_sqlalchemy_query(options, Post)

# Combine with other filters
options = parser.parse_query_string("$filter=user/name eq 'Alice' and rating gt 3")
query = apply_to_sqlalchemy_query(options, Post)
```

The `$search` option is only supported if `search_fields` is provided.

```python
options = parser.parse_query_string('$search=John')

# Search "John" in "name" and "email" fields
query = apply_to_sqlalchemy_query(
    options, User, search_fields=['name', 'email']
)
```

The `$expand` option performs a
[joined eager loading](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html#sqlalchemy.orm.joinedload)
using left outer join.

```python
options = parser.parse_query_string('$expand=posts')

# Perform joined eager loading on "posts"
query = apply_to_sqlalchemy_query(options, User)
```

> [!NOTE]
> The `$format` option won't be applied. You may need to handle it
> manually. Also, the `has` and `nor` operators are not supported in SQL,
> so they are converted to a `LIKE` and `NOT` expressions, respectively.

## Contributing

See the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE)
file for details.

## Support

If you find this project useful, give it a ⭐ on GitHub!
