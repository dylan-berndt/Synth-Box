
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


class ListElement:
    all_elements = []

    def __init__(self, rows):
        self.height = len(rows)
        self.items = rows

        ListElement.all_elements.append(self)


class NumberEdit(ListElement):
    def __init__(self, name, value):
        self.name = name
        self.value = value

        super().__init__([Text(name), Number(value)])

