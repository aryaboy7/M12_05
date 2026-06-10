from kivy.core.window import Window


def font(base):
    w = Window.width

    # M12
    if w < 700:
        scale = 0.80

    # Phone
    elif w < 900:
        scale = 1.00

    # Tablet
    elif w < 1400:
        scale = 1.10

    # Desktop
    else:
        scale = 1.00

    return int(base * scale)


def height(base):
    w = Window.width

    if w < 700:
        scale = 0.85
    elif w < 900:
        scale = 1.00
    elif w < 1400:
        scale = 1.05
    else:
        scale = 1.00

    return int(base * scale)