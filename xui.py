from txm import AST as txm
import layout
import sdl2
import sdl2.ext
import sdl2.sdlttf
import style_provider


bindings = {}
widget_map = {}


STYLE = {
    "bg": "#eff0f1",
    "accent": "#3daee9",
    "button": "#fcfcfc",
    "separator": "#d1d2d3",
    "text": "#232629",
    "highlight": "#badcee",
}


def hex_to_argb(hex_code, alpha=255):
    """
    Converts hex codes to SDL ARGB (r, g, b, alpha)
    
    :param hex_code: Hex code for color, Ex: #FFF or #432fca
    :param alpha: Transparancy level, 255 is opaque, 0 is invisible
    """
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return sdl2.SDL_Color(r, g, b, alpha)


def draw_widget(widget):
    """
    Draws a provided widget on the screen
    
    :param widget: Widget object
    """
    ast = style_provider.generate_ast("default.css")
    match widget.name:
        case "label":
            text_color = style_provider.Provider.get_property(
                ast,
                "label",
                "color"
            )
            color = style_provider.hex_to_argb(text_color)
            surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(
                font, str(widget.data).encode("utf-8"), color
            )
            if not surface:
                print("Failed to render text")
                return

            texture = sdl2.SDL_CreateTextureFromSurface(sdl_renderer, surface)
            if not texture:
                print("Failed to create texture")
                sdl2.SDL_FreeSurface(surface)
                return

            rect = sdl2.SDL_Rect(widget.x, widget.y, surface.contents.w,
                                surface.contents.h)
            sdl2.SDL_RenderCopy(sdl_renderer, texture, None, rect)
            sdl2.SDL_FreeSurface(surface)
            sdl2.SDL_DestroyTexture(texture)

        case "image":
            if not hasattr(widget, "texture_cache"):
                file_path = widget.attributes.get("src", "missing.png")
                surface = sdl2.ext.load_image(file_path)
                widget.texture_cache = sdl2.SDL_CreateTextureFromSurface(
                    sdl_renderer, surface)
                widget.texture_w, widget.texture_h = surface.w, surface.h

                sdl2.SDL_FreeSurface(surface)

            rect = sdl2.SDL_Rect(widget.x, widget.y, widget.width, widget.height)
            sdl2.SDL_RenderCopy(sdl_renderer, widget.texture_cache, None, rect)

        case _:
            style_provider.Provider.draw(ast, widget, sdl_renderer=sdl_renderer)
    # Draw children
    for child in widget.children:
        draw_widget(child)


def build_widget_map(widget):
    """
    Recursively build a mapping of widget IDs to widget objects.
    
    :param widget: Widget object
    """
    wid = widget.attributes.get("id")
    if wid:
        widget_map[wid] = widget
    for child in widget.children:
        build_widget_map(child)


def bind_widget(widget_id, callback):
    """
    Bind a function to a widget by its ID
    
    :param widget_id: ID of specified widget
    :param callback: Function to run
    """
    bindings[widget_id] = callback


def set_data(widget_id, data):
    """
    Set inner data via a widget's ID
    
    :param widget_id: ID of specified widget
    :param data: Data to replace with
    """
    widget = widget_map.get(widget_id)
    if widget:
        widget.data = data
        return True
    return False


def refresh_image(widget_id):
    """
    Force an image widget to reload from disk
    
    :param widget_id: ID of specified widget
    """
    widget = widget_map.get(widget_id)
    if not widget:
        return False

    # Remove the cached texture so draw_widget recreates it
    if hasattr(widget, "texture_cache"):
        import sdl2
        sdl2.SDL_DestroyTexture(widget.texture_cache)
        del widget.texture_cache

    return True


def handle_event(event, widget):
    """
    Recursively check widgets for a click event and call bound function
    
    :param event: SDL event object
    :param widget: Widget object
    """
    mouse_x = event.button.x
    mouse_y = event.button.y

    # Check if mouse is inside this widget
    if widget.x <= mouse_x <= widget.x + widget.width and \
        widget.y <= mouse_y <= widget.y + widget.height:
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            widget.active = True
        elif event.type == sdl2.SDL_MOUSEBUTTONUP:
            widget.active = False
            widget_id = widget.attributes.get("id")
            if widget_id and widget_id in bindings:
                bindings[widget_id]()  # call bound function
        else:
            widget.hovered = True
            widget.active = False
    else:
        widget.hovered = False
        widget.active = False

    # Recurse into children
    for child in widget.children:
        handle_event(event, child)


def start(file):
    """
    Public function to start a XUI instance
    
    :param file: TXM markup file to read from
    """
    global settings
    global widgets
    global font
    global sdl_renderer
    ast = txm.generate_ast(file)
    settings = ast[0]
    widgets = ast[1]
    build_widget_map(widgets)
    running = True

    # Initialize SDL
    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()
    font = sdl2.sdlttf.TTF_OpenFont(b"NotoSans.ttf", 13)

    # Initialize window and renderer
    window = sdl2.ext.Window(
        settings["window_title"],
        size=(settings["width"], settings["height"]),
        flags=sdl2.SDL_WINDOW_SHOWN,
    )
    sdl_renderer = sdl2.SDL_CreateRenderer(
        window.window,
        -1,
        sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC,
    )
    event = sdl2.SDL_Event()

    while running:
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_QUIT:
                running = False

            handle_event(event, widgets)


        sdl2.SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(sdl_renderer)
        layout.compute_layout(widgets, settings=settings, font=font)
        draw_widget(widgets)

        sdl2.SDL_RenderPresent(sdl_renderer)

    sdl2.SDL_DestroyRenderer(sdl_renderer)
    window.close()
    sdl2.ext.quit()

if __name__ == "__main__":
    """
    Errors if you try to run TinyXUI on its own
    """
    print("Do not run TinyXUI on its own!")
    print("Import it into another codebase to use it.")