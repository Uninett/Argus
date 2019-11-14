import re
from json import JSONDecodeError, JSONDecoder

from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

NOT_WHITESPACE = re.compile(r'[^\s]')


class StackedJSONParser(BaseParser):
    media_type = 'text/plain'

    decoder = JSONDecoder()

    def parse(self, stream, media_type=None, parser_context=None):
        # Code from https://stackoverflow.com/a/50384432/
        document = stream.read().decode(encoding="utf-8", errors="ignore")
        pos = 0
        while True:
            match = NOT_WHITESPACE.search(document, pos)
            if not match:
                return
            pos = match.start()

            try:
                obj, pos = self.decoder.raw_decode(document, pos)
            except JSONDecodeError:
                raise ParseError("Could not parse posted JSON objects.")
            yield obj
