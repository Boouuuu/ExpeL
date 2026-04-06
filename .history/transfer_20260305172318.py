import json
prompt_template = """You are a teacher agent that passes on experience to student agents. You came up with the following rules to help you achieve the task of {Source Task} effectively. The number at the end are the importance you gave to each of the rules.
RULES:
{Extracted_insights}
Now a student agent is trying to solve a similar {Target_Task}.

Some examples of this new task are:
{Fixed_fewshot_examples_of_Target_Task}

Give a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve {Target Task}. Do not state where each sentence is using whichever rule, and make sure the paragraph is VERY CONCISE and EASY TO FOLLOW!


Knowledge transfer
Fewshot Evaluation

The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target_Task} tasks efficiently:

{Finetuned_insights}

{Target_Task_description}{fewshot}

{Target_Task}
"""
Extracted_insights = """"""
Target_Task_File = r"C:\Users\HUAWEI\Desktop\ExpeL\data\math2code\code_tasks.jsonl"
# 遍历Target_Task_File
with open(Target_Task_File, 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line.strip())
        Target_Task = item.get('prompt', '').strip()
        prompt= prompt_template.format(
            Source_Task = "math problem-solving",
            Extracted_insights = Extracted_insights,
            Target_Task = Target_Task,
            Fixed_fewshot_examples_of_Target_Task = "",
            Finetuned_insights = "",
            Target_Task_description = "",
            fewshot = ""
        )
        print(""prompt)