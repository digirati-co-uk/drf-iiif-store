from search_service.parsers import (
    SearchParser,
)


class IIIFResourceSearchParser(SearchParser):
    q_prefix = "indexables__"
