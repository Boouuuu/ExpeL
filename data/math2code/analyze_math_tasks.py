# import json
# import matplotlib
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# import numpy as np
# from collections import Counter
# from pathlib import Path
# # 设置中文字体（根据系统选择）
# try:
#     # Windows系统
#     matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
# except:
#     # Mac/Linux系统
#     matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'PingFang SC', 'Heiti SC']
# matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# # ─────────────────────────────────────────────
# # 1. 加载数据
# # ─────────────────────────────────────────────
# # FILE_PATH = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\math2code\math_train_tasks.json"
# FILE_PATH = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\math2code\math_train_tasks_1750.json"
# data = []
# with open(FILE_PATH, "r", encoding="utf-8") as f:
#     # for line in f:
#         # line_data = json.loads(line)  # 每行是一个JSON对象
#         # data.append(line_data)
#     data = json.load(f)  # 整个文件是一个JSON数组


# total = len(data)
# print(f"{'='*50}")
# print(f"  总数据量: {total} 条")
# print(f"{'='*50}")

# # ─────────────────────────────────────────────
# # 2. 统计 level 和 type 分布
# # ─────────────────────────────────────────────
# levels = [item["level"] for item in data]
# types  = [item["type"]  for item in data]

# level_counter = Counter(levels)
# type_counter  = Counter(types)

# # 排序
# level_sorted = dict(sorted(level_counter.items(), key=lambda x: x[0]))
# type_sorted  = dict(sorted(type_counter.items(),  key=lambda x: -x[1]))

# print("\n【Level 分布】")
# for k, v in level_sorted.items():
#     print(f"  {k:10s}: {v:5d}  ({v/total*100:.1f}%)")

# print("\n【Type 分布】")
# for k, v in type_sorted.items():
#     print(f"  {k:20s}: {v:5d}  ({v/total*100:.1f}%)")

# # ─────────────────────────────────────────────
# # 3. 交叉统计 level × type
# # ─────────────────────────────────────────────
# level_names = sorted(set(levels))
# type_names  = list(type_sorted.keys())   # 按频次降序

# cross = np.zeros((len(level_names), len(type_names)), dtype=int)
# for item in data:
#     r = level_names.index(item["level"])
#     c = type_names.index(item["type"])
#     cross[r, c] += 1

# # ─────────────────────────────────────────────
# # 4. 绘图  (2×2 布局 + 热力图)
# # ─────────────────────────────────────────────
# PALETTE_LEVEL = ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B3"]
# PALETTE_TYPE  = [
#     "#4C72B0","#DD8452","#55A868","#C44E52","#8172B3",
#     "#937860","#DA8BC3","#8C8C8C","#CCB974","#64B5CD"
# ]

# fig = plt.figure(figsize=(20, 16))
# fig.patch.set_facecolor("#F8F9FA")

# # ── 标题 ──────────────────────────────────────
# fig.text(0.5, 0.97, "Math Train Tasks — 数据统计分析",
#          ha="center", va="top", fontsize=20, fontweight="bold", color="#2C3E50")
# fig.text(0.5, 0.94, f"总数据量：{total:,} 条",
#          ha="center", va="top", fontsize=13, color="#555555")

# gs = fig.add_gridspec(2, 2, left=0.07, right=0.97,
#                        top=0.91, bottom=0.32,
#                        hspace=0.45, wspace=0.35)

# # ── (1) Level 柱状图 ──────────────────────────
# ax1 = fig.add_subplot(gs[0, 0])
# bars = ax1.bar(list(level_sorted.keys()), list(level_sorted.values()),
#                color=PALETTE_LEVEL, edgecolor="white", linewidth=0.8, zorder=3)
# ax1.set_title("Level 分布（柱状图）", fontsize=13, fontweight="bold", pad=10)
# ax1.set_xlabel("Level", fontsize=10)
# ax1.set_ylabel("数量", fontsize=10)
# ax1.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
# ax1.set_facecolor("#FFFFFF")
# for bar in bars:
#     h = bar.get_height()
#     ax1.text(bar.get_x() + bar.get_width()/2, h + total*0.003,
#              f"{h}\n({h/total*100:.1f}%)", ha="center", va="bottom", fontsize=8.5)

