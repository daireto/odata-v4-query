from odata_v4_query import ODataQueryParser, ODataFilterParser

# Create parser instance
parser = ODataQueryParser()

# Parse a complete URL
options = parser.parse_url('https://example.com/odata?$count=true&$top=10&$skip=20')
print('Parsing URL:', options, end='\n\n')

# Parse just the query string
options = parser.parse_query_string("$filter=name eq 'John' and age gt 25")
print('Parsing query string:', options, end='\n\n')

# Parse filter expressions
filter_parser = ODataFilterParser()
ast = filter_parser.parse("name eq 'John' and age gt 25")
print('Parsing filter expression:', ast, end='\n\n')

# Evaluate filter expressions
expr = filter_parser.evaluate(ast)
print('Evaluating filter expression:', expr, end='\n\n')
