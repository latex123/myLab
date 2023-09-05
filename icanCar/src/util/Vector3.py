import math
from math import sqrt


class Vector3(object):
    x: float
    y: float
    z: float

    def __init__(self, x, y, z):
        self.x = round(x, 2)
        self.y = round(y, 2)
        self.z = round(z, 2)

    @staticmethod
    def up():
        return Vector3(0, 1, 0)

    @staticmethod
    def forward():
        return Vector3(0, 0, 1)

    @staticmethod
    def right():
        return Vector3(1, 0, 0)

    @staticmethod
    def add(a, b):
        return Vector3(a.x + b.x, a.y + b.y, a.z + b.z)

    @staticmethod
    def sub(a, b):
        return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)

    @staticmethod
    def dot(a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z

    @staticmethod
    def cross(a, b):
        return Vector3(a.y * b.z - b.y * a.z, -a.x * b.z + b.x * a.z, a.x * b.y - b.x * a.y)

    def __str__(self):
        return f"Vector3({self.x},{self.y},{self.z})"

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        return self.add(self, other)

    def __sub__(self, other):
        return self.sub(self, other)

    def __mul__(self, other):
        return self.dot(self, other)

    def cross_other(self, other):
        return self.cross(self, other)

    def distance_squared_to(self, other):
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2

    def distance_to(self, other):
        return sqrt(self.distance_squared_to(other))

    def length(self):
        return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def angle(self, other):
        dot = self * other / (self.length() * other.length())
        return math.acos(dot)
