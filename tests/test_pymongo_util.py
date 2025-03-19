import pytest
from mongomock import Database

from odata_v4_query.errors import ParseError, UnexpectedNullOperand
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

    def test_filter(self, db: Database):
        # comparison and logical
        options = self.parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'John'

        options = self.parser.parse_query_string(
            '$filter=age lt 25 or age gt 35'
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 4

        options = self.parser.parse_query_string(
            "$filter=name in ('Eve', 'Frank')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'Eve'
        assert result[1]['name'] == 'Frank'

        options = self.parser.parse_query_string(
            "$filter=name nin ('Eve', 'Frank')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 8

        options = self.parser.parse_query_string(
            "$filter=name ne 'John' and name ne 'Jane'"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 8

        options = self.parser.parse_query_string(
            "$filter=not name eq 'John' and not name eq 'Jane'"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 8

        options = self.parser.parse_query_string('$filter=name eq null')
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 0

        options = self.parser.parse_query_string('$filter=name ne null')
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 10

        # string functions
        options = self.parser.parse_query_string(
            "$filter=startswith(name, 'J') and age ge 25"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'John'
        assert result[1]['name'] == 'Jane'

        options = self.parser.parse_query_string(
            "$filter=endswith(name, 'e')"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 5
        assert result[0]['name'] == 'Jane'
        assert result[1]['name'] == 'Alice'
        assert result[2]['name'] == 'Charlie'
        assert result[3]['name'] == 'Eve'
        assert result[4]['name'] == 'Grace'

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

        # collection
        options = self.parser.parse_query_string(
            "$filter=addresses has '101 Main St'"
        )
        query = get_query_from_options(options)
        result = list(db.users.find(**query))
        assert len(result) == 2
        assert result[0]['name'] == 'Alice'
        assert result[1]['name'] == 'Bob'

    def test_search(self, db: Database):
        options = self.parser.parse_query_string('$search=John')
        query = get_query_from_options(
            options, search_fields=['name', 'email']
        )
        result = list(db.users.find(**query))
        assert len(result) == 1
        assert result[0]['name'] == 'John'

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

    def test_error(self):
        # unexpected null filters
        with pytest.raises(ParseError):
            options = ODataQueryOptions(filter_=FilterNode(type_='value'))
            get_query_from_options(options)

        # null left or right operands
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='eq')
            )
            get_query_from_options(options)

        # null left or right values
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='eq',
                    left=FilterNode(type_='identifier'),
                    right=FilterNode(type_='literal', value='John'),
                )
            )
            get_query_from_options(options)

        # null list arguments
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='in',
                    left=FilterNode(type_='identifier', value='name'),
                    right=FilterNode(type_='list'),
                )
            )
            get_query_from_options(options)

        # null operand for has operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(
                    type_='operator',
                    value='has',
                    left=FilterNode(type_='identifier', value='addresses'),
                    right=FilterNode(type_='literal'),
                )
            )
            get_query_from_options(options)

        # null operand for and/or operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='and')
            )
            get_query_from_options(options)

        # null operand for not/nor operator
        with pytest.raises(UnexpectedNullOperand):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='not')
            )
            get_query_from_options(options)

        # unknown operator
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='operator', value='unknown')
            )
            get_query_from_options(options)

        # null function
        with pytest.raises(ParseError):
            options = ODataQueryOptions(filter_=FilterNode(type_='function'))
            get_query_from_options(options)

        # null function arguments
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
                filter_=FilterNode(type_='function', value='startswith')
            )
            get_query_from_options(options)

        # more than 2 function arguments
        with pytest.raises(ParseError):
            options = ODataQueryOptions(
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
            get_query_from_options(options)

        # null function operand
        with pytest.raises(ParseError):
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
            get_query_from_options(options)

        # unknown function
        with pytest.raises(ParseError):
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
            get_query_from_options(options)
