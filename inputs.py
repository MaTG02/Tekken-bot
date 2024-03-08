# This code is the combination of multiple blog posts.
# It uses ctypes to get the processID for PS4 Remote Play
# and then feed keyboard commands to it. Later on I discovered
# REM4P can detect Ctrl + Alt from anywhere and will automatically
# latch onto the PS4 process so the process detection isn't used.
# The code has been kept just for history and just in case it is needed.
#
# The blogs can be found at:
# https://sjohannes.wordpress.com/2012/03/23/win32-python-getting-all-window-titles/
# http://pixomania.net/programming/python-getting-the-title-of-windows-getting-their-processes-and-their-commandlines-using-ctypes-and-win32/
# https://stackoverflow.com/questions/13564851/how-to-generate-keyboard-events-in-python
#

import ctypes
from ctypes import wintypes, c_int, byref
import time, random

user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004
KEYEVENTF_SCANCODE    = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd375731
VK_LMENU    = 0x12 # Left Alt key
VK_LCONTROL = 0xA2 # Left Ctrl key

# Playstation valid buttons
DPAD_UP     = 0x57 # W key
DPAD_DOWN   = 0x53 # S key
DPAD_LEFT   = 0x41 # A key
DPAD_RIGHT  = 0x44 # D key
CROSS       = 0x45 # E key
SQUARE      = 0x52 # R key
CIRCLE      = 0x54 # T key
TRIANGLE    = 0x59 # Y key
R1          = 0x51 # Q key
TOUCHPAD    = 0x58 # X key
OPTIONS     = 0x72 # F3 key
### dzialanie
DIAG_DOWN_LEFT = (DPAD_LEFT, DPAD_DOWN)
DIAG_DOWN_RIGHT = (DPAD_RIGHT, DPAD_DOWN)
DIAG_UP_LEFT = (DPAD_LEFT, DPAD_UP)
DIAG_UP_RIGHT = (DPAD_RIGHT, DPAD_UP)

CROSS_SQUARE = (CROSS, SQUARE)
CROSS_CIRCLE = (CROSS, CIRCLE)
SQUARE_TRIANGLE = (SQUARE, TRIANGLE)
TRIANGLE_CIRCLE = (TRIANGLE, CIRCLE)

delay = ['hold','tap']

direction = [0, DPAD_UP, DPAD_DOWN, DPAD_LEFT, DPAD_RIGHT, DIAG_DOWN_LEFT, DIAG_DOWN_RIGHT, DIAG_UP_LEFT, DIAG_UP_RIGHT]

attack = [0, TRIANGLE, CIRCLE, CROSS, SQUARE, CROSS_SQUARE, CROSS_CIRCLE, SQUARE_TRIANGLE, TRIANGLE_CIRCLE]


# all valid actions
valid_actions = [(x,y) for x in direction for y in attack]


wintypes.ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx",          wintypes.LONG),
                ("dy",          wintypes.LONG),
                ("mouseData",   wintypes.DWORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk",         wintypes.WORD),
                ("wScan",       wintypes.WORD),
                ("dwFlags",     wintypes.DWORD),
                ("time",        wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg",    wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type",   wintypes.DWORD),
                ("_input", _INPUT))

def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

class InputHandler:

    LPINPUT = ctypes.POINTER(INPUT)
    user32.SendInput.errcheck = _check_count
    user32.SendInput.argtypes = (wintypes.UINT, # nInputs
                                 LPINPUT,       # pInputs
                                 ctypes.c_int)  # cbSize

    def __init__(self):
        self.PS4RemotePlayHWND = 0
        self.PS4RemotePlayPID = 0
# Functions

    def get_actions(self, amount):
        actions = []
        actions.append([])
        action = 0
        for i in range(0,amount):
            temp = random.randint(0,1)
            if temp == 0:
                # select something random from the direction arroy
                action = direction[random.randint(0,len(direction)-1)]
            else:
                # select something random from the attack array
                action = attack[random.randint(0,len(direction)-1)]
            # Only add the input if it is not 0. 0 Is the same as nothing.
            if action != 0:
                actions.append(action)
        # Get the delay time for pressing these keys
        delayVal = delay[random.randint(0,1)]
        if delayVal == 'hold':
            # can't use i as the index because I am only adding non 0 inputs
            actions[0].append(random.uniform(0.1, 0.2))
        else:
            # can't use i as the index because I am only adding non 0 inputs
            actions[0].append(random.uniform(0.05, 0.1))
        return actions

    def get_action(self, index):
        return valid_actions[index]

    def get_remote_play_pid(self):
        # register winapi functions
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId

        def foreach_window(self, hwnd, lParam):
            # window must be visible
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                try:
                    windowtitle = buff.value
                    if "PS4" in windowtitle:
                        # get the processid from the hwnd
                        # declaring this as global means refer to the global version
                        #global global_PS4RemotePlayPID
                        #global global_PS4RemotePlayHWND
                        processID = c_int()
                        threadID = GetWindowThreadProcessId(hwnd, byref(processID))
                        # found the process ID
                        self.PS4RemotePlayPID = processID
                        self.PS4RemotePlayHWND = hwnd
                        return True
                except:
                    print("Unexpected error:"+sys.exc_info()[0])
                    pass;
            return True
        EnumWindows(EnumWindowsProc(foreach_window(self)), 0)


    def press_key(self, hexKeyCode):
        x = INPUT(type=INPUT_KEYBOARD,
                  ki=KEYBDINPUT(wVk=hexKeyCode))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def release_key(self, hexKeyCode):
        x = INPUT(type=INPUT_KEYBOARD,
                  ki=KEYBDINPUT(wVk=hexKeyCode,
                                dwFlags=KEYEVENTF_KEYUP))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