# # ── (2) Level 饼图 ────────────────────────────
# ax2 = fig.add_subplot(gs[0, 1])
# wedges, texts, autotexts = ax2.pie(
#     list(level_sorted.values()),
#     labels=list(level_sorted.keys()),
#     autopct="%1.1f%%",
#     colors=PALETTE_LEVEL,
#     startangle=140,
#     pctdistance=0.75,
#     wedgeprops=dict(edgecolor="white", linewidth=1.5)
# )
# for t in autotexts:
#     t.set_fontsize(9)
# ax2.set_title("Level 分布（饼图）", fontsize=13, fontweight="bold", pad=10)

# # ── (3) Type 水平柱状图 ───────────────────────
# ax3 = fig.add_subplot(gs[1, 0])
# type_keys = list(type_sorted.keys())
# type_vals = list(type_sorted.values())
# bars3 = ax3.barh(type_keys[::-1], type_vals[::-1],
#                  color=[PALETTE_TYPE[i % len(PALETTE_TYPE)] for i in range(len(type_keys)-1, -1, -1)],
#                  edgecolor="white", linewidth=0.8, zorder=3)
# ax3.set_title("Type 分布（水平柱状图）", fontsize=13, fontweight="bold", pad=10)
# ax3.set_xlabel("数量", fontsize=10)
# ax3.xaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
# ax3.set_facecolor("#FFFFFF")
# for bar in bars3:
#     w = bar.get_width()
#     ax3.text(w + total*0.002, bar.get_y() + bar.get_height()/2,
#              f"{w} ({w/total*100:.1f}%)", va="center", fontsize=8.5)

# # ── (4) Type 饼图 ─────────────────────────────
# ax4 = fig.add_subplot(gs[1, 1])
# wedges4, texts4, autotexts4 = ax4.pie(
#     type_vals,
#     labels=type_keys,
#     autopct="%1.1f%%",
#     colors=PALETTE_TYPE,
#     startangle=140,
#     pctdistance=0.78,
#     wedgeprops=dict(edgecolor="white", linewidth=1.2)
# )
# for t in autotexts4:
#     t.set_fontsize(8)
# ax4.set_title("Type 分布（饼图）", fontsize=13, fontweight="bold", pad=10)

# # ── (5) 热力图 level × type ───────────────────
# ax5 = fig.add_axes([0.07, 0.03, 0.90, 0.25])
# im = ax5.imshow(cross, cmap="YlOrRd", aspect="auto")
# ax5.set_xticks(range(len(type_names)))
# ax5.set_xticklabels(type_names, rotation=30, ha="right", fontsize=9)
# ax5.set_yticks(range(len(level_names)))
# ax5.set_yticklabels(level_names, fontsize=9)
# ax5.set_title("Level × Type 交叉热力图", fontsize=13, fontweight="bold", pad=10)
# for r in range(len(level_names)):
#     for c in range(len(type_names)):
#         val = cross[r, c]
#         color = "white" if val > cross.max() * 0.55 else "#2C3E50"
#         ax5.text(c, r, str(val), ha="center", va="center", fontsize=8.5,
#                  fontweight="bold", color=color)
# plt.colorbar(im, ax=ax5, fraction=0.015, pad=0.01)

# # ─────────────────────────────────────────────
# # 5. 保存 & 显示
# # ─────────────────────────────────────────────
# OUT_PATH = Path(FILE_PATH).parent / "math_tasks_analysis.png"
# plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
# print(f"\n✅ 图表已保存至: {OUT_PATH}")
# plt.show()



import json
from collections import Counter

