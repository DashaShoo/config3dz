import argparse
import re
import xml.etree.ElementTree as ET


class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse(self, line):
        # Удаление однострочных комментариев
        line = re.sub(r'\|\|.*', '', line)
        return line.strip()

    def parse_multiline_comments(self, lines):
        in_comment = False
        cleaned_lines = []

        for line in lines:
            if '{-' in line:
                in_comment = True
                line = line.split('{-', 1)[0]
            if '-}' in line:
                in_comment = False
                line = line.split('-}', 1)[1]
            if not in_comment and line.strip():
                cleaned_lines.append(line.strip())

        return cleaned_lines

    def evaluate(self, expression):
        # Обработка чисел и строк
        if expression.isdigit():
            return int(expression)
        if expression.startswith("'") and expression.endswith("'"):
            return expression[1:-1]

        # Обработка массивов
        array_match = re.match(r'list\((.*)\)', expression)
        if array_match:
            values = [self.evaluate(v.strip()) for v in array_match.group(1).split(',')]
            return values

        # Поддержка выражений с несколькими операциями
        expr_with_operations = re.split(r'(\s*[\+\-\*\/\%]\s*)', expression)

        # Вычисление выражения с поддержкой операций +, -, mod()
        result = None
        current_op = None

        for part in expr_with_operations:
            part = part.strip()
            if not part:
                continue

            if part.isdigit():  # Число
                value = int(part)
            elif part.startswith('?'):  # Константа
                const_name = part[1:]
                value = self.constants.get(const_name, None)
                if value is None:
                    raise SyntaxError(f"Константа '{const_name}' не определена.")
            elif part.startswith('mod(') and part.endswith(')'):  # Функция mod()
                inner_expr = part[4:-1].strip()
                mod_parts = inner_expr.split(',')
                if len(mod_parts) != 2:
                    raise SyntaxError("Неверный формат функции mod().")
                left_value = self.evaluate(mod_parts[0].strip())
                right_value = self.evaluate(mod_parts[1].strip())
                value = left_value % right_value
            else:  # Операция (+, -, *, /)
                current_op = part.strip()
                continue

            # Выполнение операции с предыдущим значением
            if result is None:
                result = value
            else:
                if current_op == '+':
                    result += value
                elif current_op == '-':
                    result -= value

        return result


class XMLGenerator:
    def __init__(self):
        self.root = ET.Element("config")

    def add_entry(self, name, value):
        entry = ET.SubElement(self.root, "entry")
        entry.set("name", name)

        if isinstance(value, list):
            value_elem = ET.SubElement(entry, "value")
            value_elem.text = ', '.join(map(str, value))
        else:
            entry.text = str(value)

    def write(self, filename):
        tree = ET.ElementTree(self.root)
        tree.write(filename)


def main():
    parser = argparse.ArgumentParser(description="Конвертер конфигурационного языка в XML.")
    parser.add_argument('--input', required=True, help='Путь к входному файлу')
    parser.add_argument('--output', required=True, help='Путь к выходному файлу')

    args = parser.parse_args()

    config_parser = ConfigParser()
    xml_generator = XMLGenerator()

    try:
        with open(args.input, 'r') as infile:
            lines = infile.readlines()
            cleaned_lines = config_parser.parse_multiline_comments(lines)

            for line in cleaned_lines:
                result = config_parser.parse(line)
                print(f"Обрабатываем строку: {result}")  # Отладочное сообщение
                if result:
                    # Обработка объявления константы
                    match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*<- (.+)', result)
                    if match:
                        name, value = match.groups()
                        print(f"Объявление константы: {name} <- {value}")  # Отладочное сообщение
                        config_parser.constants[name] = config_parser.evaluate(value)

                        # Добавляем константу в XML сразу после её определения
                        xml_generator.add_entry(name, config_parser.constants[name])
                        continue

                    # Обработка других выражений
                    try:
                        result_value = config_parser.evaluate(result)
                        print(f"Добавляем в XML: {result.strip()} -> {result_value}")  # Отладочное сообщение
                        xml_generator.add_entry(result.strip(), result_value)
                    except SyntaxError as e:
                        print(f"Ошибка при обработке строки '{result}': {e}")

        # Запись только если есть данные в XML
        if len(xml_generator.root) > 0:
            xml_generator.write(args.output)
            print(f"Данные успешно записаны в {args.output}.")
        else:
            print("Нет данных для записи в выходной файл.")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()