

class ListItem:
    def __init__(self):
        self.text = ""


class Text(ListItem):
    def __init__(self, text):
        super().__init__()
        self.text = text


class Number(ListItem):
    def __init__(self, num):
        super().__init__()
        self.text = str(num)


class List(ListItem):
    def __init__(self, text, items):
        super().__init__()
        self.text = text + ">"
        self.items = items


class ListElement:
    all_elements = []

    def __init__(self, rows):
        self.height = len(rows)
        self.items = rows
        if not hasattr(self, "value"):
            self.value = None

        ListElement.all_elements.append(self)


class NumberEdit(ListElement):
    def __init__(self, name, value):
        self.name = name
        self.value = value

        super().__init__([Text(name), Number(value)])


class Button(ListElement):
    def __init__(self, name, function, args=None):
        self.name = name
        self.function = function
        self.args = args

        super().__init__([Text(name)])

