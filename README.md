## Streamy Deck

Build apps easily on the Stream Deck.

*Streamy* is based on objects we call `View`. A view is a 2D `3*5` (the number of cells on the deck) grid containing one `Element` per cell.

`my_view[i, j]` points to the i-th row and j-th column `Element`. Each `Element` is associated with an action when a user presses this button.

The idea of *Streamy* is to navigate through different views when an action occurs.

*Available on PyPI*

```
pip install streamydeck
```

### Get Started

Let's build a simple app to display an exit button. If we click on it, the program will close.

```python
from streamydeck import init_stream_deck, Element, View, start, terminate

deck = init_stream_deck()
my_view = View('main', deck)
my_view[0, 0] = Element('exit', label='Exit').on_action(terminate, deck)
my_view.render()
start(deck)
```

You will see this on your Stream Deck:

<img src="assets/exit.jpg"></img>

### Other examples

It's easy to build more complicated apps like a calculator: [assets/calc.mp4](assets/calc.mp4).
