from node import Node

def model1():

    # 三层示例树

    # 第三层叶子节点
    A1a = Node("A1a", score=3)
    A1b = Node("A1b", score=5)
    A2a = Node("A2a", score=6)
    A2b = Node("A2b", score=4)
    B1a = Node("B1a", score=2)
    B1b = Node("B1b", score=1)
    B2a = Node("B2a", score=7)
    B2b = Node("B2b", score=3)

    # 第二层
    A1 = Node("A1", children=[A1a, A1b])
    A2 = Node("A2", children=[A2a, A2b])
    B1 = Node("B1", children=[B1a, B1b])
    B2 = Node("B2", children=[B2a, B2b])

    # 第一层
    A = Node("A", children=[A1, A2])
    B = Node("B", children=[B1, B2])

    # 第零层
    root = Node("root", children=[A, B])

    return root
