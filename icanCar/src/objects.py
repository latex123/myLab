import json
import math
from typing import Optional, List

from util.Vector3 import Vector3

bypassList = ["pos_vector", "zebra_crossings"]


class PilotObject:
    def __init__(self):
        pass


class Position(PilotObject):
    pos_x = None
    pos_y = None
    pos_z = None
    rot_pitch = None
    rot_yaw = None
    rot_roll = None

    pos_vector = None

    def __init__(self, obj):
        self.pos_x = obj["pos_x"]
        self.pos_y = obj["pos_y"]
        self.pos_z = obj["pos_z"]
        self.rot_pitch = obj["rot_pitch"]
        self.rot_yaw = obj["rot_yaw"]
        self.rot_roll = obj["rot_roll"]
        self.pos_vector = Vector3(self.pos_x, self.pos_y, self.pos_z)

    def angle_horizontal_to(self, other):
        # type: (Vector3)->float
        d_x = other.x - self.pos_x
        if d_x == 0 or d_x == 0.0:
            d_x += 0.00001
        d_y = other.y - self.pos_y
        a = (math.atan(d_y * 1.0 / d_x) / math.pi * 180)
        if d_x > 0 and d_y > 0:
            a = -a  # a=a
            # a1=a
            # print(f"a1:{a1}")
        elif d_x < 0 and d_y < 0:
            a = 180 - a
            # a2=a
            # print(f"a2:{a2}")
        elif d_x < 0 and d_y > 0:
            a = -180 - a
            # a3=a
            # print(f"a3:{a3}")
        else:
            a = -a
            # a4=a
            # print(f"a4:{a4}")
        delta = -self.rot_yaw + a
        return delta
        # if d_y == 0 or d_y == 0.0:
        #     d_y += 0.01
        # theta = (math.atan(d_x * 1.0 / d_y) / math.pi * 180)
        # delta = self.rot_yaw - 90 - theta
        # if theta > 0:
        #     delta = theta + self.rot_yaw - 90
        # else:
        #     delta = theta - self.rot_yaw + 90

        # if self.rot_yaw <= 90:
        #     delta =  math.pi /2 - theta - self.rot_yaw
        # else:
        #     delta =  theta + self.rot_yaw - math.pi /2
        # return delta

    def distance_squared_to(self, other):
        return self.pos_vector.distance_squared_to(other.pos_vector)

    def can_crash(self, anotherPos):
        # type: (Position)->bool
        # print(self.__pos_vector.distance_squared_to(anotherPos.__pos_vector))
        return self.pos_vector.distance_squared_to(anotherPos.pos_vector) <= 73.0


