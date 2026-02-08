import re
import sdl2
from sdl2.sdlgfx import roundedBoxRGBA, roundedRectangleRGBA

class Node:
    def __init__(self, selector=None, properties=None):
        self.selector = selector
        self.properties = properties if properties else []

    def __repr__(self):
        return f"Node(selector={self.selector}, properties={self.properties})"
    

class Provider:
    @staticmethod
    def draw(ast, widget, sdl_renderer):
        """
        Draw a widget using TinyXUI's CSS style provider
        
        :param ast: CSS AST to search through
        :param widget: Widget to draw
        :param sdl_renderer: SDL renderer object
        """
        for node in ast:
            if node.selector == widget.name:
                def get_styles_for_widget(widget_name):
                    styles = {prop["property"]: prop["value"] for prop in Provider.get_properties_for_selector(ast, widget_name)}

                    if widget.active:
                        active_styles = {prop["property"]: prop["value"] for prop in Provider.get_properties_for_selector(ast, f"{widget_name}:active")}
                        if active_styles:
                            styles.update(active_styles)               
                    
                    elif widget.hovered:
                        hover_styles = {prop["property"]: prop["value"] for prop in Provider.get_properties_for_selector(ast, f"{widget_name}:hover")}
                        if hover_styles:
                            styles.update(hover_styles)

                    return styles
                
                styles = get_styles_for_widget(widget.name)

                bg = styles.get("background", "#ffffff")
                border_color = styles.get("border-color", None)
                border_width = styles.get("border-width", 1)
                radius = styles.get("border-radius", 0)
                

                bgc = hex_to_argb(bg)
                if border_color:
                    bc = hex_to_argb(border_color)
                else:
                    bc = bgc

                x, y = widget.x, widget.y
                w, h = widget.width, widget.height

                match widget.name:
                    case "separator":
                        pass
                    case _:
                        roundedBoxRGBA(
                            sdl_renderer,
                            x, y,
                            x + w, y + h,
                            radius,
                            bgc.r, bgc.g, bgc.b, 255
                        )

                roundedRectangleRGBA(
                    sdl_renderer,
                    x, y,
                    x + w + border_width, y + h + border_width,
                    radius,
                    bc.r, bc.g, bc.b, 255
                )

    @staticmethod
    def get_property(ast, selector_name, property_name):
        """
        Get a property from CSS AST
        
        :param ast: CSS AST to search through
        :param selector_name: Widget/class selector
        :param property_name: Property to get
        """
        for node in ast:
            if node.selector == selector_name:
                # Find the property in the node's properties list
                for prop in node.properties:
                    if prop['property'] == property_name:
                        return prop['value']
        return None
    
    def get_properties_for_selector(ast, selector_name):
        """
        Get's all properties from a selector
        
        :param ast: CSS AST to search through
        :param selector_name: Widget/class selector
        """
        for node in ast:
            if node.selector == selector_name:
                return node.properties
        return []


def hex_to_argb(hex_code, alpha=255):
    """
    Converts hex codes to SDL ARGB (r, g, b, alpha)
    
    :param hex_code: Hex code for color, Ex: #FFF or #432fca
    :param alpha: Transparancy level, 255 is opaque, 0 is invisible
    """
    if type(hex_code) is not str:
        return sdl2.SDL_Color(0, 0, 0, 0)
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return sdl2.SDL_Color(r, g, b, alpha)

def generate_ast(stylesheet):
    with open(stylesheet, "r") as f:
        css = f.read()

    # Strip extra spaces and split by curly braces (to handle each rule block)
    rule_blocks = re.findall(r'([^{]+)\s*{([^}]+)}', css)
    
    ast = []

    for selector, properties_str in rule_blocks:
        selector = selector.strip()

        # Split the properties and values
        properties = []
        for prop in properties_str.split(';'):
            if prop.strip():
                property_match = re.match(r'([a-zA-Z\-]+)\s*:\s*(.+)', prop.strip())
                if property_match:
                    property_name = property_match.group(1).strip()
                    property_value = property_match.group(2).strip()
                    if property_value.endswith("px"):
                        property_value = int(property_value.removesuffix("px"))
                    properties.append({'property': property_name, 'value': property_value})
        
        # Create a Node for each rule and add to the AST
        ast.append(Node(selector, properties))

    return ast