prompt_template = """
You are a teacher agent that passes on experience to student agents. You came up with the following rules to help you achieve the task of {Source Task} effectively. The number at the end are the importance you gave to each of the rules.

RULES:
{Extracted insights from Source Task}

Now a student agent is trying to solve a similar {Target Task}.

Some examples of this new task are:
{Fixed fewshot examples of Target Task}

Give a concise and easy to follow instructional paragraph based on the RULES for the student agent to solve {Target Task}. Do not state where each sentence is using whichever rule, and make sure the paragraph is VERY CONCISE and EASY TO FOLLOW!


Knowledge transfer
Fewshot Evaluation

The following paragraph is insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the {Target Task} tasks efficiently:

{Finetuned insights}

{Target Task description + fewshot}

{Target Task}
"""