class CarInfo(Position):
    item_name = None
    velocity = None
    acceleration = None
    steering = None
    wheel_angle = None
    throttle = None
    brake = None
    perceptive_cars = None  # type: List[PerceptiveObjectInfo]
    perceptive_bicycles = None
    perceptive_obstacles = None
    perceptive_traffic_lights = None
    perceptive_pedestrians = None
    drivepath = None  # type: Optional [str,List[Vector3]]
    timestamp = None
    shift = None
    main_light = None
    blinker = None
    horn = None
    latitude = None
    longitude = None
    perceptive_parkinglot = None
    perceptive_roadlines = None
    zebra_crossings = None

    def __init__(self, obj):
        super().__init__(obj)
        self.item_name = obj.get("item_name")
        self.velocity = obj.get("velocity")
        self.acceleration = obj.get("acceleration")
        self.steering = obj.get("steering")
        self.wheel_angle = obj.get("wheel_angle")
        self.throttle = obj.get("throttle")
        self.brake = obj.get("brake")
        self.perceptive_cars = obj.get("perceptive_cars")
        self.perceptive_bicycles = obj.get("perceptive_bicycles")
        self.perceptive_obstacles = obj.get("perceptive_obstacles")
        self.perceptive_traffic_lights = obj.get("perceptive_traffic_lights")
        self.perceptive_pedestrians = obj.get("perceptive_pedestrians")
        self.drivepath = obj.get("drivepath")
        self.timestamp = obj.get("timestamp")
        self.shift = obj.get("shift")
        self.main_light = obj.get("main_light")
        self.left_blinker = obj.get("left_blinker")
        self.horn = obj.get("horn")
        self.latitude = obj.get("latitude")
        self.longitude = obj.get("longitude")
        self.perceptive_parkinglot = obj.get("perceptive_parkinglot")
        self.perceptive_roadlines = obj.get("perceptive_roadlines")
        self.zebra_crossings = obj.get("zebra_crossings")
        self.__post_construct()

    def get_suitable_point(self):
        distList = {idx: (self.angle_horizontal_to(point), self.pos_vector.distance_squared_to(point)) for idx, point in
                    enumerate(self.drivepath)}
        min = 1000000000
        Max = -1
        minIdx = None
        MaxIdx = None
        maxDist = max([x[1] for x in distList.values()])
        for index, entry in distList.items():
            angle = entry[0]
            distSqr = entry[1]
            if math.fabs(angle) > 90:  # 90
                continue
            if maxDist <= 25:  # 25
                if Max < distSqr:
                    Max = distSqr
                    MaxIdx = index

            else:
                if min > distSqr > 25:  # 25
                    min = distSqr
                    minIdx = index
        # print(MaxIdx, minIdx)
        if maxDist <= 25:  # 25
            return self.drivepath[MaxIdx] if MaxIdx is not None else None
        return self.drivepath[minIdx] if minIdx is not None else None

    def __post_construct(self):
        cars = []
        for car in json.loads(self.perceptive_cars):
            cars.append(PerceptiveObjectInfo(car))
        self.perceptive_cars = cars
        pedestrians = []
        for pedestrian in json.loads(self.perceptive_pedestrians):
            pedestrians.append(PerceptiveObjectInfo(pedestrian))
        self.perceptive_pedestrians = pedestrians
        obstacles = []
        for obstacle in json.loads(self.perceptive_obstacles):
            obstacles.append(PerceptiveObjectInfo(obstacle))
        self.perceptive_obstacles = obstacles
        trafficLights = []
        for light in json.loads(self.perceptive_traffic_lights):
            trafficLights.append(PerceptiveTrafficLight(light))
        self.perceptive_traffic_lights = trafficLights
        self.perceptive_parkinglot = PerceptiveParkingLot(
            json.loads(self.perceptive_parkinglot))
        drive_points = []
        for point in json.loads(self.drivepath):
            drive_points.append(Vector3(point["x"], point["y"], point["z"]))
        self.drivepath = drive_points

        if self.perceptive_roadlines:
            roadlines = []
            for perceptive_roadlines in json.loads(self.perceptive_roadlines):
                roadlines.append(RoadLine(perceptive_roadlines))
            self.perceptive_roadlines = roadlines

        # if self.perceptive_roadlines:
        #     roadlines = []
        #     zebras = set()
        #     for perceptive_roadlines in json.loads(self.perceptive_roadlines):
        #         roadlines.append(RoadLine(perceptive_roadlines))
        #         if perceptive_roadlines["type"] == "ZebraCrossing":
        #             zebras.add(ZebraCrossing(perceptive_roadlines["pointpath"]))
        #     self.perceptive_roadlines = roadlines
        #     self.zebra_crossings = zebras


class PerceptiveObjectInfo(Position):
    item_name = None
    velocity = None
    acceleration = None
    size_width = None
    size_length = None
    size_heigth = None

    def __init__(self, obj):
        Position.__init__(self, obj)
        self.item_name = obj.get("item_name")
        self.velocity = obj.get("velocity")
        self.acceleration = obj.get("acceleration")
        self.size_width = obj.get("size_width")
        self.size_length = obj.get("size_length")
        self.size_heigth = obj.get("size_heigth")
        self.RosMessageName = obj.get("RosMessageName")


class PerceptiveTrafficLight(Position):
    item_name = None
    instance_id = None
    state = None
    type = None

    def __init__(self, obj):
        Position.__init__(self, obj)
        self.item_name = obj.get("item_name")
        self.instance_id=obj.get("instance_id")
        self.state=obj.get("state")
        self.type=obj.get("type")


class RoadLine:
    type = None
    pointpath = None

    def __init__(self, obj):
        self.type = obj.get("type")
        self.pointpath = []
        for point in json.loads(obj.get("pointpath")):
            self.pointpath.append(Vector3(point["x"], point["y"], point["z"]))


class PerceptiveParkingLot(Position):
    size_width = None
    size_length = None
    def __init__(self, obj):
        Position.__init__(self, obj)
        self.size_width= obj.get("size_width")
        self.size_length=obj.get("size_length")


class ZebraCrossing():
    minX = None
    minY = None
    maxX = None
    maxY = None

    def __init__(self, point_path):
        xList = []
        yList = []
        for point in json.loads(point_path):
            xList.append(point["x"])
            yList.append(point["y"])
        self.minX = round(min(xList), 2)
        self.maxX = round(max(xList), 2)
        self.minY = round(min(yList), 2)
        self.maxY = round(max(yList), 2)

    def is_in(self, vector3: Vector3):
        return self.minX <= vector3.x <= self.maxX and self.minY <= vector3.y <= self.maxY
