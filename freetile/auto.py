"""
TODO
"""

import setproctitle
import logging
from Xlib import X, display
from .helper.helper_ewmh import ewmh
from .main import regularize
from .util_kdtree import insert_focused_window_into_kdtree
from .windowlist import windowlist


def search_window(win, lst):
    logging.debug('search window')
    for win_target, win_test in lst:
        logging.debug('%s', win_test.id)
        if win_test.id == win.id:
            logging.debug('find window:%s',win_target.id)
            return win_target
    else:
        plst = []
        for win_target, win_test in lst:
            pwin = win_test.query_tree().parent
            logging.debug('window %s has parent %s',win_test.id,pwin.id)
            if pwin is not None:
                plst.append((win_target, pwin))
        if len(plst) > 0:
            return search_window(win, plst)
        else:
            logging.info("can't find window:%s", win.id)
            return None

def loop():
    setproctitle.setproctitle("freetile-auto")

    disp = display.Display()
    root = disp.screen().root
    # | X.SubstructureRedirectMask)
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
    ]
    IGNORE_STATES = [
        disp.intern_atom('_NET_WM_STATE_ABOVE'),
        disp.intern_atom('_NET_WM_STATE_STICKY'),
        disp.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
        disp.intern_atom('_NET_WM_STATE_SKIP_PAGER'),
    ]
    IGNORE_TYPES = set(IGNORE_TYPES)
    IGNORE_STATES = set(IGNORE_STATES)

    regularize()

    def insert_window(win):
        c = win.get_wm_class()
        n = win.get_wm_name()
        s = ewmh.getWmState(win)
        t = ewmh.getWmWindowType(win)

        if not IGNORE_STATES.isdisjoint(s):
            logging.debug('wmstate:%s', s)
            return False
        if len(t) < 1 or not IGNORE_TYPES.isdisjoint(t):
            logging.debug('window type:%s', t)
            return False
        if c is not None and 'Popup' in c:
            logging.debug('wmclass:%s', c)
            return False

        wininfo[win.id] = c, n, t, s
        return True

    for win in ewmh.getClientList():
        insert_window(win)

    def add_window(win):
        logging.debug('add window')
        for _ in range(50):
            try:
                lst = ewmh.getClientList()
            except BaseException:
                logging.info('fail %s' % _)
                return True

        newwin = search_window(win, zip(lst, lst))
        if newwin:
            win = newwin
            logging.debug('window id:%s', win.id)
            if insert_window(win):
                logging.info([e.type, *wininfo[win.id]])
                windowlist.reset()
                num = len(windowlist.windowInCurrentWorkspaceInStackingOrder)
                if not regularize(force_tiling=False,
                                  minimum_regularized_window=num - 1):
                    return False
        return True

    while True:
        logging.debug('next event')
        e = disp.next_event()
        if e.type == X.MapNotify:
            logging.debug('MapNotify event')
            win = e.window
            if not add_window(win):
                logging.info('failed to add new window')
                break
        elif e.type == X.UnmapNotify:
            logging.debug('UnmapNotify event')
            win = e.window
            if win.id in wininfo:
                logging.info([e.type, *wininfo.pop(win.id)])
                windowlist.reset(ignore=[win.id])
                if len(windowlist.windowInCurrentWorkspaceInStackingOrder) < 1:
                    logging.info('no window exists')
                    # quit auto tiling when no window exists.
                    break
                regularize()
    # Quit loop when detect overlapped windows created by user.
    logging.info('quit autotiling')
