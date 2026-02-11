import sdl2
from . import style_provider
from importlib.resources import files

def normalize_layout_attrs(widget):
    """
    Converts attribute aliases to direct attributes
    
    :param widget: Widget object
    """
    align = widget.attributes.get("align", "start").lower()

    # Default to start
    widget.halign = "start"
    widget.valign = "start"

    # Parse align attribute
    if align in ("start", "left"):
        widget.halign = "start"
    elif align in ("center", "hcenter"):
        widget.halign = "center"
    elif align in ("end", "right"):
        widget.halign = "end"

    if align in ("start", "top"):
        widget.valign = "start"
    elif align in ("center", "vcenter"):
        widget.valign = "center"
    elif align in ("end", "bottom"):
        widget.valign = "end"

    # expand flags
    widget.hexpand = widget.attributes.get("hexpand", False)
    widget.vexpand = widget.attributes.get("vexpand", False)

    # "expand" shortcut for both directions
    if widget.attributes.get("expand", False):
        widget.hexpand = True
        widget.vexpand = True


def measure(widget, font, settings):
    """
    Measures and returns minimum width and height for a widget, including padding.
    
    :param widget: Widget object
    :param font: SDL font object
    :param settings: Document settings
    """
    # Load padding from stylesheet
    stylesheet = files('tinyxui.data').joinpath(settings["stylesheet"])
    ast = style_provider.generate_ast(stylesheet)
    padding = style_provider.Provider.get_property(ast, widget.name, "padding") or 0
    pad_left = pad_right = pad_top = pad_bottom = int(padding)

    # If padding is a tuple/list, unpack
    if isinstance(padding, (tuple, list)):
        if len(padding) == 2:
            pad_top, pad_bottom = pad_left, pad_right = padding
        elif len(padding) == 4:
            pad_top, pad_right, pad_bottom, pad_left = padding

    # Function to add padding
    def add_padding(w, h):
        return w + pad_left + pad_right, h + pad_top + pad_bottom

    # Children override everything
    if widget.children:
        direction = widget.attributes.get("direction", "vertical")
        total_w, total_h = 0, 0

        for child in widget.children:
            cw, ch = measure(child, font, settings=settings)

            if direction == "horizontal":
                total_w += cw
                total_h = max(total_h, ch)
            else:
                total_h += ch
                total_w = max(total_w, cw)

        return add_padding(total_w, total_h)

    # Leaf widgets: use match-case
    match widget.name:
        case "label":
            sdl_color = sdl2.SDL_Color(0, 0, 0, 255)
            surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(
                font, str(widget.data).encode("utf-8"), sdl_color
            )
            if not surface:
                return add_padding(0, 0)
            w, h = surface.contents.w, surface.contents.h
            sdl2.SDL_FreeSurface(surface)
            return add_padding(w, h)

        case "button":
            w = int(widget.attributes.get("width", 72))
            h = int(widget.attributes.get("height", 32))
            return add_padding(w, h)

        case "icon":
            size = int(widget.attributes.get("size", 16))
            return add_padding(size, size)

        case "image":
            try:
                size = int(widget.attributes["size"])
                return add_padding(size, size)
            except KeyError:
                w = int(widget.attributes.get("width", 16))
                h = int(widget.attributes.get("height", 16))
                return add_padding(w, h)

        case "separator":
            direction = widget.attributes.get("direction", "horizontal")
            if direction == "vertical":
                w = 1
                h = int(widget.attributes.get("height", 128))
            else:
                w = int(widget.attributes.get("width", 128))
                h = 1
            return add_padding(w, h)

        case "spacer":
            w = int(widget.attributes.get("width", 0))
            h = int(widget.attributes.get("height", 0))
            return add_padding(w, h)

        case "progressbar":
            w = int(widget.attributes.get("width", 128))
            return (w, 0)

        case "progressfill":
            total_width = int(widget.attributes.get("width", getattr(widget.parent, "width", 128)))
            progress = getattr(widget, "progress", 0)
            w = int(total_width * (progress / 100))
            h = int(widget.attributes.get("height", 8))
            return (w, h)


        case _:  # default fallback
            return (0, 0)


