"""
TinyXUI. A open source, fast, and light GUI toolkit for Python.
by 0Stormy
"""

import skia
import xml.etree.ElementTree as ET
import sdl2
import sdl2.ext
import ctypes


WIDTH = 640
HEIGHT = 480
STYLE = {
    "bg": "#eff0f1",
    "accent": "#3daee9",
    "folder": "#ffffff",
    "button": "#fcfcfc",
    "separator": "#d1d2d3",
    "text": "#232629",
    "highlight": "#badcee",
    "padding": 8,
    "margin": 4
}


callbacks = {}

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
    def __init__(self, type, label, y, height=0, id=None, callback=None):
        """Widget properties"""
        self.type = type
        self.label = label
        self.y = y
        self.height = height
        self.id = id
        self.callback = callback
    
    def contains(self, x, y):
        """Checks in mouse is in widget"""
        return 0 <= x < WIDTH and self.y <= y < self.y + self.height

    def set_position(self, y):
        """Sets widget screen position"""
        self.y = y


def build_widgets(dom):
    """Builds all widgets in XML file"""
    widgets = []
    for element in dom:
        wid = element.attrib.get("id")
        match element.tag:
            case "folder":
                widgets.append(Widget("folder", element.attrib.get("label",""), 0, 32, id=wid))
            case "button":
                widgets.append(Widget("button", element.attrib.get("label",""), 0, 32, id=wid))
            case "label":
                widgets.append(Widget("label", element.text or "", 0, 24, id=wid))
            case "separator":
                widgets.append(Widget("separator", "", 0, 1, id=wid))
    return widgets


def layout_widgets(widgets):
    """Creates widgets layout"""
    y = 0
    for w in widgets:
        w.set_position(y)
        y += w.height + STYLE["margin"]


class renderer:
    class draw:
        """All functions related to drawing widgets"""

        @staticmethod
        def background(canvas):
            """Draws background"""
            paint = skia.Paint(
                Color=renderer.hex_to_argb(STYLE["bg"]),
                Style=skia.Paint.kFill_Style,
                AntiAlias=True,
            )
            rect = skia.Rect.MakeLTRB(0, 0, WIDTH, HEIGHT)
            canvas.drawRect(rect, paint)

        @staticmethod
        def folder(canvas, y, label="", selected=False):
            """Draws a folder/page widget"""
            folder_height = 32

            if selected:
                fill = skia.Paint(
                    Color=renderer.hex_to_argb(STYLE["highlight"]),
                    Style=skia.Paint.kFill_Style,
                    AntiAlias=True,
                )
                rect = skia.Rect.MakeLTRB(0, y, WIDTH, y + folder_height)
                canvas.drawRect(rect, fill)

            text_paint = skia.Paint(
                Color=renderer.hex_to_argb(STYLE["text"]),
                AntiAlias=False,
            )

            text = skia.TextBlob(label, skia.Font(None, 12.0))
            text_y = y + round(folder_height / 1.5)
            canvas.drawTextBlob(text, STYLE["padding"], text_y, text_paint)

            return folder_height
        
        @staticmethod
        def button(canvas, y, label="", selected=False, mouse_down=False):
            """Draws a clickable button"""
            button_height = 32

            if selected:
                if mouse_down:
                    button_color = STYLE["accent"]
                    border_color = STYLE["accent"]
                else:
                    button_color = STYLE["highlight"]
                    border_color = STYLE["accent"]
            else:
                button_color = STYLE["button"]
                border_color = STYLE["separator"]

            fill = skia.Paint(
                Color=renderer.hex_to_argb(button_color),
                Style=skia.Paint.kFill_Style,
                AntiAlias=True,
            )

            border = skia.Paint(
                Color=renderer.hex_to_argb(border_color),
                Style=skia.Paint.kStroke_Style,
                AntiAlias=False,
                StrokeWidth=1
            )

            text_paint = skia.Paint(
                Color=renderer.hex_to_argb(STYLE["text"]),
                AntiAlias=False,
            )

            text = skia.TextBlob(label, skia.Font(None, 12.0))
            text_y = y + round(button_height / 1.5)
            rect = skia.Rect.MakeLTRB(0, y, WIDTH, y + button_height)
            border_rect = skia.Rect.MakeLTRB(
                0,
                y,
                (WIDTH - 1),
                (y + button_height - 1)
            )
            canvas.drawRect(rect, fill)
            canvas.drawRect(border_rect, border)
            canvas.drawTextBlob(text, STYLE["padding"], text_y, text_paint)

            return button_height

        @staticmethod
        def label(canvas, y, label=""):
            """Draws a text label"""
            folder_height = 24

            text_paint = skia.Paint(
                Color=renderer.hex_to_argb(STYLE["text"]),
                AntiAlias=False,
            )

            text = skia.TextBlob(label, skia.Font(None, 12.0))
            text_y = y + round(folder_height / 1.4)
            canvas.drawTextBlob(text, STYLE["padding"], text_y, text_paint)

            return folder_height

        @staticmethod
        def separator(canvas, y, margin=(0, 0)):
            """Draws a separator line"""
            separator_height = 1
            fill = skia.Paint(
                Color=renderer.hex_to_argb(STYLE["separator"]),
                Style=skia.Paint.kFill_Style,
                AntiAlias=True,
            )

            rect = skia.Rect.MakeLTRB(
                0,
                y + margin[0],
                WIDTH,
                y + margin[0] + separator_height,
            )
            canvas.drawRect(rect, fill)

            return separator_height + margin[0] + margin[1]

    @staticmethod
    def draw_widgets(canvas, widgets, selected_index, mouse_down):
        """Draws each widget in order"""
        for i, w in enumerate(widgets):
            w.selected = (i == selected_index)
            match w.type:
                case "folder":
                    renderer.draw.folder(canvas, w.y, w.label, w.selected)
                case "button":
                    renderer.draw.button(canvas, w.y, w.label, w.selected, mouse_down)
                case "label":
                    renderer.draw.label(canvas, w.y, w.label)
                case "separator":
                    renderer.draw.separator(canvas, w.y)

    @staticmethod
    def hex_to_argb(hex_code="#000", alpha=255):
        """Converts hex codes to Skia ARGB"""
        hex_code = hex_code.lstrip("#")

        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)
        elif len(hex_code) != 6:
            raise ValueError(f"Invalid hex color: {hex_code}")

        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)

        return skia.ColorSetARGB(alpha, r, g, b)


