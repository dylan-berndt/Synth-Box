

names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
values = [261.63 * ((2 ** (1/12)) ** i) for i in range(len(names))]
notes = dict(zip(names, values))


def interpret(data):
    if data == "":
        return 0, ""
    if type(data) == str:
        try:
            num = float(data)
            return num, data
        except ValueError:
            if data[0] in names:
                if len(data) > 1 and data[1] == "#":
                    if len(data) > 2 and data[2].isnumeric():
                        num = round(notes[data[0:2]] * (2 ** (int(data[2]) - 4)), 2)
                        return num, str(num)
                    else:
                        return notes[data[0:2]], data
                elif len(data) > 1 and data[1].isnumeric():
                    num = round(notes[data[0]] * (2 ** (int(data[1]) - 4)), 2)
                    return num, str(num)
                else:
                    return notes[data[0]], data
            else:
                return 0, ""
    if type(data) in [int, float]:
        return data, str(data)
    return 0, ""


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
            self.value = 0

        ListElement.all_elements.append(self)


class NumberEdit(ListElement):
    def __init__(self, name, value):
        super().__init__([Text(name), Number(value)])

        self.name = name
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, data):
        data = interpret(data)
        self._value = data[0]
        self.items[1].text = data[1]


class Button(ListElement):
    def __init__(self, name, function, args=None):
        self.name = name
        self.function = function
        self.args = args

        super().__init__([Text(name)])


class Expand(ListElement):
    def __init__(self, name, expand):
        self.name = name
        self.items = expand
        super().__init__([Text(name)])