file_path = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\math2code\math_train_tasks_1050.json"

def stat_top600_cross(file_path, top_n=1050):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"总数据量: {len(data)} 条")
    data_slice = data[:top_n]

    level_cnt = Counter()
    type_cnt = Counter()
    cross_cnt = Counter()  # key: (level, type)

    for item in data_slice:
        lv = item["level"]
        ty = item["type"]
        level_cnt[lv] += 1
        type_cnt[ty] += 1
        cross_cnt[(lv, ty)] += 1

    # 1. Level 单独分布
    print("===== 一、Level 难度分布（前1050条）=====")
    for lv, num in sorted(level_cnt.items()):
        print(f"{lv}: {num} 条 ({num/top_n*100:.2f}%)")

    # 2. Type 题型单独分布
    print("\n===== 二、Type 题型分布（前1050条）=====")
    for ty, num in sorted(type_cnt.items(), key=lambda x: x[1], reverse=True):
        print(f"{ty}: {num} 条 ({num/top_n*100:.2f}%)")

    # 3. Level & Type 交叉组合分布
    print("\n===== 三、Level + Type 交叉组合统计 ====")
    # 按数量降序排列
    cross_sorted = sorted(cross_cnt.items(), key=lambda x: x[1], reverse=True)
    for (lv, ty), num in cross_sorted:
        print(f"{lv} | {ty}：{num} 条")

    print(f"\n总计统计样本：{sum(level_cnt.values())} / {top_n}")

if __name__ == "__main__":
    stat_top600_cross(file_path, 1050)
    
    
# import json
# from collections import Counter, defaultdict

# file_path = r"C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\data\math2code\math_train_tasks_1750.json"
# target_per_group = 30  # 每个level-type组合目标30条
# base_num = 601         # 前601条固定保留

# def balance_math_dataset():
#     # 1. 读取全部原始数据
#     with open(file_path, "r", encoding="utf-8") as f:
#         all_data = json.load(f)
    
#     base_data = all_data[:base_num]    # 固定前601条不动
#     supplement_pool = all_data[base_num:]  # 601条之后用于补充的池子

#     # 2. 统计前601条各组合已有数量
#     group_count = defaultdict(int)
#     for item in base_data:
#         key = (item["level"], item["type"])
#         group_count[key] += 1

#     # 3. 计算每个分组还缺多少条
#     need_fill = defaultdict(int)
#     total_need = 0
#     for group, cnt in group_count.items():
#         diff = target_per_group - cnt
#         if diff > 0:
#             need_fill[group] = diff
#             total_need += diff
#     print(f"各分组缺口总量：{total_need} 条")

#     # 4. 从补充池抽取数据填补缺口
#     final_data = base_data.copy()
#     # 遍历补充池，依次填充各组缺口
#     for item in supplement_pool:
#         current_group = (item["level"], item["type"])
#         if need_fill[current_group] > 0:
#             final_data.append(item)
#             need_fill[current_group] -= 1
#             # 全部缺口填满则提前退出循环
#             if sum(need_fill.values()) == 0:
#                 break

#     # 5. 输出校验信息
#     print("===== 补齐后各组数量统计 =====")
#     final_stat = Counter()
#     for d in final_data:
#         final_stat[(d["level"], d["type"])] += 1
#     for g, num in sorted(final_stat.items(), key=lambda x: x[1], reverse=True):
#         lv, ty = g
#         print(f"{lv} | {ty}: {num} 条")
    
#     print(f"\n最终数据集总条数：{len(final_data)}")

#     # 6. 保存均衡后的新文件
#     output_path = r"C:\Users\HUAWEI\Desktop\balanced_math_train.json"
#     with open(output_path, "w", encoding="utf-8") as fw:
#         json.dump(final_data, fw, ensure_ascii=False, indent=4)
#     print(f"均衡数据集已保存至：{output_path}")

# if __name__ == "__main__":
#     balance_math_dataset()