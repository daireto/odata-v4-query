import pytest

from odata_v4_query.errors import EvaluateError, ParseError
from odata_v4_query.filter_parser import FilterNode, ODataFilterParser


class TestFilterParser:

    parser = ODataFilterParser()

    def test_parse(self):
        ast = self.parser.parse("name eq 'John' and age gt 25")
        assert ast.type_ == 'operator'
        assert ast.value == 'and'
        assert ast.left is not None
        assert ast.left.type_ == 'operator'
        assert ast.left.value == 'eq'
        assert ast.left.left is not None
        assert ast.left.left.type_ == 'identifier'
        assert ast.left.left.value == 'name'
        assert ast.left.right is not None
        assert ast.left.right.type_ == 'literal'
        assert ast.left.right.value == 'John'
        assert ast.right is not None
        assert ast.right.type_ == 'operator'
        assert ast.right.value == 'gt'
        assert ast.right.left is not None
        assert ast.right.left.type_ == 'identifier'
        assert ast.right.left.value == 'age'
        assert ast.right.right is not None
        assert ast.right.right.type_ == 'literal'
        assert ast.right.right.value == 25

        ast = self.parser.parse('')
        assert ast.type_ == 'value'
        assert ast.value is None

    def test_parse_in(self):
        ast = self.parser.parse("name in ('John', 'Jane')")
        assert ast.type_ == 'operator'
        assert ast.value == 'in'
        assert ast.left is not None
        assert ast.left.type_ == 'identifier'
        assert ast.left.value == 'name'
        assert ast.right is not None
        assert ast.right.type_ == 'list'
        assert ast.right.arguments is not None
        assert ast.right.arguments[0].type_ == 'literal'
        assert ast.right.arguments[0].value == 'John'
        assert ast.right.arguments[1].type_ == 'literal'
        assert ast.right.arguments[1].value == 'Jane'

        ast = self.parser.parse('name in ()')
        assert ast.type_ == 'operator'
        assert ast.value == 'in'
        assert ast.left is not None
        assert ast.left.type_ == 'identifier'
        assert ast.left.value == 'name'
        assert ast.right is not None
        assert ast.right.type_ == 'list'
        assert ast.right.arguments == []

    def test_parse_null_identifier(self):
        ast = self.parser.parse('null')
        assert ast.type_ == 'identifier'
        assert ast.value is None

        parser = ODataFilterParser(parse_null_identifier=False)
        ast = parser.parse('null')
        assert ast.type_ == 'identifier'
        assert ast.value == 'null'

    def test_parse_function(self):
        ast = self.parser.parse("startswith(name, 'J')")
        assert ast.type_ == 'function'
        assert ast.value == 'startswith'
        assert ast.arguments is not None
        assert ast.arguments[0].type_ == 'identifier'
        assert ast.arguments[0].value == 'name'
        assert ast.arguments[1].type_ == 'literal'
        assert ast.arguments[1].value == 'J'

    def test_parse_not(self):
        ast = self.parser.parse("not name eq 'John'")
        assert ast.type_ == 'operator'
        assert ast.value == 'not'
        assert ast.right is not None
        assert ast.right.type_ == 'operator'
        assert ast.right.value == 'eq'
        assert ast.right.left is not None
        assert ast.right.left.type_ == 'identifier'
        assert ast.right.left.value == 'name'
        assert ast.right.right is not None
        assert ast.right.right.type_ == 'literal'
        assert ast.right.right.value == 'John'

    def test_parse_error(self):
        # no primary expression
        with pytest.raises(ParseError):
            self.parser.parse('eq')

        # no opening parenthesis
        with pytest.raises(ParseError):
            self.parser.parse('startswith')

        # no closing parenthesis
        with pytest.raises(ParseError):
            self.parser.parse("name in ('John', 'Jane'")

        # no comma nor closing parenthesis
        with pytest.raises(ParseError):
            self.parser.parse("name in ('John'd")

        # unexpected end of expression
        with pytest.raises(ParseError):
            self.parser.parse('name in')

        # empty list but no closing parenthesis
        with pytest.raises(ParseError):
            self.parser.parse('name in (')

    def test_evaluate(self):
        ast = self.parser.parse("name eq 'John' and age gt 25")
        assert self.parser.evaluate(ast) == "name eq 'John' and age gt 25"

        ast = self.parser.parse('name eq null')
        assert self.parser.evaluate(ast) == "name eq null"

        ast = self.parser.parse("startswith(name, 'John')")
        assert self.parser.evaluate(ast) == "startswith(name, 'John')"

        ast = self.parser.parse("name in ('John', 'Jane')")
        assert self.parser.evaluate(ast) == "name in ('John', 'Jane')"

        ast = self.parser.parse("not name eq 'John'")
        assert self.parser.evaluate(ast) == "not name eq 'John'"

    def test_evaluate_error(self):
        # null node type
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_=None))  # type: ignore

        # unknown node type
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='unknown'))  # type: ignore

        # null literal
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='literal'))

        # null identifier
        assert self.parser.evaluate(FilterNode(type_='identifier')) == 'null'
        with pytest.raises(EvaluateError):
            parser = ODataFilterParser(parse_null_identifier=False)
            parser.evaluate(FilterNode(type_='identifier'))

        # null list
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='list'))

        # null operator
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='operator'))

        # null right operand for not operator
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='operator', value='not'))

        # null operand for operator
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='operator', value='eq'))

        # null function
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='function'))

        # null function arguments
        with pytest.raises(EvaluateError):
            self.parser.evaluate(FilterNode(type_='function', value='startswith'))
