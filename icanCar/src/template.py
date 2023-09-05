#!/usr/bin/env python
# license removed for brevity
from socket import timeout
import time
import sys
from threading import Thread
from typing import List
import roslibpy
import json
from pynput import keyboard


class RosConnection:

    def __init__(self, opss) -> None:
        self.control_thread: ControlThread = None
        self.isOpen = False
        self.opss = opss
        self.service: roslibpy.Service
        self.client: roslibpy.Ros
        self.topicClient: roslibpy.Ros

    def build_conn(self) -> roslibpy.Ros:
        self.client = roslibpy.Ros(host='localhost', port=9090)
        self.service = roslibpy.Service(self.client, '/unity_ops_car_service', 'sim_car_msgs/srv/VehicleControlService')
        self.listener = roslibpy.Topic(self.client, '/switch', 'sim_car_msgs/msg/Switch')
        self.listener.subscribe(lambda message: self.curStatus(message['is_available']))
        self.control_thread = ControlThread(self, self.opss)
        return self.client

    def start_conn(self):
        self.client.run_forever()

    def curStatus(self, msg):
        self.isOpen = msg
        print(self.isOpen)
        if self.isOpen:
            print("收到连接，开始启动")
            self.connect_suc_callback()

    def send_request(self, opss: List[str]):
        carName = "EgoVehicle"
        jsonArr = json.dumps(opss)
        print('Request: ' + jsonArr)
        request = roslibpy.ServiceRequest(dict(input=dict(car_name=carName, opss=jsonArr)))
        try:
            if (self.isOpen):
                respond = self.service.call(request, timeout=1)
                print(respond)
                if (len(respond["error_message"])):
                    print('Service response: ', respond["error_message"])
                else:
                    print('Service response: ', respond["car_info"])
        except Exception as err:
            print("err is:" + str(err))

    def connect_suc_callback(self):
        self.control_thread.start()


class ControlThread(Thread):
    def __init__(self, conn, operates):
        super().__init__()
        self.conn: RosConnection = conn
        self.operates = operates
        self.currentIdx = 0

    def run(self):
        while self.currentIdx < len(self.operates):
            operate = self.operates[self.currentIdx]
            if not operate.startswith("{"):
                print(f"执行指令睡眠: {operate}")
                time.sleep(float(operate))
                self.currentIdx += 1
                continue
            self.conn.send_request([operate])
            print(f"执行指令: {operate}")
            self.currentIdx += 1


def main():
    # client = roslibpy.Ros(host='localhost', port=9090)
    # service = roslibpy.Service(client, '/unity_ops_car_service', 'sim_car_msgs/srv/VehicleControlService')
    # conn =Conn(service)
    # client.on_ready(lambda: conn.call_service(service,client))
    # client.run_forever()
    # print(client.is_connected)
    ros = RosConnection([
        "{\"OpsName\":\"Steering\",\"value\":1}",
        "1",
        "{\"OpsName\":\"Steering\",\"value\":-1}",
        "2",
        "{\"OpsName\":\"Brake\",\"value\":1}"
    ])
    ros.build_conn()
    ros.start_conn()
    # ros.build_listener()


if __name__ == '__main__':
    main()
