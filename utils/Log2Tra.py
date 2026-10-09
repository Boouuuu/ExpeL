import re
import json

def parse_log(log_path: str) -> list:
    """
    从日志文件中提取正确的做题轨迹。
    返回列表，每个元素为 {"question": ..., "trajectory": ...}
    """
    with open(log_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 按分隔线分割每个任务块
    blocks = re.split(r'#######################################', text)
    trajectories = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 只处理答案正确的任务块
        if 'Answer is CORRECT' not in block:
            continue

        # 取最后一个 "Now it's your turn!" 之后的内容（如果有）
        marker = "Now it's your turn!"
        last_idx = block.rfind(marker)
        if last_idx != -1:
            start = last_idx + len(marker)
            # 跳过换行和空格
            while start < len(block) and block[start] in '\n\r ':
                start += 1
            content = block[start:]
        else:
            content = block

        # 提取问题文本（第一个 "Question:" 行）
        q_match = re.search(r'(?m)^Question:\s*(.*?)(?=\n\s*(?:Thought|Action)|$)', content, re.DOTALL)
        if not q_match:
            continue
        question_text = q_match.group(1).strip()

        # 构建轨迹：去除开头的 "Question:" 行，保留后续所有行
        lines = content.splitlines()
        question_line_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^\s*Question:', line):
                question_line_idx = i
                break
        if question_line_idx is None:
            continue

        remaining_lines = lines[question_line_idx + 1:]
        # 删除首部空行
        while remaining_lines and not remaining_lines[0].strip():
            remaining_lines.pop(0)

        remaining = '\n'.join(remaining_lines)
        # 按照示例格式，以 "Problem: " 开头
        if remaining:
            trajectory = "Problem: " + question_text + "\n" + remaining
        else:
            trajectory = "Problem: " + question_text

        trajectories.append({
            "question": question_text,
            "trajectory": trajectory
        })

    return trajectories


def save_to_json(trajectories: list, output_path: str):
    """
    将轨迹列表保存为 JSON 文件
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trajectories, f, ensure_ascii=False, indent=4)
    print(f"已成功保存 {len(trajectories)} 条轨迹到 {output_path}")


if __name__ == '__main__':
    log_path = r'C:\Users\HUAWEI\Desktop\MathWithCode2\ExpeL\logs\math2code_math\expel\run-glm-2k.txt'
    output_path = "MathTrajetory.json"  
    
    # 解析日志
    result = parse_log(log_path)
    
    # 保存为 JSON 文件
    save_to_json(result, output_path)
    
    # 可选：在控制台打印前几条预览
    print(f"\n共提取 {len(result)} 条正确轨迹")
    if result:
        print("\n第一条轨迹预览：")
        print(json.dumps(result[0], ensure_ascii=False, indent=2))