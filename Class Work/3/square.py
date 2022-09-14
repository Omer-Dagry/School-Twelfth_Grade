"""
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 14/09/2022 (day/month/year)
"""
import os
from typing import *
if "rectangle.py" and "shape.py" in os.listdir():
    from rectangle import Rectangle
    from shape import Shape
else:
    raise AssertionError("Missing Files: " + ", ".join([missing_file for missing_file in
                                                        ["rectangle.py", "shape.py"]
                                                        if missing_file not in os.listdir()]))


class Square(Shape):
    def __init__(self, rib_length: Union[int, float]):
        """ Initialize The Square """
        super().__init__()
        self.rib_length = rib_length
        self.set_area(self.rib_length ** 2)
        self.set_perimeter(self.rib_length * 4)

    def set_rib_length(self, rib_length: Union[int, float]):
        """ Set The Square Rib Length """
        self.rib_length = rib_length
        self.set_area(self.rib_length ** 2)
        self.set_perimeter(self.rib_length * 4)

    def get_rib_length(self) -> Union[int, float]:
        """ Get The Square Rib Length """
        return self.rib_length

    def connect_to_rectangle(self, rectangle):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The rectangle + This Square Area And Perimeter
        :type rectangle: Square
        """
        total_area = self.area + rectangle.get_perimeter()
        total_perimeter = self.perimeter + rectangle.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            if width != length:
                return Rectangle(width=width, length=length)
            else:
                return Square(width)
        else:
            return None

    def connect_to_square(self, square):
        """
        Creates A New Rectangle The Has The Same Area And Perimeter As The square + This Square Area And Perimeter
        :type square: Square
        """
        total_area = self.area + square.get_perimeter()
        total_perimeter = self.perimeter + square.get_perimeter()
        length_options = super().solve_quadratic_equation(1, -total_perimeter / 2, total_area)
        if length_options:
            length = length_options[0]
            width = total_area / length
            if width != length:
                return Rectangle(width=width, length=length)
            else:
                return Square(width)
        else:
            return None
