from node import Node

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


# 四层示例树

# 第四层叶子节点
N40 = Node("N40", score=60)
N41 = Node("N41", score=63)
N42 = Node("N42", score=15)
N43 = Node("N43", score=58)
N44 = Node("N44", score=81)
N45 = Node("N45", score=74)
N46 = Node("N46", score=88)
N47 = Node("N47", score=15)
N48 = Node("N48", score=20)
N49 = Node("N49", score=92)
N4A = Node("N4A", score=9)
N4B = Node("N4B", score=62)
N4C = Node("N4C", score=82)
N4D = Node("N4D", score=89)
N4E = Node("N4E", score=54)
N4F = Node("N4F", score=17)

# 第三层
N30 = Node("N30", children=[N40, N41])
N31 = Node("N31", children=[N42, N43])
N32 = Node("N32", children=[N44, N45])
N33 = Node("N33", children=[N46, N47])
N34 = Node("N34", children=[N48, N49])
N35 = Node("N35", children=[N4A, N4B])
N36 = Node("N36", children=[N4C, N4D])
N37 = Node("N37", children=[N4E, N4F])

# 第二层
N20 = Node("N20", children=[N30, N31])
N21 = Node("N21", children=[N32, N33])
N22 = Node("N22", children=[N34, N35])
N23 = Node("N23", children=[N36, N37])

# 第一层
N10 = Node("N10", children=[N20, N21])
N11 = Node("N11", children=[N22, N23])

# 第零层
N00 = Node("N00", children=[N10, N11])


def models():
    return root, N00, N10, N11
