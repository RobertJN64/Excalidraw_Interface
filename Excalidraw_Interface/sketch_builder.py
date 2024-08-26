""" SketchBuilder class for creating Excalidraw JSON files."""

from Excalidraw_Interface import primitives, defaults
import json
import math
import copy
import uuid

class SketchBuilder:
    """SketchBuilder class for creating Excalidraw files."""

    def __init__(self, **custom_defaults):
        """
        Create a sketch
        :param custom_defaults: overrides normal defaults
        """

        self.data = {
            "type": "excalidraw",
            "version": 1,
            "source": "Excalidraw.py",
            "elements": [],
            "appState": {
                "viewBackgroundColor": "#ffffff",
                "gridSize": None,
            }
        }
        self.draw_objs: list[primitives.ExcaliDrawPrimitive] = []

        self.BOX_DEFAULTS = copy.deepcopy(defaults.BOX_DEFAULTS)

        self.LINE_DEFAULTS = copy.deepcopy(defaults.BOX_DEFAULTS)
        self.LINE_DEFAULTS.update(copy.deepcopy(defaults.LINE_DEFAULTS))

        self.TEXT_DEFAULTS = copy.deepcopy(defaults.BOX_DEFAULTS)
        self.TEXT_DEFAULTS.update(copy.deepcopy(defaults.TEXT_DEFAULTS))

        for key, value in custom_defaults.items():
            used = False

            if key in self.BOX_DEFAULTS:
                self.BOX_DEFAULTS[key] = value
                used = True

            if key in self.LINE_DEFAULTS:
                self.BOX_DEFAULTS[key] = value
                used = True

            if key in self.TEXT_DEFAULTS:
                self.BOX_DEFAULTS[key] = value
                used = True

            if not used:
                raise Exception(f"Key <{key}> not used.")

    def add_element(self, element: primitives.ExcaliDrawPrimitive):
        self.draw_objs.append(element)
        return element

    def Rectangle(self, x: int, y: int, width: int = 100, height: int = 100, **kwargs):
        """
        Creates a rectangle
        :param x: center x
        :param y: center y
        :param width: width
        :param height: height
        :param kwargs: other properties
        """
        return self.add_element(primitives.Shape('rectangle', self.BOX_DEFAULTS, x, y, width, height, **kwargs))

    def Diamond(self, x: int, y: int, width: int = 100, height: int = 100, **kwargs):
        """
        Creates a diamond
        :param x: center x
        :param y: center y
        :param width: width
        :param height: height
        :param kwargs: other properties
        """
        return self.add_element(primitives.Shape('diamond', self.BOX_DEFAULTS, x, y, width, height, **kwargs))

    def Ellipse(self, x: int, y: int, width: int = 100, height: int = 100, **kwargs):
        """
        Creates a ellipse
        :param x: center x
        :param y: center y
        :param width: width
        :param height: height
        :param kwargs: other properties
        """
        return self.add_element(primitives.Shape('ellipse', self.BOX_DEFAULTS, x, y, width, height, **kwargs))

    def Text(self, text: str, x: int, y: int, **kwargs):
        """
        Creates text
        :param text: text
        :param x: center x
        :param y: center y
        :param kwargs: other properties
        """
        return self.add_element(primitives.Text(text, self.TEXT_DEFAULTS, x, y, **kwargs))

    def Line(self, start_pt: tuple, end_pt: tuple, **kwargs):
        return self.add_element(primitives.Line('line', self.LINE_DEFAULTS, start_pt, end_pt, **kwargs))

    def Arrow(self, start_pt: tuple, end_pt: tuple, **kwargs):
        kwargs['endArrowhead'] = 'arrow'
        arrow = primitives.Line('arrow', self.LINE_DEFAULTS, start_pt, end_pt, **kwargs)
        self.add_element(arrow)
        return arrow

    def DoubleArrow(self, start_pt: tuple, end_pt: tuple, **kwargs):
        kwargs['startArrowhead'] = 'arrow'
        return self.Arrow(start_pt, end_pt, **kwargs)

    def export_to_file(self, save_path):
        """Export the sketch to a excalidraw file."""
        for element in self.draw_objs:
            json_obj = element.export()
            self.data['elements'].append(json_obj)

        if save_path.split(".")[-1] != "excalidraw":
            save_path += ".excalidraw"

        with open(save_path, "w") as file_reader:
            json.dump(self.data, file_reader, indent=4)

    def create_binding_arrows(self, start: primitives.ExcaliDrawPrimitive, end: primitives.ExcaliDrawPrimitive,
                              arrow = None, padding:int=10, **kwargs):
        """
        Create a binding arrow between two elements.
        :param start: primitives.ExcaliDrawPrimitives
        :param end: primitives.ExcaliDrawPrimitives
        :param arrow: self.Arrow or self.DoubleArrow
        :param padding: defaults to 10
        :param kwargs: passed to arrow
        """

        if arrow is None:
            arrow = self.Arrow

        center_start = start.center
        center_end = end.center
        dx = center_end[0] - center_start[0]
        dy = center_end[1] - center_start[1]
        theta = math.atan2(dy, dx)
        theta = (theta + math.pi) % (2*math.pi) - math.pi
        inverted_theta = theta % (2*math.pi) - math.pi
        start_pt = start.get_edge_midpoint(theta, padding=padding)
        end_pt = end.get_edge_midpoint(inverted_theta, padding=padding)

        line = arrow(start_pt, end_pt, **kwargs)
        line.set_start_binding(start, padding=padding)
        line.set_end_binding(end, padding=padding)

    def create_bounding_element(self, element: primitives.ExcaliDrawPrimitive, function = None, padding = 10, **kwargs):
        """
        Create a bounding box around the given element/group.

        :param element: primitives.ExcaliDrawPrimitives
        :param function: self.Rectangle or similar, defaults to self.Rectangle
        :param padding: defaults to 10
        :param kwargs: passed to arrow
        """

        if function is None:
            function = self.Rectangle

        element_center = element.center
        new_x = element_center[0]
        new_y = element_center[1]

        new_width = element.width + 2 * padding
        new_height = element.height + 2 * padding

        bounding_elem = function(x=new_x, y=new_y, width=new_width, height=new_height, **kwargs)

        group_id = str(uuid.uuid4())
        element.groupIds.append(group_id)
        bounding_elem.groupIds.append(group_id)

        return bounding_elem

    def TextBox(self, text: str, x: int, y: int, txt_kwargs = None, rect_kwargs = None):
        """
        Creates a text box
        :param text: text
        :param x: center x
        :param y: center y
        :param txt_kwargs: other properties for text
        :param rect_kwargs: other properties for rect
        """
        if txt_kwargs is None:
            txt_kwargs = {}
        if rect_kwargs is None:
            rect_kwargs = {}

        txt = self.Text(text, x, y, **txt_kwargs)
        return self.create_bounding_element(txt, self.Rectangle, **rect_kwargs)