def compute_layout(widget, x=0, y=0, width=None, height=None,
                   settings=None, font=None):
    """
    Creates layout from generated AST
    
    :param widget: Widget object
    :param x: Widget X position
    :param y: Widget Y position
    :param width: Widget width
    :param height: Widget height
    :param settings: Document settings from AST
    :param font: SDL font object
    """
    normalize_layout_attrs(widget)

    if width is None:
        width = settings["width"]
    if height is None:
        height = settings["height"]

    if widget.name == "root":
        widget.x, widget.y = x, y
        widget.width, widget.height = width, height
    else:
        mw, mh = measure(widget, font, settings=settings)
        widget.x, widget.y = x, y
        widget.width = max(width, mw)
        widget.height = max(height, mh)
        if widget.hexpand:
            width = max(width, mw)
        if widget.vexpand:
            height = max(height, mh)

    if width is None or height is None:
        mw, mh = measure(widget, font, settings=settings)
        widget.width = mw if width is None else width
        widget.height = mh if height is None else height

    if not widget.children:
        return

    # Normalize all children
    for child in widget.children:
        normalize_layout_attrs(child)
        
    direction = widget.attributes.get("direction", "vertical")

    # Horizontal
    if direction == "horizontal":
        total_base = 0
        expanders = []
        sizes = []

        for child in widget.children:
            cw, ch = measure(child, font, settings=settings)
            sizes.append([cw, ch])
            total_base += cw

            if child.hexpand:
                expanders.append(child)

        remaining = max(0, widget.width - total_base)
        extra = remaining // len(expanders) if expanders else 0

        cx = widget.x

        for i, child in enumerate(widget.children):
            cw, ch = sizes[i]

            if child.hexpand:
                cw += extra

            if child.vexpand:
                ch = widget.height

            # vertical alignment
            if child.valign == "center":
                cy = widget.y + (widget.height - ch) // 2
            elif child.valign == "end":
                cy = widget.y + widget.height - ch
            else:
                cy = widget.y

            compute_layout(child, cx, cy, cw, ch, settings=settings,font=font)
            cx += cw

    # Vertical
    else:
        total_base = 0
        expanders = []
        sizes = []

        for child in widget.children:
            cw, ch = measure(child, font, settings=settings)
            sizes.append([cw, ch])
            total_base += ch

            if child.vexpand:
                expanders.append(child)

        remaining = max(0, widget.height - total_base)
        extra = remaining // len(expanders) if expanders else 0

        total_height = sum(
            ch + (extra if widget.children[i].vexpand else 0)
            for i, (_, ch) in enumerate(sizes)
        )

        # container vertical alignment
        if widget.valign == "center" and widget.name != "root":
            cy = widget.y + (widget.height - total_height) // 2
        elif widget.valign == "end" and widget.name != "root":
            cy = widget.y + widget.height - total_height
        else:
            cy = widget.y

        for i, child in enumerate(widget.children):
            cw, ch = sizes[i]

            if child.vexpand:
                ch += extra

            # cross-axis expand
            if child.hexpand:
                cw = widget.width

            # horizontal alignment
            if child.halign == "center":
                cx = widget.x + (widget.width - cw) // 2
            elif child.halign == "end":
                cx = widget.x + widget.width - cw
            else:
                cx = widget.x

            if child.valign == "center":
                cy = widget.y + (widget.height - ch) // 2
            elif child.valign == "end":
                cy = widget.y + widget.height - ch
            else:
                pass

            compute_layout(child, cx, cy, cw, ch, settings=settings, font=font)
            cy += ch
            

if __name__ == "__main__":
    """Errors if you try to run TinyXUI on its own"""
    print("Do not run TinyXUI's layout engine on its own!")
    print("Import it into another codebase to use it.")