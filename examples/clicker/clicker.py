import tinyxui as xui

clicker_value = 0

def on_click(amount):
    global clicker_value
    clicker_value += amount
    xui.set_data("click_label", f"Clicker: {str(clicker_value)}")

xui.bind_widget("click_down", lambda: on_click(-1))
xui.bind_widget("click_up", lambda: on_click(1))

xui.start("clicker.txm")
