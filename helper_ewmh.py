from ewmh import EWMH
from helper_xlib import get_window

ewmh = EWMH()


@get_window
def raise_window(win):
    ewmh.setActiveWindow(win)
    ewmh.display.flush()


def get_window_list(ignore=[]):
    """
    in stacking order.
    """
    for win in ewmh.getClientListStacking():
        if win.id in ignore:
            continue
        name = ewmh.getWmName(win)
        if name is not None:
            name = name.decode('utf8')
        yield win, ewmh.getWmDesktop(win), name
