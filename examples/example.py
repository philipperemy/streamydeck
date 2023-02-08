import logging
import sys

from streamydeck import init_stream_deck, Element, View, terminate, start


class Calculator:

    def __init__(self):
        self.keys_pressed = []
        self.calc_view = None
        self.main_view = None

    def compute(self):
        # noinspection PyBroadException
        try:
            result = eval(''.join(self.keys_pressed))
            self.keys_pressed.clear()
            is_int = all([str(a).isdigit() for a in list(str(result))])
            if is_int:
                result_as_list = list(str(result))
            else:
                result_as_list = list('{:g}'.format(float(f'{result:.3f}')))
            result_view = View('result', self.calc_view.deck, render_on_assign=False)
            for key, v in enumerate(result_as_list[0:14]):
                j = key % result_view.key_cols
                i = int((key - j) / result_view.key_cols)
                result_view[i, j] = Element('black', label=str(v), text_only=True, font_size=50)
            result_view[-1, -1] = Element('go_back', has_cooldown=False).on_action(self.main_view.render)
            result_view.render()
        except Exception:
            pass

    def on_key(self, elt: Element):
        self.keys_pressed.append(elt.label)


class Brightness:

    def __init__(self):
        self.value = 50

    def adjust_brightness(self, deck, up: bool, elt: Element, view: View):
        if up:
            if self.value == 100:
                return
            self.value += 10
        else:
            if self.value == 0:
                return
            self.value -= 10
        deck.set_brightness(self.value)
        elt.label = f'Brightness {int(self.value)}%'
        view.render(elt)


def create_terminate_view(deck, parent_view: View) -> View:
    view = View('confirm', deck)
    view[-1, 0] = Element('yes', has_cooldown=False).on_action(terminate, deck)
    view[-1, -1] = Element('no', has_cooldown=False).on_action(parent_view.render)
    return view


def create_calculator_view(deck, calc: Calculator) -> View:
    view = View('calculator', deck)
    # numbers.
    view[0, 0] = Element('black', label='0', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[0, 1] = Element('black', label='1', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[0, 2] = Element('black', label='2', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[0, 3] = Element('black', label='3', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[0, 4] = Element('black', label='4', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[1, 0] = Element('black', label='5', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[1, 1] = Element('black', label='6', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[1, 2] = Element('black', label='7', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[1, 3] = Element('black', label='8', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[1, 4] = Element('black', label='9', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    # operations.
    view[2, 0] = Element('black', label='+', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[2, 1] = Element('black', label='-', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[2, 2] = Element('black', label='/', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    view[2, 3] = Element('black', label='*', text_only=True, font_size=50, elt_to_action=True).on_action(calc.on_key)
    # go back to main view.
    view[-1, -1] = Element('black', text_only=True, label='ENTER').on_action(calc.compute)
    for i in range(15):
        view.get_from_key_id(i).has_cooldown = False
    return view


def create_brightness_view(deck, brightness: Brightness, parent_view: View) -> View:
    deck.set_brightness(brightness.value)
    view = View('settings', deck)
    text = Element(name='black', label='', text_only=True)

    view[0, 0] = Element(name='icon-up', label='Brightness', has_cooldown=False). \
        on_action(brightness.adjust_brightness, deck=deck, up=True, elt=text, view=view)
    view[1, 0] = text
    view[2, 0] = Element(name='icon-down', label='Brightness', has_cooldown=False). \
        on_action(brightness.adjust_brightness, deck=deck, up=False, elt=text, view=view)

    view[0, -1] = Element(name='settings', label='')
    view[-1, -1] = Element('go_back', has_cooldown=False).on_action(parent_view.render)
    return view


def main():
    deck = init_stream_deck()

    # Define objects with internal states.
    brightness = Brightness()
    calc = Calculator()

    # Define views.
    main_view = View('main', deck)
    settings_view = create_brightness_view(deck, brightness, main_view)
    calc_view = create_calculator_view(deck, calc)
    terminate_view = create_terminate_view(deck, main_view)
    calc.calc_view = calc_view
    calc.main_view = main_view

    main_view[0, 0] = Element(name='settings', label='Settings', has_cooldown=False).on_action(settings_view.render)
    main_view[0, 1] = Element(name='calc', label='Calculator', has_cooldown=False).on_action(calc_view.render)
    main_view[-1, -1] = Element('exit', has_cooldown=False).on_action(terminate_view.render)
    main_view.render()

    start(deck)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(threadName)-9s - %(levelname)-4s - %(message)s',
        stream=sys.stdout
    )
    main()
