from time import time

class Timer(object):
    __slots__ = 'path', 'path_starts', 'times'

    def __init__(self):
        self.path = ()
        self.path_starts = ()
        self.times = {}

    def __call__(self, path):
        self.path += path,
        self.path_starts += time(),
        return self

    def __enter__(self):
        pass

    def __exit__(self, *exc):
        end_time = time()

        my_time = self.times.get(self.path, 0)
        my_time += end_time - self.path_starts[-1]
        self.times[self.path] = my_time

        self.path = self.path[:-1]
        self.path_starts = self.path_starts[:-1]

        return False


class StringTree(object):
    __slots__ = 'string', 'children'

    def __init__(self, string, children):
        self.string = string
        self.children = children

    def _make_indent(self, indent):
        if not indent:
            return ""

        result = ""
        for line in indent:
            if line:
                result += "│   "
            else:
                result += "    "

        if indent[-1]:
            result += "├───"
        else:
            result += "└───"

        return result

    def to_indented_str(self, indent):
        result = self.string + "\n"
        if self.children:
            next_indent = indent + (True,)
            for child in self.children[:-1]:
                result += child.to_indented_str(next_indent)
            result += children[-1].to_indented_str(indent + (False,))
        return result

    def __str__(self):
        return to_indented_str(indent=())


def timer_to_tree(timer, root_label="Root"):
    times = sorted(timer.times.items())

    last_depth = 0
    children = []

    for name, time in times:
        label = "%s (%s)" % (name[-1], time)

        depth = len(name)
        if depth > last_depth:
            children.append(label)
            assert(depth == last_depth + 1)
        else:
            # TODO 
            pass


t = Timer()
with t("Test one"):
    with t("Test two"):
        pass
    with t("Test three"):
        with t("Test four"):
            pass
with t("Test five"):
    pass

print(t.times)
print(timer_to_tree(t.times))
