from odata_v4_query import ODataQueryParser

parser = ODataQueryParser()

print(parser.parse_url('https://example.com/odata?$count=true&$top=10&$skip=20'))
