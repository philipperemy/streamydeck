import logging
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

logger = logging.getLogger(__name__)

ASSETS_PATH = Path(__file__).parent / 'assets'

COOLDOWN_KEY_PRESSED = 2


# noinspection DuplicatedCode
def render_key_image(deck, icon_filename, font_filename, label_text, text_only, background='black', font_size=14):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0], background=background)

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, font_size)
    if text_only:
        h = image.height / 2 + 10
    else:
        if len(label_text) == 0:
            h = image.height
        else:
            h = image.height - 5
    text = label_text.replace(' ', '\n') if text_only else label_text
    draw.text((image.width / 2, h), text=text, font=font, anchor='ms', fill='white')
    return PILHelper.to_native_format(deck, image)


class Element:

    def __init__(self, name: str, icon=None, label=None, text_only=False,
                 has_cooldown=True, background='black', font_size=14,
                 elt_to_action=False):
        self.name = name
        self.raw_icon = icon
        self.font = 'Roboto-Regular.ttf'
        self.action = None
        self.font_size = font_size
        self.has_cooldown = has_cooldown
        self.uid = str(uuid.uuid4())
        self.text_only = text_only
        self.background = background
        self.self_as_arg = elt_to_action
        self.label = self.name.replace('_', ' ').title() if label is None else label
        assert Path(self.icon_filename).exists(), Path(self.icon_filename)
        assert Path(self.font_filename).exists(), Path(self.font_filename)

    @property
    def icon(self):
        return self.name.lower() + '.png' if self.raw_icon is None else self.raw_icon

    def copy(self, action=False):
        elt = Element(self.name, self.icon)
        if action:
            elt.action = action
        return elt

    @property
    def icon_filename(self):
        return str(ASSETS_PATH / 'icons' / self.icon)

    def __str__(self):
        attr = str(self.name)
        if self.action is not None:
            callback, args, kwargs = self.action
            attr += f' - {callback.__name__}({args}, {kwargs}))'
        return str(attr)

    @property
    def font_filename(self):
        return str(ASSETS_PATH / 'fonts' / self.font)

    def image(self, deck):
        return render_key_image(
            deck=deck,
            icon_filename=self.icon_filename,
            font_filename=self.font_filename,
            label_text=self.label,
            text_only=self.text_only,
            background=self.background,
            font_size=self.font_size
        )

    def on_action(self, callback, *args, **kwargs):
        self.action = callback, args, kwargs
        return self

    def set_background(self, background):
        if self.text_only:
            self.name = background
        self.background = background


class View:
    current = None
    frames = {}

    def __init__(self, name, deck, render_on_assign=False):
        self.name = name
        self.deck = deck
        self.render_on_assign = render_on_assign
        self.key_rows, self.key_cols = self.deck.key_layout()
        self.states = [[None for _ in range(self.key_cols)] for _ in range(self.key_rows)]
        View.frames[self.name] = self
        if View.current is None:
            View.current = self.name

    def __getitem__(self, index) -> Optional[Element]:
        i, j = index
        return self.states[i][j]

    def full_assign(self, elt: Optional[Element]):
        for i in range(self.key_rows):
            for j in range(self.key_cols):
                self[i, j] = elt
                time.sleep(0.01)

    def key_from_index(self, index):
        i, j = index
        if j == -1:
            j = self.key_cols - 1
        if i == -1:
            i = self.key_rows - 1
        key = i * self.key_cols + j
        return key

    def get_from_key_id(self, key: int) -> Optional[Element]:
        j = key % self.key_cols
        i = int((key - j) / self.key_cols)
        if i < 0:
            i = 0
        return self[i, j]

    def __str__(self):
        return str('\n'.join(['\t'.join([str(cell) for cell in row]) for row in self.states]))

    def __setitem__(self, index, elt: Optional[Element]):
        i, j = index
        key = self.key_from_index(index)
        self.states[i][j] = elt
        if self.render_on_assign:
            image = None if elt is None else elt.image(self.deck)
            self.send_image_to_deck(key, image)

    def clear(self):
        for i in range(self.key_rows):
            for j in range(self.key_cols):
                key = self.key_from_index((i, j))
                self.send_image_to_deck(key, None)

    def send_image_to_deck(self, key, image):
        is_in_focus = View.current == self.name
        View.current = self.name
        if not is_in_focus:
            self.clear()
        with self.deck:
            self.deck.set_key_image(key, image)

    def render(self, elt=None):
        if elt is None:
            self.clear()
        for i in range(self.key_rows):
            for j in range(self.key_cols):
                key = self.key_from_index((i, j))
                state = self.states[i][j]
                if elt is not None and state != elt:
                    continue
                # noinspection PyUnresolvedReferences
                image = None if state is None else state.image(self.deck)
                self.send_image_to_deck(key, image)


def init_stream_deck():
    stream_decks = DeviceManager().enumerate()
    if len(stream_decks) != 1:
        print('Is the stream deck plugged?')
        sys.exit(1)
    deck = stream_decks[0]
    deck.open()
    deck.reset()
    print(f'Opened {deck.deck_type()} device (serial number: {deck.get_serial_number()})')
    deck.set_brightness(30)
    return deck


def wait_until_completion():
    # Wait until all application threads have terminated (for this example, this is when all deck handles are closed).
    for t in threading.enumerate():
        try:
            t.join()
        except RuntimeError:
            pass


def start(deck):
    deck.set_key_callback(KeyChangeCallback().key_change_callback)
    wait_until_completion()


def terminate(deck):
    with deck:
        deck.reset()
        deck.close()


class KeyChangeCallback:

    def __init__(self):
        self.previous_actions = {}

    # noinspection PyUnusedLocal
    def key_change_callback(self, deck, key, state):
        focus = View.frames[View.current]
        if focus is not None:
            elt: Element = focus.get_from_key_id(key)
            if elt is not None and elt.action is not None and state:
                if elt.uid in self.previous_actions:
                    last_time_pressed = self.previous_actions[elt.uid]
                    if time.time() - last_time_pressed < COOLDOWN_KEY_PRESSED and elt.has_cooldown:
                        logger.warning(f'Key pressed again: {key}. Ignoring.')
                        return
                callback, args, kwargs = elt.action
                logger.info(f'Key pressed: {key}, callback: {callback.__name__}.')
                self.previous_actions[elt.uid] = time.time()
                if elt.self_as_arg:
                    callback(elt, *args, **kwargs)
                else:
                    callback(*args, **kwargs)
