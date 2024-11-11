from pynput import keyboard
from _thread import start_new_thread


KEYBOARD_SERVER = None


class KeyboardServer:
    def __init__(self, hotkey=keyboard.Key.backspace):
        print(f"[KeyboardServer] Hotkey: {hotkey}")
        self.hotkey = hotkey
        self.pressed = False

        start_new_thread(self.start, ())

    def on_press(self, key):
        if not self.pressed and key == self.hotkey:
            self.pressed = True

    def on_release(self, key):
        if key == self.hotkey:
            self.pressed = False

    def get_key(self):
        return self.pressed

    def start(self):
        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()


def construct_keyboard_reward(hotkey=keyboard.Key.backspace):
    print(f"[Keyboard Reward] Hotkey: {hotkey}")

    global KEYBOARD_SERVER
    if KEYBOARD_SERVER is None:
        KEYBOARD_SERVER = KeyboardServer(hotkey)

    def keyboard_reward(*args, **kwargs):
        return KEYBOARD_SERVER.get_key()

    return keyboard_reward
