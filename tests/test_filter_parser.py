import pytest

from odata_v4_query.errors import (
    CommaOrClosingParenthesisExpectedError,
    MissingClosingParenthesisError,
    OpeningParenthesisExpectedError,
    UnexpectedEndOfExpressionError,
    UnexpectedNullFunctionNameError,
    UnexpectedNullIdentifierError,
    UnexpectedNullListError,
    UnexpectedNullLiteralError,
    UnexpectedNullNodeTypeError,
    UnexpectedNullOperandError,
    UnexpectedNullOperatorError,
    UnexpectedTokenError,
    UnknownNodeTypeError,
)
from odata_v4_query.filter_parser import FilterNode, ODataFilterParser


class TestFilterParser:
    parser = ODataFilterParser()

    def test_parse_ast(self):
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

    def test_parse_empty_ast(self):
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

    def test_parse_in_empty_list(self):
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

    def test_parse_null_identifier_disabled(self):
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

    def test_no_primary_expression(self):
        with pytest.raises(UnexpectedTokenError):
            self.parser.parse('eq')

    def test_no_opening_parenthesis(self):
        with pytest.raises(OpeningParenthesisExpectedError):
            self.parser.parse('startswith')

    def test_missing_comma_or_closing_parenthesis(self):
        with pytest.raises(CommaOrClosingParenthesisExpectedError):
            self.parser.parse("name in ('John', 'Jane'")

        with pytest.raises(CommaOrClosingParenthesisExpectedError):
            self.parser.parse("name in ('John'd")

    def test_unexpected_end_of_expression(self):
        with pytest.raises(UnexpectedEndOfExpressionError):
            self.parser.parse('name in')

    def test_missing_closing_parenthesis(self):
        with pytest.raises(MissingClosingParenthesisError):
            self.parser.parse('name in (')

    def test_evaluate(self):
        ast1 = self.parser.parse("name eq 'John' and age gt 25")
        ast2 = self.parser.parse('name eq null')
        ast3 = self.parser.parse("startswith(name, 'John')")
        ast4 = self.parser.parse("name in ('John', 'Jane')")
        ast5 = self.parser.parse("not name eq 'John'")
        assert self.parser.evaluate(ast1) == "name eq 'John' and age gt 25"
        assert self.parser.evaluate(ast2) == 'name eq null'
        assert self.parser.evaluate(ast3) == "startswith(name, 'John')"
        assert self.parser.evaluate(ast4) == "name in ('John', 'Jane')"
        assert self.parser.evaluate(ast5) == "not name eq 'John'"

    def test_unexpected_null_node_type(self):
        with pytest.raises(UnexpectedNullNodeTypeError):
            self.parser.evaluate(FilterNode(type_=None))  # type: ignore

    def test_unknown_node_type(self):
        with pytest.raises(UnknownNodeTypeError):
            self.parser.evaluate(FilterNode(type_='unknown'))  # type: ignore

    def test_unexpected_null_literal(self):
        with pytest.raises(UnexpectedNullLiteralError):
            self.parser.evaluate(FilterNode(type_='literal'))

    def test_unexpected_null_identifier(self):
        parser = ODataFilterParser(parse_null_identifier=False)
        assert self.parser.evaluate(FilterNode(type_='identifier')) == 'null'
        with pytest.raises(UnexpectedNullIdentifierError):
            parser.evaluate(FilterNode(type_='identifier'))

    def test_unexpected_null_list(self):
        with pytest.raises(UnexpectedNullListError):
            self.parser.evaluate(FilterNode(type_='list'))

    def test_unexpected_null_operator(self):
        with pytest.raises(UnexpectedNullOperatorError):
            self.parser.evaluate(FilterNode(type_='operator'))

    def test_unexpected_null_operand_for_not_operator(self):
        with pytest.raises(UnexpectedNullOperandError):
            self.parser.evaluate(FilterNode(type_='operator', value='not'))

    def test_unexpected_null_operand_for_operator(self):
        with pytest.raises(UnexpectedNullOperandError):
            self.parser.evaluate(FilterNode(type_='operator', value='eq'))

    def test_unexpected_null_function_name(self):
        with pytest.raises(UnexpectedNullFunctionNameError):
            self.parser.evaluate(FilterNode(type_='function'))

    def test_unexpected_empty_arguments(self):
        with pytest.raises(UnexpectedNullListError):
            self.parser.evaluate(FilterNode(type_='function', value='startswith'))
