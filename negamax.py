import math

from model import *


# Negamax + α-β剪枝实现
def negamax(node, alpha, beta, depth=0):
    """
    使用 Negamax 算法结合 Alpha-Beta 剪枝来搜索最佳着法和分数.

    参数:
    node (Node): 当前节点.
    alpha (float): Alpha值 (当前玩家能确保的最好分数).
    beta (float): Beta值 (对手能确保的最好分数).
    depth (int): 当前搜索深度.

    返回:
    tuple: (最佳分数, 最佳着法).
    """
    indent = "  " * depth
    print(f"{indent}进入节点 {node.name}, depth={depth}, alpha={alpha}, beta={beta}")

    # 1. 到达叶子节点(递归终点), 返回局面评估分数.
    if node.is_leaf():
        # 根据深度奇偶性, 将分数转换成相对于根节点玩家的视角.
        # 偶数深度(我方回合)分数不变, 奇数深度(对方回合)分数取反.
        perspective_multiplier = 1 if depth % 2 == 0 else -1
        score = node.score * perspective_multiplier
        print(f"{indent}-> 叶子节点 {node.name}, 原始分={node.score}, 调整后得分={score}")
        return score, None

    # 2. 初始化最佳分数和最佳着法.
    best_value = -math.inf
    best_move = None
    print(f"{indent}初始化 best_value = -inf, best_move = None")

    # 3. 遍历所有子节点 (即所有可能的着法).
    for child in node.children:
        print(f"{indent}- 探索子节点: {child.name}")
        # 递归调用negamax, 注意参数的变化:
        # - 交换alpha和beta, 并都取反.
        # - 深度+1.
        child_value, _ = negamax(child, -beta, -alpha, depth + 1)

        # 从子节点返回的是"对手"的分数, 需要取反转换成"我方"的分数.
        current_score = -child_value
        print(f"{indent}  子节点 {child.name} 的返回分(对手角度)={child_value}, 取反后(我方角度)={current_score}")

        # 4. 如果当前分数更好, 则更新最佳分数和最佳着法.
        if current_score > best_value:
            print(f"{indent}  更新! {current_score} > {best_value}. 新 best_value={current_score}, best_move={child.name}")
            best_value = current_score
            best_move = child
        else:
            print(f"{indent}  不更新. {current_score} <= {best_value}")

        # 5. 更新alpha值 (我方能保证的最低分数).
        old_alpha = alpha
        alpha = max(alpha, best_value)
        if alpha != old_alpha:
            print(f"{indent}  更新 alpha: max({old_alpha}, {best_value}) -> {alpha}")

        # 6. Alpha-Beta 剪枝.
        # 如果alpha >= beta, 说明这个分支不会比已经找到的其他分支更优, 可以剪掉.
        if alpha >= beta:
            print(f"{indent}  !!剪枝!! alpha ({alpha}) >= beta ({beta}). 停止探索 {node.name} 的其他子节点.")
            break  # 剪枝

    print(f"{indent}节点 {node.name} 返回 best_value={best_value}, best_move={best_move.name if best_move else 'None'}")
    return best_value, best_move


def search(root):
    print("="*20 + " 开始搜索 " + "="*20)
    final_score, best_move = negamax(root, -math.inf, math.inf, depth=0)
    print("="*20 + " 搜索结束 " + "="*20)
    print(f"\n最终评估分数 (从我方角度): {final_score}")
    if best_move:
        print(f"最佳着法是: {best_move.name}")


if __name__ == "__main__":
    search(models()[0])
