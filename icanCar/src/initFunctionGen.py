class Inst:
    item_name = None
    velocity = None
    acceleration = None
    size_width = None
    size_length = None
    size_heigth = None
    RosMessageName = None


for line in Inst.__dict__:
    print(f"self.{line} = obj.get(\"{line}\")")
