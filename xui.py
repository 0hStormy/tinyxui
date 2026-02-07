"""
TinyXUI. A open source, fast, and light GUI toolkit for Python.
by 0Stormy
"""


import xml.etree.ElementTree as ET
import sdl2
import sdl2.ext
import sdl2.sdlttf as sdlttf
import PIL


WIDTH = 640
HEIGHT = 480
STYLE = {
    "bg": "#eff0f1",
    "accent": "#3daee9",
    "button": "#fcfcfc",
    "separator": "#d1d2d3",
    "text": "#232629",
    "highlight": "#badcee",
    "padding": 4,
    "margin": 4
}

callbacks = {}
_widget_registry = {}

def bind_button(id, func):
    """Bind a function to a button with a given ID"""
    callbacks[id] = func


class parser:
    @staticmethod
    def parse(file):
        """Parses TinyXUI XML"""
        with open(file, "r") as f:
            xml_data = f.read()
        root = ET.fromstring(xml_data)
        return root

class Widget:
    def __init__(self, type, label, y, height=0, id=None, callback=None, src=None):
        self.type = type
        self.label = label
        self.y = y
        self.height = height
        self.id = id
        self.src = src
        self.callback = callback

    def contains(self, x, y):
        """Checks if mouse is in widget"""
        return STYLE["margin"] <= x < (WIDTH - STYLE["margin"]) and self.y <= y < self.y + self.height

    def set_position(self, y):
        """Sets widget screen position"""
        self.y = y
    
    def set_attribute(self, attr, value):
        """Set an attribute if it exists"""
        if hasattr(self, attr):
            setattr(self, attr, value)
        else:
            raise AttributeError(f"Widget has no attribute '{attr}'")

    def set_label(self, value):
        """Set arbitrary label for this widget"""
        self.label = value
    

def build_widgets(dom):
    """Builds all widgets in XML file"""
    widgets = []
    for element in dom:
        wid = element.attrib.get("id")
        wsrc = element.attrib.get("src")
        match element.tag:
            case "button":
                w = Widget("button", element.attrib.get("label",""), 0, 32, id=wid)
            case "label":
                w = Widget("label", element.text or "", 0, 24, id=wid)
            case "separator":
                w = Widget("separator", "", 0, 1, id=wid)
            case "image":
                w = Widget("image", "", 0, 128, id=wid, src=wsrc)
            case _:
                continue
        widgets.append(w)
        if wid:
            _widget_registry[wid] = w
    return widgets


def layout_widgets(widgets):
    """Creates widgets layout"""
    y = 0
    for w in widgets:
        w.set_position(y)
        y += w.height + STYLE["margin"]

def widget_from_id(widget_id):
    """Return the live widget from the currently running UI"""
    w = _widget_registry.get(widget_id)
    if not w:
        raise ValueError(f"No widget with id '{widget_id}' found")
    return w

