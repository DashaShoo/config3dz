import unittest
from io import StringIO
import sys
import xml.etree.ElementTree as ET

# Импортируем классы из основного модуля
from main import ConfigParser, XMLGenerator


class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()
        self.xml_generator = XMLGenerator()

    def test_constant_declaration(self):
        self.parser.constants['server'] = self.parser.evaluate("'192.168.1.1'")
        self.assertEqual(self.parser.constants['server'], '192.168.1.1')

    def test_array_declaration(self):
        result = self.parser.evaluate("list(8080, 8081, 8082)")
        self.assertEqual(result, [8080, 8081, 8082])

    def test_addition(self):
        self.parser.constants['db_port'] = 5432
        result = self.parser.evaluate("?db_port + 10")
        self.assertEqual(result, 5442)

    def test_subtraction(self):
        self.parser.constants['db_port'] = 5432
        result = self.parser.evaluate("?db_port - 10")
        self.assertEqual(result, 5422)

    def test_mod_function(self):
        self.parser.constants['db_port'] = 5432
        result = self.parser.evaluate("mod(?db_port, 100)")
        self.assertEqual(result, 32)

    def test_nested_expressions(self):
        # Вложенные выражения: (?db_port + 10) - (5 * 2)
        self.parser.constants['db_port'] = 5432
        result = self.parser.evaluate("(?db_port + 10) - (5 * 2)")
        self.assertEqual(result, (5432 + 10) - (5 * 2))


    def test_xml_generation(self):
        self.parser.constants['app_name'] = 'MyApp'
        self.xml_generator.add_entry('app_name', self.parser.constants['app_name'])

        # Проверяем, что XML содержит правильные данные
        expected_xml = '<config><entry name="app_name">MyApp</entry></config>'
        output_xml = ET.tostring(self.xml_generator.root).decode()

        self.assertEqual(output_xml, expected_xml)


if __name__ == '__main__':
    unittest.main()