LAYER_SPACE = 3


class TreeVisualizer:
    def __init__(self, tree, names, current_index):
        self.layers = []
        self.names = {}
        self.current = current_index
        for j in range(len(tree)):
            for i in range(len(tree[j])):
                if i >= len(self.layers):
                    self.layers.append([])
                pair = (tree[j][i], -1) if i == 0 else (tree[j][i],
                                                        tree[j][i - 1])
                if pair not in self.layers[i]:
                    self.layers[i].append(pair)
        for name in names:
            self.names[names[name]] = name

    def draw(self, silent=False):
        if silent:
            return
        if self.current == -1:
            print(f'<{self.names[-1]}>', end=' ')
        else:
            print(f'{self.names[-1]}', end=' ')
        self._draw_childes(0, -1)
        print()

    def _draw_childes(self, start_layer, el, last=False):
        if start_layer == len(self.layers):
            return
        element_to_avoid = None
        index = 0
        for element in self.layers[start_layer]:
            index += 1
            if element[1] == el and self._has_no_branches(element[0]):
                sep = '→'
                print(sep, end=' ')
                if self.current == element[0]:
                    print(f'<{self.names[element[0]]}>', end=' ')
                else:
                    print(self.names[element[0]], end=' ')
                element_to_avoid = element[0]
                if start_layer == 0:
                    last = index >= len(self.layers[start_layer])
                self._draw_childes(start_layer + 1,
                                   element[0],
                                   last)
                break
        index = 0
        for element in self.layers[start_layer]:
            index += 1
            if element[1] == el and element[0] != element_to_avoid:
                print()
                sep = ' ' * (start_layer * LAYER_SPACE - 1)
                if start_layer >= 1 and not last:
                    sep = '|' + sep
                else:
                    sep += min(start_layer * LAYER_SPACE, 1) * ' '
                sep = sep + '|→'
                print(sep, end=' ')
                if self.current == element[0]:
                    print(f'<{self.names[element[0]]}>', end=' ')
                else:
                    print(self.names[element[0]], end=' ')
                if start_layer == 0:
                    last = index >= len(self.layers[start_layer])
                self._draw_childes(start_layer + 1,
                                   element[0],
                                   last)

    def _get_child_count(self, element):
        counter = 0
        for layer in self.layers:
            for _, parent in layer:
                if parent == element:
                    counter += 1
        return counter

    def _get_first_child(self, element):
        for layer in self.layers:
            for child, parent in layer:
                if parent == element:
                    return child

    def _has_no_branches(self, element):
        if self._get_child_count(element) == 0:
            return True
        if self._get_child_count(element) > 1:
            return False
        return self._has_no_branches(self._get_first_child(element))
