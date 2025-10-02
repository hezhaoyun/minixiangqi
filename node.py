# 节点类
class Node:
    def __init__(self, name, children=None, score=None):
        """
        name: 节点名字
        children: 子节点列表
        score: 叶子节点的分数（如果是None表示非叶子节点）
        """
        self.name = name
        self.children = children or []
        self.score = score

    def is_leaf(self):
        return self.score is not None
