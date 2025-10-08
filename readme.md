# Xiangqi: A Modern Chinese Chess Engine
## A powerful Xiangqi AI for developers and enthusiasts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Keywords**: Chinese Chess, Xiangqi, Chess Engine, AI, Artificial Intelligence, NegaMax, Alpha-Beta Pruning, Zobrist Hashing, Transposition Table, Game AI, Board Game, Python

---

### English

**Xiangqi** is a modern Chinese Chess (Xiangqi) engine built from the ground up as a learning and research project. It began as a simple implementation of the NegaMax search algorithm and has since evolved to incorporate a wide range of advanced techniques found in state-of-the-art chess engines.

This project serves not only as a capable Xiangqi AI but also as an excellent educational resource, demonstrating the complete journey of building a chess AI from basic algorithms to sophisticated optimizations.

### 简体中文

**Xiangqi (迷你象棋)** 是一个从零开始、逐步构建的现代化中国象棋引擎。项目最初旨在学习和实践 NegaMax 搜索算法，随着研究的深入，我们不断融入多种现代象棋引擎的核心技术，使其具备了完善的对弈能力与精准的评估体系。

该项目不仅是一个功能强大的象棋 AI，也是一个绝佳的学习资源，清晰地展示了棋类 AI 从基础算法到高级优化的完整实现过程。

---

## Core Technologies & Features (核心技术与特性)

The engine implements a comprehensive suite of technologies that form the backbone of modern chess programs.

| Feature | Description (English) | 描述 (中文) |
| :--- | :--- | :--- |
| **Search Algorithm** | **NegaMax with Alpha-Beta Pruning**: A highly efficient search algorithm that minimizes the number of nodes to be evaluated in the search tree. | **NegaMax 搜索与 Alpha-Beta 剪枝**: 高效的搜索算法，通过剪枝极大减少需要评估的节点数量。 |
| **Search Extensions** | **Quiescence Search**: Extends the search for captures after reaching the nominal depth, mitigating the "horizon effect" and stabilizing evaluations. | **静态搜索**: 在达到预设深度后继续扩展吃子着法，直至局面稳定，有效缓解“地平线效应”。 |
| **Search Enhancements** | **Iterative Deepening Search (IDS)**: A standard practice in modern engines that searches layer by layer, starting from depth 1, allowing for effective time management. | **迭代深化搜索**: 从深度 1 开始逐层加深搜索，是现代引擎的标准实现，便于时间控制。 |
| **Search Optimizations** | **Null Move Pruning**: A technique that prunes branches of the search tree by assuming the opponent makes a "null move" (passes their turn), which can quickly identify positions that are much worse than expected. | **空着裁剪**: 一种通过假设对手进行“空着”（跳过回合）来修剪搜索树分支的技术，可以快速识别比预期差得多的局面。 |
| **Transposition Table**| **Zobrist Hashing & Transposition Table**: Uses Zobrist keys to store previously evaluated positions, avoiding redundant calculations and enabling faster search. | **Zobrist 哈希与置换表**: 使用 Zobrist 键存储已评估过的局面，避免重复计算，显著提升搜索效率。 |
| **Move Ordering** | **Advanced Move Ordering**: Prioritizes moves from the transposition table (hash move), capture moves (MVV-LVA), and quiet moves with high scores from the **History Heuristic**, leading to more frequent and deeper alpha-beta cutoffs. | **高效着法排序**: 优先考虑置换表中的历史最佳着法、吃子着法 (MVV-LVA) 以及**历史启发**分数高的静默着法，实现更频繁、更深度的剪枝。 |
| **Repetition Detection**| **Repetition Prevention & Detection**: Utilizes a history of Zobrist hashes to detect repeated positions and enforce draw rules, preventing infinite loops. | **循环检测与防止**: 利用哈希历史判定重复局面，并赋予和棋结果，避免无限循环。 |
| **Opening Book** | **Opening Book**: Utilizes a pre-computed `opening_book.json` to play standard openings, ensuring a strong start. | **开局库**: 在开局阶段直接检索 `opening_book.json` 中的预设着法，保证开局质量。 |
| **Evaluation** | **Tapered Evaluation with PST**: Employs two sets of Piece-Square Tables (PST) for middlegame and endgame. The evaluation dynamically blends these tables based on the game phase, creating a more nuanced understanding of piece values. | **渐进式评估与棋子位置表 (PST)**: 采用中局 (PST_MG) 与残局 (PST_EG) 两套位置表，根据场上子力动态混合评估结果，实现更精确的“棋感”。 |
| **Evaluation Features**| **Mobility & King Safety**: The evaluation function considers piece mobility (number of legal moves) and king safety (detecting attacks around the palace), leading to more human-like strategic decisions. | **机动性与将/帅安全评估**: 评估函数包含对棋子活跃度（合法移动步数）和将/帅安全性（检测九宫格内的受攻击情况）的考量，使决策更具战略性。 |
| **Performance** | **Piece-List Optimization**: Maintains a list of piece positions for each player, avoiding full-board scans during move generation and evaluation, which significantly boosts performance. | **棋子列表优化**: 维护玩家棋子位置列表，在评估与走法生成中避免全盘扫描，大幅提升性能。 |
| **Board Representation** | **Bitboard**: Utilizes Python's arbitrary-precision integers to represent the 90-square Xiangqi board, enabling highly efficient and fast bitwise operations for move generation and board manipulation. This approach extends beyond standard 64-bit integers to accommodate the larger board size. | **位棋盘**: 利用 Python 的任意精度整数来表示 90 格的中国象棋棋盘状态，实现高效快速的位运算，用于走法生成和棋盘操作。这种方法超越了标准的 64 位整数，以适应更大的棋盘尺寸。 |
| **Time Management** | **Basic Time Management**: Periodically checks the elapsed time during the search process to ensure it returns the best move within the allocated time limit. | **基本时间管理**: 在搜索过程中周期性检查时间，确保在限定时间内返回最佳着法。 |

---

## Project Structure (项目结构)

The project is organized into two main parts: the core engine source code and external dependencies managed as Git submodules.

- **`/src`**: Contains all the Python source code for the Xiangqi engine itself, including search algorithms, evaluation functions, and board representation.
- **`/scripts`**: Includes utility scripts, such as `create_opening_book.py`, which processes data to generate the engine's opening book.
- **`/external/xq_data`**: A Git submodule containing a large community-maintained database of Xiangqi game records. This data is used by the `create_opening_book.py` script to build a comprehensive opening library for the engine.

---

## Getting Started (如何开始)

1.  **Clone the repository & submodules:**
    ```bash
    git clone --recursive https://github.com/hezhaoyun/minixiangqi.git
    cd minixiangqi
    ```

2.  **Create Opening Book:**
    ```bash
    python -m scripts.create_opening_book
    ```
3.  **Run the game with a sample GUI (R: Restart, U: Undo):**
    ```bash
    python -m src.main
    ```

---

## Contributing (贡献)

We welcome contributions from the community! Whether you want to fix a bug, add a new feature, or improve the documentation, please feel free to open an issue or submit a pull request.

欢迎社区的贡献！无论是修复 Bug、添加新功能还是改进文档，都欢迎您提交 Issue 或 Pull Request。

---

## License (许可)

This project is licensed under the MIT License.

该项目采用 MIT 许可协议。