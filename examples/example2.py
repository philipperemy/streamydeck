from streamydeck import init_stream_deck, Element, View, start, terminate


def main():
    deck = init_stream_deck()
    my_view = View('main', deck)
    my_view[0, 0] = Element('exit', label='Exit').on_action(terminate, deck)
    my_view.render()
    start(deck)


if __name__ == '__main__':
    main()
