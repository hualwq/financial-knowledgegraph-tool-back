import pandas as pd
import networkx as nx
import random

# 读取 Excel 文件并构建无向图
file_path = r"D:\建信金科数据集\参数\汇总小编号量化参数.xlsx"  # 替换为实际文件路径
data = pd.read_excel(file_path)

# 构建图
G = nx.Graph()
edges = list(zip(data['GuarantorID'], data['GuaranteeID']))
G.add_edges_from(edges)

# 参数设置
beta = 0.9   # 感染率
gamma = 0.2  # 恢复率
alpha = 0.1  # 免疫丧失率
max_infected_limit = 1000  # 最大感染节点数限制

# 初始化节点状态 (S, I, R)
states = {node: 'S' for node in G.nodes}
initial_infected = [688086]  # 替换为初始感染点编号
for node in initial_infected:
    states[node] = 'I'  # 初始感染点设为感染状态

# 模拟传播过程
def simulate_sirs_until_stable_or_limit(graph, states, beta, gamma, alpha, max_infected_limit):
    time_series = {}
    all_infected_nodes = set()  # 记录整个过程中感染的节点
    previous_infected_nodes = set()  # 记录上一时间步的感染节点
    t = 0

    time_series[t] = list(states.items())  # 初始状态

    while True:
        new_states = states.copy()
        current_infected_nodes = set()  # 当前时间步的感染节点

        for node in graph.nodes:
            if states[node] == 'S':
                # 易感者可能被感染
                infected_neighbors = [n for n in graph.neighbors(node) if states[n] == 'I']

                # 计算 beta_i
                beta_i = 0
                for neighbor in infected_neighbors:
                    # 找到对应的边
                    edge_data = data[
                        ((data['GuarantorID'] == neighbor) & (data['GuaranteeID'] == node)) |
                        ((data['GuarantorID'] == node) & (data['GuaranteeID'] == neighbor))
                        ]
                    if not edge_data.empty:
                        amount_num = edge_data['AmountNum'].iloc[0]
                        risk_probability = edge_data['Risk_Probability'].iloc[0]
                        beta_i += (amount_num * 0.5 + risk_probability * 0.5) * beta

                if beta_i>1:
                    beta_i=1
                if infected_neighbors and random.random() < 1 - (1 - beta_i) ** len(infected_neighbors):
                    new_states[node] = 'I'
                    all_infected_nodes.add(node)
                    current_infected_nodes.add(node)
            elif states[node] == 'I':
                # 感染者可能恢复
                current_infected_nodes.add(node)  # 感染状态持续的节点
                if random.random() < gamma:
                    new_states[node] = 'R'
            elif states[node] == 'R':
                # 恢复者可能再次变成易感者
                if random.random() < alpha:
                    new_states[node] = 'S'

        # 检查终止条件：当前感染者与上一时间步相同且状态无变化，或超过最大感染节点数
        if new_states == states and current_infected_nodes == previous_infected_nodes:
            break
        if len(all_infected_nodes) > max_infected_limit:
            print("Simulation stopped: Infected nodes exceeded the limit.")
            break

        previous_infected_nodes = current_infected_nodes  # 更新上一时间步感染节点
        states = new_states  # 更新状态
        t += 1
        time_series[t] = list(states.items())  # 记录当前时间步的状态

    return time_series, all_infected_nodes

# 运行模拟
infection_result, all_infected_nodes = simulate_sirs_until_stable_or_limit(
    G, states, beta, gamma, alpha, max_infected_limit
)

# 输出结果
for time, state_list in infection_result.items():
    infected_nodes = [node for node, state in state_list if state == 'I']
    print(f"Time {time}: Infected nodes = {infected_nodes}")

# 输出总共被感染的节点数
print(f"Total number of nodes infected during the process: {len(all_infected_nodes)}")
