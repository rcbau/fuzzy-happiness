
class CSVParser:
    """Parser for CSV files.

    Includes things such as:
      * Quotes strings containing all kinds of things
      * delimiters that are quoted

    """

    (Normal, InSingleQuote, InDoubleQuote) = range(3)

    def __init__(self, delimiter=','):
        """Create a new parser"""
        self._delimiter = delimiter

        self._fields = []
        self._current_field = ""
        self._state = self.Normal

        self.addField = self._fields.append

        self._lookup = [
            self._process_normal,
            self._process_in_single_quote,
            self._process_in_double_quote,
        ]

    def _process_normal(self, c):
        if c == self._delimiter:
            if self._current_field != "":
                # we've already been building up a field
                # so finish this one, and start afresh
                self.addField(self._current_field)
                self._current_field = ""
                return

        # Skip whitespace
        if c == " ":
            return

        # Handle quoting
        if c == "'":
            self._state = self.InSingleQuote
            # Fall through as we still want this character added
        if c == '"':
            self._state = self.InDoubleQuote
            # Fall through as we still want this character added

        # We're building a field
        self._current_field += c
        return

    def _process_in_double_quote(self, c):
        if c == '"':
            # Leaving the double quoted mode
            self._state = self.Normal
        self._current_field += c

    def _process_in_single_quote(self, c):
        if c == "'":
            # Leaving the single quoted mode
            self._state = self.Normal
        self._current_field += c

    def parse(self, str):
        """Parse str and return a list of string fields"""
        i = 0
        strlen = len(str)
        while i < strlen:
            c = str[i]
            self._lookup[self._state](c)
            i += 1
        # The last field case
        if self._current_field != "":
            self.addField(self._current_field)
        return self._fields