class renderer:
    class draw:
        @staticmethod
        def background(sdl_renderer):
            """Draws background"""
            color = renderer.hex_to_argb(STYLE["bg"])
            sdl2.SDL_SetRenderDrawColor(
                sdl_renderer, color.r, color.g, color.b, 255
            )
            sdl2.SDL_RenderClear(sdl_renderer)

        @staticmethod
        def button(sdl_renderer, font, y, label="", selected=False, mouse_down=False):
            """Draws a clickable button"""
            h = 32

            if selected:
                bg = STYLE["accent"] if mouse_down else STYLE["highlight"]
                border = STYLE["accent"]
            else:
                bg = STYLE["button"]
                border = STYLE["separator"]

            bgc = renderer.hex_to_argb(bg)
            bc = renderer.hex_to_argb(border)

            sdl2.SDL_SetRenderDrawColor(
                sdl_renderer, bgc.r, bgc.g, bgc.b, 255
            )
            sdl2.SDL_RenderFillRect(
                sdl_renderer, sdl2.SDL_Rect(STYLE["margin"], y, (WIDTH - (STYLE["margin"] * 2)), h)
            )

            sdl2.SDL_SetRenderDrawColor(
                sdl_renderer, bc.r, bc.g, bc.b, 255
            )
            sdl2.SDL_RenderDrawRect(
                sdl_renderer, sdl2.SDL_Rect(STYLE["margin"], y, (WIDTH - (STYLE["margin"] * 2)), h)
            )

            renderer.draw_text(
                sdl_renderer,
                font,
                label,
                (STYLE["margin"] + STYLE["padding"]),
                y + 7,
                renderer.hex_to_argb(STYLE["text"]),
            )
            return h

        @staticmethod
        def label(sdl_renderer, font, y, label=""):
            """Draws a text label"""
            renderer.draw_text(
                sdl_renderer,
                font,
                label,
                STYLE["padding"],
                y + 4,
                renderer.hex_to_argb(STYLE["text"]),
            )
            return 24

        @staticmethod
        def separator(sdl_renderer, y):
            """Draws a separator line"""
            c = renderer.hex_to_argb(STYLE["separator"])
            sdl2.SDL_SetRenderDrawColor(
                sdl_renderer, c.r, c.g, c.b, 255
            )
            sdl2.SDL_RenderDrawLine(
                sdl_renderer, 0, y, WIDTH, y
            )
            return 1
        
        @staticmethod
        def image(sdl_renderer, y, src):
            if src is None:
                file_path = "missing.png"
            else:
                file_path = src
            try:
                surface = sdl2.ext.load_image(file_path)
            except PIL.UnidentifiedImageError:
                print(f"Failed to load image: {file_path}")
                return
            except FileNotFoundError:
                file_path = "missing.png"
                surface = sdl2.ext.load_image(file_path)

            texture = sdl2.SDL_CreateTextureFromSurface(sdl_renderer, surface)

            sdl2.SDL_FreeSurface(surface)
            
            rect = sdl2.SDL_Rect(STYLE["margin"], y, 128, 128)
            sdl2.SDL_RenderCopy(sdl_renderer, texture, None, rect)

            sdl2.SDL_DestroyTexture(texture)


    @staticmethod
    def draw_widgets(sdl_renderer, font, widgets, selected_index, mouse_down):
        """Draws each widget in order"""
        for i, w in enumerate(widgets):
            selected = i == selected_index
            match w.type:
                case "folder":
                    renderer.draw.folder(sdl_renderer, font, w.y, w.label, selected)
                case "button":
                    renderer.draw.button(
                        sdl_renderer, font, w.y, w.label, selected, mouse_down
                    )
                case "label":
                    renderer.draw.label(sdl_renderer, font, w.y, w.label)
                case "separator":
                    renderer.draw.separator(sdl_renderer, w.y)
                case "image":
                    renderer.draw.image(sdl_renderer, w.y, w.src)


    def draw_text(renderer, font, text, x, y, color):
        """Draws bare text, should be used with a widget"""
        surface = sdlttf.TTF_RenderUTF8_Blended(font, text.encode("utf-8"), color)
        texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)

        rect = sdl2.SDL_Rect(x, y, surface.contents.w, surface.contents.h)
        sdl2.SDL_RenderCopy(renderer, texture, None, rect)

        sdl2.SDL_FreeSurface(surface)
        sdl2.SDL_DestroyTexture(texture)


    def hex_to_argb(hex_code, alpha=255):
        """Converts hex codes to SDL ARGB (r, g, b, alpha)"""
        hex_code = hex_code.lstrip("#")
        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return sdl2.SDL_Color(r, g, b, alpha)


def start(xml_file="demo.xml"):
    """Main UI Function"""
    sdl2.ext.init()
    sdlttf.TTF_Init()
    font = sdlttf.TTF_OpenFont(b"NotoSans.ttf", 12)
    redraw = True
    last_tick = sdl2.SDL_GetTicks()
    interval = 100

    dom = parser.parse(xml_file)

    sdl2.SDL_SetHint(
        sdl2.SDL_HINT_RENDER_SCALE_QUALITY,
        b"1"
    )

    window = sdl2.ext.Window(
        dom.attrib["title"],
        size=(WIDTH, HEIGHT),
        flags=sdl2.SDL_WINDOW_SHOWN,
    )

    sdl_renderer = sdl2.SDL_CreateRenderer(
        window.window,
        -1,
        sdl2.SDL_RENDERER_ACCELERATED,
    )

    event = sdl2.SDL_Event()
    running = True

    widgets = build_widgets(dom)
    layout_widgets(widgets)
    for w in widgets:
        if w.id in callbacks:
            w.callback = callbacks[w.id]
            
    selected_index = 0
    mouse_down = False

    while running:
        while sdl2.SDL_PollEvent(event):
            mouse_x = event.motion.x
            mouse_y = event.motion.y

            old_selected = selected_index
            selected_index = None

            for i, widget in enumerate(widgets):
                if widget.contains(mouse_x, mouse_y):
                    selected_index = i
                    break


            if selected_index != old_selected:
                redraw = True

            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mouse_down = True
                redraw = True
            elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                mouse_down = False
                redraw = True
                for w in widgets:
                    if w.type == "button" and w.contains(event.button.x, event.button.y):
                        if w.callback:
                            w.callback()
                            redraw = True

        current_tick = sdl2.SDL_GetTicks()
        if current_tick - last_tick >= interval:
            redraw = True
            last_tick = current_tick

        if redraw:
            renderer.draw.background(sdl_renderer)
            renderer.draw_widgets(sdl_renderer, font, widgets, selected_index, mouse_down)
            sdl2.SDL_RenderPresent(sdl_renderer)

            redraw = False

        
    sdl2.ext.quit()

if __name__ == "__main__":
    """Errors if you try to run TinyXUI on its own"""
    print("Do not run TinyXUI on its own!")
    print("Import it into another codebase to use it.")