#!/usr/bin/env python
# license removed for brevity
import math
import threading
from typing import List
import time
import json
import roslibpy
from simple_pid import PID

from controller import CarController, OpsEnum
from objects import CarInfo, RoadLine


def log(msg):
    print(f"{time.time()} {msg}")


class RosConnection:
    def __init__(self) -> None:
        self.car_controller: threading.Thread
        self.isOpen = False
        self.service: roslibpy.Service
        self.switch_listener: roslibpy.Topic
        self.monitor_listener: roslibpy.Topic
        self.client: roslibpy.Ros
        self.topicClient: roslibpy.Ros
        self.stopped_at_crossing = False  # 车是否在路口停下过
        self.ignore_traffic_light = False
        self.park_stage = 0
        self.allow_car_info = True
        self.time = 0
        self.isInit = False
        self.pid_values = []
        self.throttle_pid = PID(1, 0.1, 0.05, setpoint=6)
        self.steering_pid = PID(0.8, 0.1, 0.2)

    def build_conn(self) -> roslibpy.Ros:
        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.service = roslibpy.Service(
            self.client, '/unity_ops_car_service', 'sim_car_msgs/srv/VehicleControlService')
        self.switch_listener = roslibpy.Topic(
            self.client, '/switch', 'sim_car_msgs/msg/Switch')
        self.switch_listener.subscribe(
            lambda message: self.curStatus(message['is_available']))
        self.monitor_listener = roslibpy.Topic(
            self.client, '/sync_topic', 'sim_car_msgs/msg/CarInfo')
        self.monitor_listener.subscribe(self.monitor_service)
        self.car_controller = CarController(self)
        self.car_controller.daemon = True
        self.car_controller.start()
        return self.client

    def start_conn(self):
        self.client.run_forever()
        pass

    def monitor_service(self, message, ignore=False):
        if not self.allow_car_info and not ignore:
            return
        if time.time() - self.time > 2 and not self.isInit:
            self.isInit = True
            self.car_controller.set_shift("D")
        car_info = CarInfo(message)
        # print(message)
        # print(f"velocity:{car_info.velocity}")
        velocity = self.throttle_pid(car_info.velocity)
        self.pid_values.append([velocity, car_info.velocity])
        # if velocity > 0:
        #     self.car_controller.set_throttle(velocity / 50.0)
        for anotherCar in car_info.perceptive_cars:
            if car_info.can_crash(anotherCar):
                self.car_controller.set_brake()
                break
                # 停走场景
            if 400 > car_info.distance_squared_to(anotherCar) > 300:
                self.car_controller.set_brake()
            if car_info.distance_squared_to(anotherCar) >= 400:
                self.car_controller.set_throttle(0.7)
        # 检测是否有行人
        for anotherPedestrian in car_info.perceptive_pedestrians:
            if car_info.can_crash(anotherPedestrian):
                self.car_controller.set_brake()
                angle1 = car_info.angle_horizontal_to(anotherPedestrian.pos_vector)
                print(f"偏转角度: {angle1}")
            else:
                self.car_controller.set_throttle(1)
                # if angle1>(60/math.pi*180):
                #     self.car_controller.set_throttle(0.6)
                break
        # 是否有限速
        for anotherObstacle in car_info.perceptive_obstacles:
            if anotherObstacle.item_name == "Roadblocks":
                if car_info.distance_squared_to(anotherObstacle) <= 100:
                    self.car_controller.set_brake()
                    self.car_controller.set_blinker(3)
            if car_info.distance_squared_to(anotherObstacle) <= 10000:
                if anotherObstacle.item_name == "RoadSign-ProhibitionSign":
                    # print(car_info.velocity)
                    if car_info.velocity > 8.33:
                        self.car_controller.set_brake(0.1)
                    else:
                        self.car_controller.set_throttle(0.5)  # 油门加速仍有问题
                    break

        # 停车线停止
        for light in car_info.perceptive_traffic_lights:
            if light.item_name == "traffic lights_02_05":
                if car_info.distance_squared_to(light) <= 50:
                    if self.ignore_traffic_light:
                        break
                    if not self.stopped_at_crossing:
                        print("遇到红灯，开始刹车")
                        self.car_controller.set_brake()
                    if car_info.velocity <= 0.1:
                        print("红灯刹停，等待绿灯")
                        self.stopped_at_crossing = True
                    if light.state == "G" and self.stopped_at_crossing:
                        print("绿灯亮，加油门")
                        self.car_controller.set_throttle(0.6)
                        self.stopped_at_crossing = False
                        self.ignore_traffic_light = True
        if car_info.drivepath:
            # print(car_info.drivepath)
            next_point = car_info.get_suitable_point()
            angle = None
            if next_point:
                angle = car_info.angle_horizontal_to(next_point)
            # print(f"当前位置: {car_info.pos_vector} 目标位置: {next_point} 偏转角度: {angle} yaw: {car_info.rot_yaw}")
            if not next_point:
                print("未找到下个合适的目标位置")
                return
            if math.fabs(angle) < 5:
                return
            self.steering_pid.setpoint = angle
            angle = self.steering_pid(0)
            print(f"rot_yaw: {car_info.rot_yaw} setpoint: {self.steering_pid.setpoint} pid feedback: {angle}")

            angle *= 0.60  # 0.75
            angle = angle / 45.0
            if angle > 1.0:
                angle = 1.0
            elif angle < -1.0:
                angle = -1.0
            # self.car_controller.set_blinker()
            self.car_controller.set_steering(angle)
            self.car_controller.set_blinker(2 if angle > 0 else 1)

        # if car_info.velocity > 9:
        #     self.car_controller.set_brake(1)
        if car_info.velocity < 5:
            self.car_controller.set_throttle(0.6)

        # print(f"yaw: {car_info.rot_yaw},pitch: {car_info.rot_pitch}, roll:{car_info.rot_roll}")

        # 倒库
        # parkingLot = car_info.perceptive_parkinglot
        # distDiff = parkingLot.pos_vector - car_info.pos_vector
        # print(distDiff)
        # print(car_info.velocity)
        # if distDiff.y > -5 and self.park_stage == 0:
        #     self.car_controller.set_brake()
        #     self.park_stage += 1
        # if car_info.velocity <= 0.1 and self.park_stage == 1:
        #     self.car_controller.set_steering(1)

    def curStatus(self, msg):
        self.isOpen = msg
        log(self.isOpen)
        if self.isOpen:
            self.time = time.time()
            self.isInit = False
            self.car_controller.reload()
            log("收到连接，开始启动")
        else:
            pass
            # print(self.pid_values)
            # print("开始绘图")
            # if self.pid_values:
            #     import matplotlib.pyplot as plt
            #     x_axis = []
            #     speed_axis = []
            #     pid_axis = []
            #     for idx, entry in enumerate(self.pid_values):
            #         pid_axis.append(entry[0])
            #         speed_axis.append(entry[1])
            #         x_axis.append(idx)
            #     plt.plot(x_axis, speed_axis, "r", label="velocity")
            #     plt.plot(x_axis, pid_axis, "b", label="pid feedback")
            #     plt.legend()
            #     plt.title("setpoint: {}".format(self.throttle_pid.setpoint))
            #     plt.show()

    def send_request(self, opss: List[str]):
        carName = "EgoVehicle"
        jsonArr = json.dumps(opss)
        log('Request: ' + jsonArr)
        request = roslibpy.ServiceRequest(
            dict(input=dict(car_name=carName, opss=jsonArr)))
        try:
            if (self.isOpen):
                self.allow_car_info = False
                respond = self.service.call(request, timeout=1)
                if respond:
                    print(
                        f"车辆油门: {respond['car_info']['throttle']} 速度: {respond['car_info']['velocity']} 刹车:{respond['car_info']['brake']} 挡位:{respond['car_info']['shift']}")
                if (len(respond["error_message"])):
                    print('Service response: ', respond["error_message"])
                else:
                    self.monitor_service(respond["car_info"], True)
                self.allow_car_info = True
        except Exception as err:
            print("err is:" + str(err))


class Main:
    def __init__(self):
        ros = RosConnection()
        ros.build_conn()
        ros.start_conn()


if __name__ == '__main__':
    mainClass = Main()
