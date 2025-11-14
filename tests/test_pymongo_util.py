import pytest
from mongomock import Database

from odata_v4_query.errors import (
    AggregationOperatorNotSupportedError,
    UnexpectedEmptyArgumentsError,
    UnexpectedNullFiltersError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnexpectedNumberOfArgumentsError,
    UnexpectedTypeError,
    UnknownFunctionError,
    UnknownOperatorError,
)
from odata_v4_query.filter_parser import FilterNode
from odata_v4_query.query_parser import ODataQueryOptions, ODataQueryParser
from odata_v4_query.utils.pymongo import PyMongoQuery, get_query_from_options

from ._core.pymongo import get_client, seed_data


@pytest.fixture(scope='session')
def db():
    client = get_client()
    db = client['db']
    seed_data(db)
    return db


class TestBeanie:
    parser = ODataQueryParser()

    def test_py_mongo_query_class(self):
        query = PyMongoQuery(skip=1, limit=10, filter={'name': 'John'})
        assert query.skip == 1
        assert query.limit == 10
        assert query.filter == {'name': 'John'}
        assert query['skip'] == 1
        assert query['limit'] == 10
        assert query['filter'] == {'name': 'John'}

        query.skip = 2
        assert query.skip == 2
        assert query['skip'] == 2

        query['skip'] = 3
        assert query.skip == 3
        assert query['skip'] == 3

    def test_skip(self, db: Database):
        users_count = len(list(db.users.find()))
        options = self.parser.parse_query_string('$skip=2')
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == users_count - 2
        assert result[0]['name'] == 'Alice'

    def test_top(self, db: Database):
        options = self.parser.parse_query_string('$top=2')
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'John'
        assert result[1]['name'] == 'Jane'

    def test_page(self, db: Database):
        users_count = len(list(db.users.find()))
        options1 = self.parser.parse_query_string('$page=1')
        query1 = get_query_from_options(options1)
        result1 = list(db.users.find(**query1))
        options2 = self.parser.parse_query_string('$page=1&$top=4')
        query2 = get_query_from_options(options2)
        result2 = list(db.users.find(**query2))
        options3 = self.parser.parse_query_string('$page=2&$top=4')
        query3 = get_query_from_options(options3)
        result3 = list(db.users.find(**query3))
        options4 = self.parser.parse_query_string('$page=3&$top=4')
        query4 = get_query_from_options(options4)
        result4 = list(db.users.find(**query4))
        options5 = self.parser.parse_query_string('$page=4&$top=4')
        query5 = get_query_from_options(options5)
        result5 = list(db.users.find(**query5))
        assert len(result1) == users_count
        assert len(result2) == 4
        assert len(result3) == 4
        assert len(result4) == 2
        assert len(result5) == 0

    def test_filter_comparison(self, db: Database):
        options1 = self.parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25"
        )
        query1 = get_query_from_options(options1)
        result1 = list(db.users.find(**query1))
        options2 = self.parser.parse_query_string('$filter=age lt 25 or age gt 35')
        query2 = get_query_from_options(options2)
        result2 = list(db.users.find(**query2))
        options3 = self.parser.parse_query_string("$filter=name in ('Eve', 'Frank')")
        query3 = get_query_from_options(options3)
        result3 = list(db.users.find(**query3))
        options4 = self.parser.parse_query_string("$filter=name nin ('Eve', 'Frank')")
        query4 = get_query_from_options(options4)
        result4 = list(db.users.find(**query4))
        assert len(result1) == 1
        assert result1[0]['name'] == 'John'
        assert len(result2) == 4
        assert len(result3) == 2
        assert result3[0]['name'] == 'Eve'
        assert result3[1]['name'] == 'Frank'
        assert len(result4) == 8

    def test_filter_logical(self, db: Database):
        options1 = self.parser.parse_query_string(
            "$filter=name ne 'John' and name ne 'Jane'"
        )
        query1 = get_query_from_options(options1)
        result1 = list(db.users.find(**query1))
        options2 = self.parser.parse_query_string(
            "$filter=not name eq 'John' and not name eq 'Jane'"
        )
        query2 = get_query_from_options(options2)
        result2 = list(db.users.find(**query2))
        assert len(result1) == 8
        assert len(result2) == 8

    def test_filter_null(self, db: Database):
        options1 = self.parser.parse_query_string('$filter=name eq null')
        query1 = get_query_from_options(options1)
        result1 = list(db.users.find(**query1))
        options2 = self.parser.parse_query_string('$filter=name ne null')
        query2 = get_query_from_options(options2)
        result2 = list(db.users.find(**query2))
        assert len(result1) == 0
        assert len(result2) == 10

    def test_filter_startswith_function(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=startswith(name, 'J') and age ge 25"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'John'
        assert result[1]['name'] == 'Jane'

    def test_filter_endswith_function(self, db: Database):
        options = self.parser.parse_query_string("$filter=endswith(name, 'e')")
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 5
        assert result[0]['name'] == 'Jane'
        assert result[1]['name'] == 'Alice'
        assert result[2]['name'] == 'Charlie'
        assert result[3]['name'] == 'Eve'
        assert result[4]['name'] == 'Grace'

    def test_filter_contains_function(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=contains(name, 'i') and age le 35"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'Alice'
        assert result[0]['age'] == 35
        assert result[1]['name'] == 'Charlie'
        assert result[1]['age'] == 32

    def test_filter_substring_function(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=substring(name, 1, 3) eq 'ohn'"
        )
        with pytest.raises(AggregationOperatorNotSupportedError):
            get_query_from_options(options)

    def test_filter_tolower_function(self, db: Database):
        options = self.parser.parse_query_string("$filter=tolower(name) eq 'john'")
        with pytest.raises(AggregationOperatorNotSupportedError):
            get_query_from_options(options)

    def test_filter_toupper_function(self, db: Database):
        options = self.parser.parse_query_string("$filter=toupper(name) eq 'ALICE'")
        with pytest.raises(AggregationOperatorNotSupportedError):
            get_query_from_options(options)

    def test_filter_has(self, db: Database):
        options = self.parser.parse_query_string("$filter=addresses has '101 Main St'")
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'Alice'
        assert result[1]['name'] == 'Bob'

    def test_search(self, db: Database):
        options = self.parser.parse_query_string('$search=John')
        query = get_query_from_options(options, search_fields=['name', 'email'])
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'John'

    def test_filter_and_search_merge(self, db: Database):
        options = self.parser.parse_query_string('$filter=age gt 30&$search=a')
        query = get_query_from_options(options, search_fields=['name'])
        result = list(db.users.find(**query))
        # Should find users with age > 30 AND name containing 'a' (case-sensitive)
        assert len(result) == 3
        names = [r['name'] for r in result]
        assert 'Charlie' in names  # age 32, name contains 'a'
        assert 'David' in names  # age 41, name contains 'a'
        assert 'Grace' in names  # age 37, name contains 'a'

    def test_orderby(self, db: Database):
        options = self.parser.parse_query_string('$orderby=name asc,age desc')
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 10
        assert result[0]['name'] == 'Alice'
        assert result[1]['name'] == 'Bob'
        assert result[1]['age'] == 40
        assert result[2]['name'] == 'Bob'
        assert result[2]['age'] == 28
        assert result[3]['name'] == 'Charlie'
        assert result[4]['name'] == 'David'
        assert result[5]['name'] == 'Eve'
        assert result[6]['name'] == 'Frank'
        assert result[7]['name'] == 'Grace'
        assert result[8]['name'] == 'Jane'
        assert result[9]['name'] == 'John'

    def test_select(self, db: Database):
        options = self.parser.parse_query_string('$select=name,email')
        query = get_query_from_options(options, parse_select=True)
        result = list(db.users.find(**query))
        assert len(result) == 10
        assert result[0]['name'] == 'John'
        assert result[0]['email'] == 'john@example.com'

    def test_filter_nested_field_eq(self, db: Database):
        options = self.parser.parse_query_string("$filter=profile/city eq 'Chicago'")
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'Alice'
        assert result[0]['profile']['city'] == 'Chicago'

    def test_filter_nested_field_comparison(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=profile/city eq 'New York' and age gt 20"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'John'

    def test_filter_nested_field_startswith(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=startswith(profile/city, 'San')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 3
        names = [r['name'] for r in result]
        assert 'David' in names  # San Antonio
        assert 'Eve' in names  # San Diego
        assert 'Grace' in names  # San Jose

    def test_filter_nested_field_contains(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=contains(profile/city, 'Angeles')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'Jane'

    def test_filter_nested_field_in_operator(self, db: Database):
        options = self.parser.parse_query_string(
            "$filter=profile/city in ('Chicago', 'Houston', 'Dallas')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 3
        names = [r['name'] for r in result]
        assert 'Alice' in names  # Chicago
        assert 'Bob' in names  # Houston
        assert 'Frank' in names  # Dallas

    def test_filter_nested_field_has_operator(self, db: Database):
        options = self.parser.parse_query_string("$filter=profile/country has 'USA'")
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 10

    def test_unexpected_null_filters(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='value'))
        with pytest.raises(UnexpectedNullFiltersError):
            get_query_from_options(options)

    def test_unexpected_null_operator(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='operator'))
        with pytest.raises(UnexpectedNullOperatorError):
            get_query_from_options(options)

    def test_unexpected_null_operand(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='operator', value='eq'))
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options)

    def test_unexpected_null_operand_value(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='operator',
                value='eq',
                left=FilterNode(type_='identifier'),
                right=FilterNode(type_='literal', value='John'),
            )
        )
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options)

    def test_unexpected_null_operand_for_in_nin_operators(self):
        options1 = ODataQueryOptions(
            filter_=FilterNode(
                type_='operator',
                value='in',
                left=FilterNode(type_='identifier', value='name'),
                right=FilterNode(type_='list'),
            )
        )
        options2 = ODataQueryOptions(
            filter_=FilterNode(
                type_='operator',
                value='nin',
                left=FilterNode(type_='identifier', value='name'),
                right=FilterNode(type_='list'),
            )
        )
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options1)
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options2)

    def test_unexpected_null_operand_for_has_operator(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='operator',
                value='has',
                left=FilterNode(type_='identifier', value='addresses'),
                right=FilterNode(type_='literal'),
            )
        )
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options)

    def test_unexpected_null_operand_for_and_or_operators(self):
        options1 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='and'))
        options2 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='or'))
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options1)
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options2)

    def test_unexpected_null_operand_for_not_nor_operators(self):
        options1 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='not'))
        options2 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='nor'))
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options1)
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options2)

    def test_unknown_operator(self):
        options = ODataQueryOptions(
            filter_=FilterNode(type_='operator', value='unknown')
        )
        with pytest.raises(UnknownOperatorError):
            get_query_from_options(options)

    def test_unexpected_null_function_name(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='function'))
        with pytest.raises(UnexpectedNullFunctionNameError):
            get_query_from_options(options)

    def test_unexpected_empty_arguments(self):
        options = ODataQueryOptions(
            filter_=FilterNode(type_='function', value='startswith')
        )
        with pytest.raises(UnexpectedEmptyArgumentsError):
            get_query_from_options(options)

    def test_unexpected_number_of_arguments(self):
        options1 = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='startswith',
                arguments=[
                    FilterNode(type_='identifier', value='name'),
                    FilterNode(type_='literal', value='J'),
                    FilterNode(type_='literal', value='J'),
                ],
            )
        )
        options2 = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='substring',
                arguments=[
                    FilterNode(type_='identifier', value='name'),
                    FilterNode(type_='literal', value=1),
                ],
            )
        )
        with pytest.raises(UnexpectedNumberOfArgumentsError):
            get_query_from_options(options1)
        with pytest.raises(UnexpectedNumberOfArgumentsError):
            get_query_from_options(options2)

    def test_unexpected_null_operand_for_function(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='startswith',
                arguments=[
                    FilterNode(type_='identifier', value='name'),
                    FilterNode(type_='literal'),
                ],
            )
        )
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options)

    def test_unknown_function(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='unknown',
                arguments=[
                    FilterNode(type_='identifier', value='name'),
                    FilterNode(type_='literal', value='J'),
                ],
            )
        )
        with pytest.raises(UnknownFunctionError):
            get_query_from_options(options)

    def test_function_with_null_field(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='startswith',
                arguments=[
                    FilterNode(type_='identifier'),
                    FilterNode(type_='literal', value='J'),
                ],
            )
        )
        with pytest.raises(UnexpectedNullOperandError):
            get_query_from_options(options)

    def test_function_with_invalid_type(self):
        options = ODataQueryOptions(
            filter_=FilterNode(
                type_='function',
                value='substring',
                arguments=[
                    FilterNode(type_='identifier', value='name'),
                    FilterNode(type_='literal', value='invalid'),
                    FilterNode(type_='literal', value=2),
                ],
            )
        )
        with pytest.raises(UnexpectedTypeError):
            get_query_from_options(options)