def start(xml_file="demo.xml"):
    """Main UI Function"""
    sdl2.ext.init()
    dom = parser.parse(xml_file)

    window = sdl2.ext.Window(
        dom.attrib["title"],
        size=(WIDTH, HEIGHT),
        flags=sdl2.SDL_WINDOW_SHOWN,
    )

    sdl_renderer = sdl2.SDL_CreateRenderer(
        window.window,
        -1,
        sdl2.SDL_RENDERER_SOFTWARE,
    )

    texture = sdl2.SDL_CreateTexture(
        sdl_renderer,
        sdl2.SDL_PIXELFORMAT_ABGR8888,
        sdl2.SDL_TEXTUREACCESS_STREAMING,
        WIDTH,
        HEIGHT,
    )

    bytes_per_pixel = 4
    row_bytes = WIDTH * bytes_per_pixel
    pixel_buffer = bytearray(HEIGHT * row_bytes)

    surface = skia.Surface.MakeRasterDirect(
        skia.ImageInfo.Make(
            WIDTH,
            HEIGHT,
            skia.kRGBA_8888_ColorType,
            skia.kPremul_AlphaType,
        ),
        pixel_buffer,
        row_bytes,
    )

    canvas = surface.getCanvas()

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

            for i, widget in enumerate(widgets):
                if widget.contains(mouse_x, mouse_y):
                    selected_index = i
                    break

            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                mouse_down = True
            elif event.type == sdl2.SDL_MOUSEBUTTONUP:
                mouse_down = False
                for w in widgets:
                    if w.type == "button" and w.contains(event.button.x, event.button.y):
                        if w.callback:
                            w.callback()


        canvas.clear(skia.ColorWHITE)
        renderer.draw.background(canvas)
        renderer.draw_widgets(canvas, widgets, selected_index, mouse_down)

        # Upload pixels to SDL texture
        pixels = ctypes.c_void_p()
        pitch = ctypes.c_int()
        sdl2.SDL_LockTexture(
            texture,
            None,
            ctypes.byref(pixels),
            ctypes.byref(pitch)
        )
        ctypes.memmove(pixels.value, bytes(pixel_buffer), len(pixel_buffer))
        sdl2.SDL_UnlockTexture(texture)

        # Present to window
        sdl2.SDL_RenderClear(sdl_renderer)
        sdl2.SDL_RenderCopy(sdl_renderer, texture, None, None)
        sdl2.SDL_RenderPresent(sdl_renderer)

        pixels = ctypes.c_void_p()
        pitch = ctypes.c_int()

        sdl2.SDL_LockTexture(
            texture,
            None,
            ctypes.byref(pixels),
            ctypes.byref(pitch),
        )

        ctypes.memmove(
            pixels.value,
            bytes(pixel_buffer),
            len(pixel_buffer),
        )

        sdl2.SDL_UnlockTexture(texture)

        sdl2.SDL_RenderClear(sdl_renderer)
        sdl2.SDL_RenderCopy(sdl_renderer, texture, None, None)
        sdl2.SDL_RenderPresent(sdl_renderer)
        
    sdl2.ext.quit()

if __name__ == "__main__":
    """Errors if you try to run TinyXUI on its own"""
    print("Do not run TinyXUI on its own!")
    print("Import it into another codebase to use it.")