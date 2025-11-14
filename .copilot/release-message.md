# Release message generation instructions

Compare the current branch (develop) and main branch, check the commit history since the last commit in main that has a message like "ci: version X.Y.Z" and generate the message for the next version. Release message should be in markdown format and include a summary of the changes, new features, breaking changes (important if any), and any other relevant information. Check the following examples:

This is the release description of the 0.4.0 version:

```markdown
## [0.4.0](https://github.com/daireto/odata-v4-query/compare/v0.3.0...v0.4.0) (2025-11-13)

> This release introduces major enhancements including nested field filtering support, new string functions, improved query options handling, and comprehensive test coverage improvements.

### Added

- **Nested field filtering support** for all backends (SQLAlchemy, Beanie, PyMongo):
  - Single-level nesting: `user/name`
  - Multi-level nesting: `user/profile/address/city`
  - Support for nested fields with all operators and functions

- **New string functions**:
  - `substring` - Extract substring from a string
  - `tolower` - Convert string to lowercase
  - `toupper` - Convert string to uppercase

- **Enhanced query options**:
  - `clone()` method for `ODataQueryOptions` supporting deep and shallow copying
  - `remove_pagination_options()` utility function
  - `$count` option support in SQLAlchemy and Beanie utilities

- **New error classes** for better error handling:
  - `AggregationOperatorNotSupportedError`
  - `UnexpectedNumberOfArgumentsError`

### Breaking Changes

- `TwoArgumentsExpectedError` has been replaced by `UnexpectedNumberOfArgumentsError`.

### Enhancements

- **Improved number handling** in tokenizer to support negative numbers
- **Enhanced filter node parsers** with comprehensive function parsing capabilities:
  - `BaseFilterNodeParser` with extensible function parsing architecture
  - `SQLAlchemyFilterNodeParser` with nested relationship traversal using `has()`
  - `MongoDBFilterNodeParser` with proper field path normalization

- **Better documentation**:
  - Comprehensive docstrings for all utility functions
  - Detailed parameter and return type descriptions
  - Examples for nested field filtering in README
  - Clarified unsupported functions and options for each backend

### Fixed

- Removed `add_note` function call to fix compatibility with Python <3.11 versions
- Fixed async cursor handling in Beanie by monkey patching `AggregationQuery`

### Refactored

- Organized imports and updated `__all__` exports in utility modules
- Improved code formatting and consistency across test files

### Testing

- **Significantly improved test coverage** (100% coverage achieved):
  - Added 30+ new tests for nested field filtering
  - Added tests for new string functions (`substring`, `tolower`, `toupper`)
  - Added tests for `clone()` method and pagination removal
  - Added tests for `$count` option handling
  - Enhanced edge case and error handling tests

- **Coverage configuration**:
  - Excluded test files from coverage reports
  - Added pragma comments for defensive code paths

### Documentation

- Updated README with comprehensive examples for:
  - Nested field filtering (single and multi-level)
  - New string functions
  - Unsupported features per backend
- Enhanced inline documentation with detailed examples and parameter descriptions

### Performance

- Improved filter parsing efficiency with optimized field path resolution
- Better memory management by removing unnecessary caching

---

### Summary of Changes

- **22 files changed**: 1,631 insertions(+), 221 deletions(-)
- **Test coverage**: Achieved 100% coverage (950 statements)
- **Total tests**: 175 tests (up from 170)
- **New features**: Nested field filtering, 3 new string functions, query cloning
- **Compatibility**: Fixed Python 3.10 compatibility issues

This release significantly enhances the library's filtering capabilities and brings it closer to full OData V4 specification compliance, particularly with comprehensive nested field filtering support across all backends.

```

And this is the release description of the 0.3.0 version:

```markdown
## [0.3.0](https://github.com/daireto/odata-v4-query/compare/v0.2.0...v0.3.0) (2025-06-07)

> This release introduces refinements, performance improvements, and stricter enforcement of predefined operators and functions.

### Enhancements

- Improved linting and formatting configurations with the addition of Ruff linter.
- Refined `parse_in_nin_operators` method to `parse_membership_operators` for better clarity.

### Security

- Added a security policy document (`SECURITY.md`) specifying guidelines for reporting vulnerabilities.

### Fixed

- Addressed an import error.
- Fixed memory leak issues by removing unnecessary use of `lru_cache`.
- Corrected linting issues and improved code consistency.
- Ensured exceptions are raised when order direction values are not `"asc"` or `"desc"`.

### Refactored

- Enforced predefined operators and functions by removing constructor-based initialization.
- Replaced generic `ParseError` and `EvaluateError` with specific exception classes.
- Streamlined handling of operators and functions by introducing centralized arity management.

### Documentation

- Updated contributing guidelines, especially commit message conventions.
- Removed the unnecessary "Raises" section from documentation.

### Other

- Excluded the `tests` folder from linting but kept it for formatting.

#### Breaking Changes

- **Removed error classes**:
  - `EvaluateError`
  - `ParseError`

- **Renamed error classes**:
  - `NoPositiveIntegerValue` → `NoPositiveError`
  - `NoRootClassFound` → `NoRootClassError`
  - `UnexpectedNullOperand` → `UnexpectedNullOperatorError`
  - `UnsupportedFormat` → `UnsupportedFormatError`

- **Added error classes**:
  - `InvalidOrderDirectionError`
  - `OpeningParenthesisExpectedError`
  - `CommaOrClosingParenthesisExpectedError`
  - `MissingClosingParenthesisError`
  - `NoNumericValueError`
  - `TwoArgumentsExpectedError`
  - `UnexpectedEmptyArgumentsError`
  - `UnexpectedEndOfExpressionError`
  - `UnexpectedNullFiltersError`
  - `UnexpectedNullFunctionNameError`
  - `UnexpectedNullIdentifierError`
  - `UnexpectedNullListError`
  - `UnexpectedNullLiteralError`
  - `UnexpectedNullNodeTypeError`
  - `UnexpectedNullOperandError`
  - `UnexpectedTokenError`
  - `UnknownFunctionError`
  - `UnknownNodeTypeError`
  - `UnknownOperatorError`
```

And this is the example for the 0.2.0 version:

```markdown
## [0.2.0](https://github.com/daireto/odata-v4-query/compare/v0.1.0...v0.2.0) (2025-03-19)

> Introduces the `$page` option and improves `README.md`.

### Added
 - Support for `$page` option.

### Documentation
- Added examples for `$search` and `$select` options in ORM/ODM integration helpers.

```

Release message: