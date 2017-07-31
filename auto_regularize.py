"""
TODO
"""
import setproctitle
setproctitle.setproctitle("kdtreeautotile")

import Xlib
from Xlib import X, display, Xutil, protocol
import os
import ewmh
ewmh = ewmh.EWMH()
disp = display.Display()
root = disp.screen().root
root.change_attributes(event_mask=X.SubstructureNotifyMask)

wininfo = {}

IGNORE_TYPES = [
    disp.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_DOCK'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_TOOLBAR'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_MENU'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_UTILITY'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_SPLASH'),
    disp.intern_atom('_NET_WM_WINDOW_TYPE_DIALOG'),
    #    390,  # emerald
    #    391,  # volnoti
    #    348,  # docky setting
    #        disp.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL'),
]
IGNORE_STATES = [
    disp.intern_atom('_NET_WM_STATE_ABOVE'),
    disp.intern_atom('_NET_WM_STATE_STICKY'),
    disp.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
    disp.intern_atom('_NET_WM_STATE_SKIP_PAGER'),
]
IGNORE_TYPES = set(IGNORE_TYPES)
IGNORE_STATES = set(IGNORE_STATES)

os.system('python ./main.py layout regularize &> /dev/null')


def insert_window(win):
    c = win.get_wm_class()
    n = win.get_wm_name()
    s = ewmh.getWmState(win)
    t = ewmh.getWmWindowType(win)
    wininfo[win.id] = c, n, t, s


for win in ewmh.getClientList():
    insert_window(win)

while True:
    e = disp.next_event()
    if e.type in (
            X.UnmapNotify,
            X.MapNotify,
        # X.MappingNotify, # what is this?
            # X.ReparentNotify,
            # X.DestroyNotify
    ):
        win = e.window
        if e.type == X.MapNotify:
            if win.id not in [w.id for w in ewmh.getClientList()]:
                print('not a client')
                continue
            insert_window(win)
        elif e.type == X.UnmapNotify:
            if win.id not in wininfo:
                continue
        else:
            print(e.type)
        c, n, t, s = wininfo[win.id]
        print([e.type, n, c, t, s])
        if len(IGNORE_STATES.intersection(s)) > 0:
            continue
        if len(IGNORE_TYPES.intersection(t)) < 0 or len(t) < 1:
            continue
        if not None == c and 'Popup' in c:
            continue

        print('excute')
        os.system('python ./main.py layout regularize &> /dev/null')
