import re


class Widget:
    """
    Widget class that all other widgets extend from
    """
    def __init__(self, name, attributes=None, children=None, data=None, x=0,
                y=0, width=0, height=0, hovered=False, active=False,
                margin=[0, 0, 0, 0]):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []
        self.data = data
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hovered = hovered
        self.active = active
        self.margin = margin

    def __repr__(self):
        return (
            f"Widget({self.name}, {self.attributes}, "
            f"children={len(self.children)}, data={self.data})"
        )


class AST:
    """
    Class for AST related tasks
    """
    @staticmethod
    def parse_value(value):
        """
        Parse TXM value to Python value
        
        :param value: Value to parse
        """

        # String
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        
        # Integer
        if value.isdigit():
            return int(value)
        
        # Boolean
        if value == "true":
            return True
        elif value == "false":
            return False

        # Unsupported type
        raise TypeError(f"{value} does not fit into a valid type!")
    
    
    @staticmethod
    def parse_attributes(attr_string):
        """
        Parses attributes from a TXM widget
        
        :param attr_string: String of attributes to parse
        """
        attributes = {}

        if not attr_string.strip():
            return attributes

        parts = attr_string.split(",")
        for part in parts:
            key, value = part.split("=", 1)
            attributes[key.strip()] = AST.parse_value(value.strip())

        return attributes
    
    @staticmethod
    def parse_setting(line):
        """
        Parse a setting from a TXM document
        
        :param line: Line of TXM code to parse
        """
        # Remove newline
        setting_line = line.rstrip("\n")[1:]

        # Strip spaces to create dictionary entry
        key, value = setting_line.split("=", 1)
        key = key.strip()
        value = AST.parse_value(value.strip())

        # Add to settings dictionary
        return key, value
    

    @staticmethod
    def parse_widget(line):
        """
        Parse widget and its attributes
        
        :param line: Line of TXM code to parse
        """
        widget_pattern = r'(\w+)\((.*?)\)\s*(\{.*\})?'
        match = re.match(widget_pattern, line)

        if not match:
            raise SyntaxError(f"Invalid widget syntax: {line}")

        name, attr_string, data_block = match.groups()

        attributes = AST.parse_attributes(attr_string)
        data = None

        if data_block:
            data = data_block.strip()[1:-1].strip()
            if data:
                data = AST.parse_value(data)

        return Widget(name, attributes, data=data)


    @staticmethod
    def generate_ast(document):
        """
        Generate an AST from a TXM document
        
        :param document: File path of TXM document
        """
        settings = {
            "window_title": "TinyXUI",
            "width": 320,
            "height": 240
        }
        root = Widget(
            "root", attributes={"direction": "vertical", "expand": True})
        stack = [root]

        with open(document, "r") as f:
            lines = f.readlines()

        for raw_line in lines:
            line = raw_line.strip()

            if not line or line.startswith("//"):
                continue

            # Settings
            if line.startswith("!"):
                key, value = AST.parse_setting(raw_line)
                settings[key] = value
                continue

            # End of widget block
            if line == "}":
                stack.pop()
                continue

            widget = AST.parse_widget(line)

            stack[-1].children.append(widget)

            if line.endswith("{"):
                stack.append(widget)

        return settings, root

            
AST.generate_ast("mpd.txm")