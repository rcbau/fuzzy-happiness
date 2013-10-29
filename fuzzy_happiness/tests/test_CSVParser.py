
import testtools

from fuzzy_happiness import CSVParser


class TestParse(testtools.TestCase):

    # Note(mrda): Need to test null
    # Note(mrda): Need to test json

    def test_simple(self):
        input = "a,b,c,d"
        output = ['a', 'b', 'c', 'd']
        csv = CSVParser.CSVParser()
        self.assertEqual(csv.parse(input), output)
        self.assertEqual(','.join(output), input)

    def test_real_simple(self):
        input = ("'2013-05-13 04:35:08', '2013-05-13 06:54:09', 1, 16162, "
                 "218, 960, 0, 'QEMU'")
        output = ["'2013-05-13 04:35:08'", "'2013-05-13 06:54:09'", '1',
                  '16162', '218', '960', '0', "'QEMU'"]
        csv = CSVParser.CSVParser()
        self.assertEqual(csv.parse(input), output)
        self.assertEqual(', '.join(output), input)

    def test_commas_in_quotes(self):
        input = "'foo, bar', 'baz'"
        output = ["'foo, bar'", "'baz'"]
        csv = CSVParser.CSVParser()
        self.assertEqual(csv.parse(input), output)
        self.assertEqual(', '.join(output), input)

    def test_commas_in_double_quotes(self):
        input = '"foo, bar", "baz"'
        output = ['"foo, bar"', '"baz"']
        csv = CSVParser.CSVParser()
        self.assertEqual(csv.parse(input), output)
        self.assertEqual(', '.join(output), input)

    def test_simple_json(self):
        input = ("'fred', '{\"vendor\": \"Intel\", \"features\": "
                 "[\"lahf_lm\", \"lm\", \"rdtscp\", ] }', 'wilma'")
        output = ["'fred'", "'{\"vendor\": \"Intel\", \"features\": "
                  "[\"lahf_lm\", \"lm\", \"rdtscp\", ] }'", "'wilma'"]
        csv = CSVParser.CSVParser()
        self.assertEqual(csv.parse(input), output)
        self.assertEqual(', '.join(output), input)
