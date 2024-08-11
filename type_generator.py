import re
from typing import List

thrift_file = "idl/soccer_service.thrift"  # Replace with your actual Thrift file name
output_file = "soccer/ttypes.pyi"

# Regex patterns to match Thrift definitions
enum_pattern = re.compile(r"enum\s+(\w+)\s*{?")
struct_pattern = re.compile(r"struct\s+(\w+)\s*{?")
field_pattern = re.compile(r"\s*(\d+):\s*(\w+)\s+(\w+)[,;]?")
enum_field_pattern = re.compile(r"\s*(\w+)\s*=\s*(\d+),?")
list_pattern = re.compile(r"\s*(\d+):\s*list<(\w+)>\s*(\w+)[,;]?")
# 11: map<i32, Player> our_players_dict,
map_pattern = re.compile(r"\s*(\d+):\s*map<(\w+),\s*(\w+)>\s*(\w+)[,;]?")

# Typing map from Thrift types to Python types
type_map = {
    "i32": "int",
    "i64": "int",
    "double": "float",
    "bool": "bool",
    "string": "str",
    "list": "List",
    "map": "Dict",
}


def add_types(lines: List[str]) -> None:
    global type_map

    for line in lines:
        # Match enums
        enum_match = enum_pattern.match(line)
        if enum_match:
            enum_name = enum_match.group(1)
            type_map[enum_name] = enum_name
            continue

        # Match structs
        struct_match = struct_pattern.match(line)
        if struct_match:
            struct_name = struct_match.group(1)
            type_map[struct_name] = struct_name
            continue

class Field:
    def __init__(self, name: str, type: str, is_enum: bool = False):
        self.name = name
        self.type = type
        self.is_enum = is_enum

    def __str__(self):
        if self.is_enum:
            return f"    {self.name} = auto()"
        return f"    {self.name}: {self.type}"

class Class:
    def __init__(self, name: str, is_enum: bool = False):
        self.name = name
        self.is_enum = is_enum
        self.fields = []

    def add_field(self, field: Field):
        self.fields.append(field)

    def __str__(self):
        return f"class {self.name}:\n" + "\n".join(self.fields)

def parse_thrift_file(old_lines: list[str]) -> List[str]:
    """Parse the Thrift file and return lines for .pyi file"""
    lines = []

    current_struct = None
    current_struct_has_fields = False
    current_enum = None
    classes = []

    for line in old_lines:
        # Match enums
        enum_match = enum_pattern.match(line)
        struct_match = struct_pattern.match(line)
        field_match = field_pattern.match(line)
        enum_field_match = enum_field_pattern.match(line)
        list_match = list_pattern.match(line)
        map_match = map_pattern.match(line)

        if enum_match:
            enum_name = enum_match.group(1)
            classes.append(Class(enum_name, is_enum=True))
            continue

        if struct_match:
            struct_name = struct_match.group(1)
            classes.append(Class(struct_name, is_enum=False))
            continue

        if field_match:
            field_type = field_match.group(2)
            field_name = field_match.group(3)
            python_type = type_map.get(field_type, field_type)
            classes[-1].add_field(Field(field_name, python_type))
            continue

        if enum_field_match:
            field_name = enum_field_match.group(1)
            classes[-1].add_field(Field(field_name, "", is_enum=True))
            continue

        if list_match:
            field_name = list_match.group(3)
            list_type = list_match.group(2)
            classes[-1].add_field(Field(field_name, f"List[{list_type}]"))
            continue

        if map_match:
            field_name = map_match.group(4)
            key_type = map_match.group(2)
            key_type = type_map.get(key_type, key_type)
            value_type = map_match.group(3)
            classes[-1].add_field(Field(field_name, f"Dict[{key_type}, {value_type}]"))
            continue

    for class_ in classes:
        lines.append("")
        if class_.is_enum:
            lines.append(f"class {class_.name}(Enum):")
        else:
            lines.append(f"class {class_.name}(object):")
            init_input_str = ", ".join([f"{field.name}: {field.type} = None" for field in class_.fields])
            lines.append(f"    def __init__(self, {init_input_str}):")
            lines.append("        pass")

        if len(class_.fields) == 0:
            lines.append("    pass")
        else:
            for field in class_.fields:
                lines.append(str(field))

    return lines


def write_pyi_file(output_file: str, lines: List[str]) -> None:
    """Write the generated lines to the output .pyi file"""
    with open(output_file, "w") as file:
        file.write("import sys\n")
        file.write("from typing import List, Dict, Tuple, Union, Any, Optional\n")
        file.write("from enum import Enum, auto\n")
        for line in lines:
            file.write(line + "\n")


def main():
    file_path = thrift_file
    with open(file_path, "r") as file:
        content = file.read()
    lines = []
    # remove optional form all lines
    for line in content.splitlines():
        new_line = line.replace("optional", "")
        lines.append(new_line)

    add_types(lines)
    print("Types added to type map")
    print(type_map)
    lines = parse_thrift_file(lines)
    write_pyi_file(output_file, lines)
    print(f"Type annotations written to {output_file}")


if __name__ == "__main__":
    main()
