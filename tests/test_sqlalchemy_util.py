import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

from odata_v4_query.errors import (
    NoRootClassError,
    UnexpectedNumberOfArgumentsError,
    UnexpectedEmptyArgumentsError,
    UnexpectedNullFiltersError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnknownFunctionError,
    UnknownOperatorError,
)
from odata_v4_query.filter_parser import FilterNode
from odata_v4_query.query_parser import ODataQueryOptions, ODataQueryParser
from odata_v4_query.utils.sqlalchemy import (
    apply_to_sqlalchemy_query,
    get_query_root_cls,
)

from ._core.sqlalchemy import Post, User, get_engine, seed_data


@pytest.fixture(scope='session')
def session():
    engine = get_engine()
    with Session(engine) as session:
        seed_data(session)
        yield session


class TestSQLAlchemy:
    parser = ODataQueryParser()

    def test_skip(self, session: Session):
        query = select(User)
        users_count = len(session.scalars(query).all())
        options = self.parser.parse_query_string('$skip=2')
        query = apply_to_sqlalchemy_query(options, query)
        result = session.scalars(query).all()
        assert len(result) == users_count - 2
        assert result[0].name == 'Alice'

    def test_top(self, session: Session):
        options = self.parser.parse_query_string('$top=2')
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].name == 'John'
        assert result[1].name == 'Jane'

    def test_page(self, session: Session):
        query = select(User)
        users_count = len(session.scalars(query).all())
        options1 = self.parser.parse_query_string('$page=1')
        query1 = apply_to_sqlalchemy_query(options1, User)
        result1 = session.scalars(query1).all()
        options2 = self.parser.parse_query_string('$page=1&$top=4')
        query2 = apply_to_sqlalchemy_query(options2, User)
        result2 = session.scalars(query2).all()
        options3 = self.parser.parse_query_string('$page=2&$top=4')
        query3 = apply_to_sqlalchemy_query(options3, User)
        result3 = session.scalars(query3).all()
        options4 = self.parser.parse_query_string('$page=3&$top=4')
        query4 = apply_to_sqlalchemy_query(options4, User)
        result4 = session.scalars(query4).all()
        options5 = self.parser.parse_query_string('$page=4&$top=4')
        query5 = apply_to_sqlalchemy_query(options5, User)
        result5 = session.scalars(query5).all()
        assert len(result1) == users_count
        assert len(result2) == 4
        assert len(result3) == 4
        assert len(result4) == 2
        assert len(result5) == 0

    def test_filter_comparison_and_logical(self, session: Session):
        options1 = self.parser.parse_query_string(
            "$filter=name eq 'John' and age ge 25"
        )
        query1 = apply_to_sqlalchemy_query(options1, User)
        result1 = session.scalars(query1).all()
        options2 = self.parser.parse_query_string('$filter=age lt 25 or age gt 35')
        query2 = apply_to_sqlalchemy_query(options2, User)
        result2 = session.scalars(query2).all()
        options3 = self.parser.parse_query_string("$filter=name in ('Eve', 'Frank')")
        query3 = apply_to_sqlalchemy_query(options3, User)
        result3 = session.scalars(query3).all()
        options4 = self.parser.parse_query_string("$filter=name nin ('Eve', 'Frank')")
        query4 = apply_to_sqlalchemy_query(options4, User)
        result4 = session.scalars(query4).all()
        options5 = self.parser.parse_query_string(
            "$filter=name ne 'John' and name ne 'Jane'"
        )
        query5 = apply_to_sqlalchemy_query(options5, User)
        result5 = session.scalars(query5).all()
        options6 = self.parser.parse_query_string(
            "$filter=not name eq 'John' and not name eq 'Jane'"
        )
        query6 = apply_to_sqlalchemy_query(options6, User)
        result6 = session.scalars(query6).all()
        assert len(result1) == 1
        assert result1[0].name == 'John'
        assert len(result2) == 4
        assert len(result3) == 2
        assert result3[0].name == 'Eve'
        assert result3[1].name == 'Frank'
        assert len(result4) == 8
        assert len(result5) == 8
        assert len(result6) == 8

    def test_filter_null(self, session: Session):
        options1 = self.parser.parse_query_string('$filter=name eq null')
        query1 = apply_to_sqlalchemy_query(options1, User)
        result1 = session.scalars(query1).all()
        options2 = self.parser.parse_query_string('$filter=name ne null')
        query2 = apply_to_sqlalchemy_query(options2, User)
        result2 = session.scalars(query2).all()
        assert len(result1) == 0
        assert len(result2) == 10

    def test_filter_startswith_function(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=startswith(name, 'J') and age ge 25"
        )
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].name == 'John'
        assert result[1].name == 'Jane'

    def test_filter_endswith_function(self, session: Session):
        options = self.parser.parse_query_string("$filter=endswith(name, 'e')")
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 5
        assert result[0].name == 'Jane'
        assert result[1].name == 'Alice'
        assert result[2].name == 'Charlie'
        assert result[3].name == 'Eve'
        assert result[4].name == 'Grace'

    def test_filter_contains_function(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=contains(name, 'i') and age le 35"
        )
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].name == 'Alice'
        assert result[0].age == 35
        assert result[1].name == 'Charlie'
        assert result[1].age == 32

    def test_filter_substring_function(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=substring(name, 1, 2) eq 'oh'"
        )
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].name == 'John'

        options = self.parser.parse_query_string(
            "$filter=substring(name, 1, -1) eq 'lice'"
        )
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].name == 'Alice'

    def test_filter_tolower_function(self, session: Session):
        options = self.parser.parse_query_string("$filter=tolower(name) eq 'john'")
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].name == 'John'

    def test_filter_toupper_function(self, session: Session):
        options = self.parser.parse_query_string("$filter=toupper(name) eq 'ALICE'")
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].name == 'Alice'

    def test_filter_has(self, session: Session):
        options = self.parser.parse_query_string("$filter=addresses has '101 Main St'")
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].name == 'Alice'
        assert result[1].name == 'Bob'

    def test_search(self, session: Session):
        options = self.parser.parse_query_string('$search=John')
        query = apply_to_sqlalchemy_query(
            options, User, search_fields=['name', 'email']
        )
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].name == 'John'

    def test_orderby(self, session: Session):
        options = self.parser.parse_query_string('$orderby=name asc,age desc')
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).all()
        assert len(result) == 10
        assert result[0].name == 'Alice'
        assert result[1].name == 'Bob'
        assert result[1].age == 40
        assert result[2].name == 'Bob'
        assert result[2].age == 28
        assert result[3].name == 'Charlie'
        assert result[4].name == 'David'
        assert result[5].name == 'Eve'
        assert result[6].name == 'Frank'
        assert result[7].name == 'Grace'
        assert result[8].name == 'Jane'
        assert result[9].name == 'John'

    def test_expand(self, session: Session):
        options = self.parser.parse_query_string('$expand=posts')
        query = apply_to_sqlalchemy_query(options, User)
        result = session.scalars(query).unique().all()
        assert result[0].posts[0].title == 'Post 1'
        assert result[0].posts[1].title == 'Post 2'
        assert result[1].posts[0].title == 'Post 3'
        assert result[1].posts[1].title == 'Post 4'

    def test_count(self, session: Session):
        options = self.parser.parse_query_string('$count=true')
        query = apply_to_sqlalchemy_query(options, User)
        result = session.execute(query).all()
        assert len(result) == 1
        assert result[0][0] == 10

    def test_select(self, session: Session):
        options = self.parser.parse_query_string('$select=name,email')
        query = apply_to_sqlalchemy_query(options, User)
        result = session.execute(query).all()
        assert len(result) == 10
        assert result[0][0] == 'John'
        assert result[0][1] == 'john@example.com'

    def test_filter_nested_field_eq(self, session: Session):
        options = self.parser.parse_query_string("$filter=user/name eq 'John'")
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 1'
        assert result[1].title == 'Post 2'

    def test_filter_nested_field_comparison(self, session: Session):
        options = self.parser.parse_query_string(
            '$filter=user/age gt 25 and rating ge 3'
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].title == 'Post 3'
        assert result[0].user.name == 'Jane'

    def test_filter_nested_field_startswith(self, session: Session):
        options = self.parser.parse_query_string("$filter=startswith(user/name, 'J')")
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 4
        titles = [r.title for r in result]
        assert 'Post 1' in titles
        assert 'Post 2' in titles
        assert 'Post 3' in titles
        assert 'Post 4' in titles

    def test_filter_nested_field_contains(self, session: Session):
        options = self.parser.parse_query_string("$filter=contains(user/email, 'jane')")
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 3'
        assert result[1].title == 'Post 4'

    def test_filter_nested_field_endswith(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=endswith(user/email, 'example.com')"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 4

    def test_filter_nested_field_tolower(self, session: Session):
        options = self.parser.parse_query_string("$filter=tolower(user/name) eq 'john'")
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 1'
        assert result[1].title == 'Post 2'

    def test_filter_nested_field_toupper(self, session: Session):
        options = self.parser.parse_query_string("$filter=toupper(user/name) eq 'JANE'")
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 3'
        assert result[1].title == 'Post 4'

    def test_filter_nested_field_and_operator(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=user/name eq 'Jane' and rating eq 3"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 1
        assert result[0].title == 'Post 3'

    def test_filter_multi_level_nested_field_eq(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=user/profile/address/city eq 'Chicago'"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 3'
        assert result[1].title == 'Post 4'

    def test_filter_multi_level_nested_field_comparison(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=user/profile/address/country eq 'USA'"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 4

    def test_filter_multi_level_nested_field_startswith(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=startswith(user/profile/address/city, 'Chi')"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2

    def test_filter_multi_level_nested_field_tolower(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=tolower(user/profile/address/city) eq 'chicago'"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2

    def test_filter_multi_level_nested_field_and_operator(self, session: Session):
        options = self.parser.parse_query_string(
            "$filter=user/profile/address/country eq 'USA' and rating ge 4"
        )
        query = apply_to_sqlalchemy_query(options, Post)
        result = session.scalars(query).all()
        assert len(result) == 2
        assert result[0].title == 'Post 1'
        assert result[1].title == 'Post 2'

    def test_unexpected_null_filters(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='value'))
        with pytest.raises(UnexpectedNullFiltersError):
            apply_to_sqlalchemy_query(options, User)

    def test_unexpected_null_operator(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='operator'))
        with pytest.raises(UnexpectedNullOperatorError):
            apply_to_sqlalchemy_query(options, User)

    def test_unexpected_null_operand(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='operator', value='eq'))
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options, User)

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
            apply_to_sqlalchemy_query(options, User)

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
            apply_to_sqlalchemy_query(options1, User)
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options2, User)

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
            apply_to_sqlalchemy_query(options, User)

    def test_unexpected_null_operand_for_and_or_operators(self):
        options1 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='and'))
        options2 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='or'))
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options1, User)
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options2, User)

    def test_unexpected_null_operand_for_not_nor_operators(self):
        options1 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='not'))
        options2 = ODataQueryOptions(filter_=FilterNode(type_='operator', value='nor'))
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options1, User)
        with pytest.raises(UnexpectedNullOperandError):
            apply_to_sqlalchemy_query(options2, User)

    def test_unknown_operator(self):
        options = ODataQueryOptions(
            filter_=FilterNode(type_='operator', value='unknown')
        )
        with pytest.raises(UnknownOperatorError):
            apply_to_sqlalchemy_query(options, User)

    def test_unexpected_null_function_name(self):
        options = ODataQueryOptions(filter_=FilterNode(type_='function'))
        with pytest.raises(UnexpectedNullFunctionNameError):
            apply_to_sqlalchemy_query(options, User)

    def test_unexpected_empty_arguments(self):
        options = ODataQueryOptions(
            filter_=FilterNode(type_='function', value='startswith')
        )
        with pytest.raises(UnexpectedEmptyArgumentsError):
            apply_to_sqlalchemy_query(options, User)

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
            apply_to_sqlalchemy_query(options1, User)
        with pytest.raises(UnexpectedNumberOfArgumentsError):
            apply_to_sqlalchemy_query(options2, User)

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
            apply_to_sqlalchemy_query(options, User)

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
            apply_to_sqlalchemy_query(options, User)

    def test_no_root_class(self):
        query = select(func.count('*'))
        options1 = self.parser.parse_query_string('$filter=name eq null')
        options2 = self.parser.parse_query_string('$search=John')
        options3 = self.parser.parse_query_string('$orderby=name asc')
        options4 = self.parser.parse_query_string('$expand=posts')
        options5 = self.parser.parse_query_string('$select=name,email')
        with pytest.raises(NoRootClassError):
            get_query_root_cls(query, raise_on_none=True)
        with pytest.raises(NoRootClassError):
            apply_to_sqlalchemy_query(options1, query)
        with pytest.raises(NoRootClassError):
            apply_to_sqlalchemy_query(options2, query, search_fields=['name'])
        with pytest.raises(NoRootClassError):
            apply_to_sqlalchemy_query(options3, query)
        with pytest.raises(NoRootClassError):
            apply_to_sqlalchemy_query(options4, query)
        with pytest.raises(NoRootClassError):
            apply_to_sqlalchemy_query(options5, query)
