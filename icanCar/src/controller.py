import json
import queue
import time
from threading import Thread


class OpsEnum:
    """用ros的方式构造控制指令

    输入ops_name、操作名、操作数值，输出一个json字符串

    """
    Throttle = "Throttle"
    Brake = "Brake"
    Shift = "Shift"
    Steering = "Steering"
    Blinker = "Blinker"
    Horn = "Horn"

    def __init__(self, ops_name, value=None):
        self.ops_name = ops_name
        self.value = value

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        result = {"OpsName": self.ops_name}
        if self.value is not None:
            result["value"] = self.value
        return json.dumps(result)


class CarController(Thread):
    """
    车的控制器
    """

    throttle_state = 1  # 油门状态: 0刹车 1油门
    throttle_value = 1  # 油门值
    steering_value = 0
    shift_state = "N"
    last_throttle_time = 0
    blinker_value = 0
    horn_value = None

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.ops_queue = queue.Queue()
        self.reload()
        print("控制器 初始化完成")

    def reload(self):
        self.ops_queue.empty()
        self.throttle_state = 1  # 油门状态: 0刹车 1油
        self.throttle_value = 1  # 油门值
        self.steering_value = 0
        self.shift_state = "N"
        self.last_throttle_time = 0
        self.blinker_value = 0
        self.horn_value = 0

    def run(self) -> None:
        while True:
            time.sleep(0.0001)
            if not self.conn.isOpen:
                continue
            while not self.ops_queue.empty():
                opss = self.ops_queue.get()
                self.conn.send_request([str(x) for x in opss])

    def set_brake(self, value=1):
        # print("准备刹车")
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        if self.throttle_state == 0 and self.throttle_value == value:
            return

        if self.shift_state == "N":
            return
        self.throttle_state = 0
        self.throttle_value = value
        self.ops_queue.put([OpsEnum(OpsEnum.Throttle, 0),
                            OpsEnum(OpsEnum.Brake, value)])

    def set_throttle(self, value=1):
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        # if self.throttle_state == 1 and self.throttle_value == value:
        #     return
        if time.time() - self.last_throttle_time <= 1.0:
            return
        if self.shift_state == "N":
            return
        self.throttle_state = 1
        self.throttle_value = value
        self.last_throttle_time = time.time()
        self.ops_queue.put(
            [OpsEnum(OpsEnum.Shift, "D"), OpsEnum(OpsEnum.Brake, 0), OpsEnum(OpsEnum.Throttle, value)])

    def set_steering(self, value=0):
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        if self.steering_value == value:
            return
        self.steering_value = value
        self.ops_queue.put([OpsEnum(OpsEnum.Steering, value)])

    def set_shift(self, shift="N"):
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        if self.shift_state == shift:
            return
        self.shift_state = shift
        print(f"挂{shift}挡")
        self.ops_queue.put([OpsEnum(OpsEnum.Shift, shift)])

    def set_blinker(self, value=0):
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        if self.blinker_value == value:
            return
        self.blinker_value = value
        self.ops_queue.put([OpsEnum(OpsEnum.Blinker, value)])

    def set_horn(self, value=0):
        if not self.conn.isOpen:
            print("连接未初始化，操作被屏蔽")
            return
        if self.horn_value == value:
            return
        self.horn_value = value
        self.ops_queue.put([OpsEnum(OpsEnum.Horn, value)])
