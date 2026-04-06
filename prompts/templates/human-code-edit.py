from langchain.prompts.chat import HumanMessagePromptTemplate, SystemMessagePromptTemplate

human_instruction_fewshots_template = """{instruction}

{fewshots}

(END OF EXAMPLES)
"""
# human_instruction_fewshot_message_prompt = lambda message_type: \
#     SystemMessagePromptTemplate.from_template(
#         human_instruction_fewshots_template,
#     ) if message_type == 'all_system' else \
#         HumanMessagePromptTemplate.from_template(human_instruction_fewshots_template,)
def human_instruction_fewshot_message_prompt(message_type):
    message_dict = {}
    # 根据message_type设置不同角色
    if message_type == 'all_system':
        message_dict["role"] = "system"
    else:
        message_dict["role"] = "human"
    # 公共内容：赋值模板字符串（保持纯字典格式，不依赖LangChain）
    message_dict["content"] = human_instruction_fewshots_template
    return message_dict
    
    

human_task_template = """Now it's your turn!
{task}"""
# human_task_message_prompt = HumanMessagePromptTemplate.from_template(
#     human_task_template,
# )
human_task_message_prompt = {
    "role": "human",
    "content": human_task_template,
}

FORMAT_RULES_OPERATION_TEMPLATE = """<OPERATION> <RULE NUMBER>: <RULE>

The available operations are: EDIT (if any existing rule is not general enough or can be enhanced, rewrite and improve it), ADD (add new rules that are very different from existing rules and relevant for other tasks). Each needs to CLOSELY follow their corresponding formatting below (any existing rule not edited is considered copied):

EDIT <EXISTING RULE NUMBER>: <NEW MODIFIED RULE>
ADD <NEW RULE NUMBER>: <NEW RULE>

Do not mention the trials in the rules because all the rules should be GENERALLY APPLICABLE. Each rule should be concise and easy to follow. Any operation can be used MULTIPLE times. Each existing rule can only get a maximum of 1 operation. """

CRITIQUE_SUMMARY_SUFFIX = dict(full = """ADD a new rule when it is VERY insightful and different from EXISTING RULES. Below are the operations you do to the above list of EXISTING RULES:
""", not_full = """ADD a new rule when it is VERY insightful and different from EXISTING RULES. Below are the operations you do to the above list of EXISTING RULES:
""")

### 3个level的prompt
human_critique_existing_rules_all_success_template = """{instruction}
Here are the trials:
{success_history}

Here are the EXISTING RULES:
{existing_rules}
Your goal is to extract, refine, and organize reusable experience of code completion from these trials into THREE DISTINCT TYPES of rules. Each rule MUST be assigned to exactly one of the following categories by adding a prefix tag:
[THINKING] Describe domain-agnostic cognitive strategies that regulate high-level planning and reasoning behavior. They are used to guide how the agent plans, allocates attention, and sequences reasoning steps, rather than how to solve a specific type of problem. Specify how the agent should structure its reasoning process before or during problem solving, independent of the concrete domain or problem class. Thinking Pattern Rules answer the question of how to think, not what method or formula to apply. For problem-type-specific reasoning, prefer [METHOD] or [TECHNIQUE]. Example: [THINKING] Decompose a complex problem into smaller subproblems before attempting detailed computation.
[METHOD] Capture structured solution paradigms associated with a specific class of problems. Describe canonical solution schemas, including the organization of steps and the logical flow between them, while remaining independent of concrete numerical values. Method Rules answer the question of how problems of this type are generally solved and can be directly translated into structured mathematical reasoning, such as induction, case analysis, or stepwise derivation. Example: [METHOD] Induction-based problem solving: step1. Establish the base case. step2. Assume the property holds for n=k. step3. Prove it for n=k+1 by systematically applying logical steps. step4. Conclude the result holds for all n.
[TECHNIQUE] Represent fine-grained, execution-level knowledge used to perform concrete computations or verify intermediate results. These rules encode reusable mathematical facts, formulas, or transformation laws that are applied within a single reasoning step. Example: [TECHNIQUE] To simplify a fraction, divide both numerator and denominator by their greatest common divisor (GCD).

By examining and contrasting the successful and failed trials, and the list of existing rules, you can perform the following operations: ADD or EDIT.

When updating rules:
- Prefer [THINKING] rules when successful trials demonstrate effective planning, appropriate planning order, or deliberate control of the reasoning process, or when failure is due to poor planning, improper act order, or premature termination rather than lack of domain knowledge.
- Prefer [METHOD] rules when successful trials consistently follow a clear and reusable solution structure for a specific problem type, or when failure is due to missing or incorrect solution structure tied to a specific problem type.
- Prefer [TECHNIQUE] rules for any reusable execution-level operation, identity, transformation, or verification step that appears as a correct and local computation in successful trials.
- Before assigning a rule to [THINKING] or [METHOD], explicitly check whether it could instead be expressed as a single mathematical operation or formula. If so, prefer [TECHNIQUE].
- Do NOT mix multiple categories in a single rule.

The resulting rules should be GENERAL, HIGH-LEVEL, and EXPLICITLY LABELED, so they can be reused to improve Thought and Action in future, unseen mathematics tasks. Follow the below format:

""" + FORMAT_RULES_OPERATION_TEMPLATE

### Expel原始模板
# human_critique_existing_rules_all_success_template = """{instruction}
# Here are the trials:
# {success_history}

# Here are the EXISTING RULES:
# {existing_rules}

# By examining the successful trials, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules are general and high level insights of the successful trials or proposed way of Thought so they can be used as helpful tips to different tasks in the future. Have an emphasis on tips that help the agent perform better Thought and Action. Follow the below format:

# """ + FORMAT_RULES_OPERATION_TEMPLATE

human_all_success_existing_rules_critique = HumanMessagePromptTemplate.from_template(human_critique_existing_rules_all_success_template)

### Expel原始模板
# human_critique_existing_rules_template = """{instruction}
# Here are the two previous trials to compare and critique:
# TRIAL TASK:
# {task}

# SUCCESSFUL TRIAL:
# {success_history}

# FAILED TRIAL:
# {fail_history}

# Here are the EXISTING RULES:
# {existing_rules}

# By examining and contrasting to the successful trial, and the list of existing rules, you can perform the following operations: add, edit, remove, or agree so that the new list of rules is GENERAL and HIGH LEVEL critiques of the failed trial or proposed way of Thought so they can be used to avoid similar failures when encountered with different questions in the future. Have an emphasis on critiquing how to perform better Thought and Action. Follow the below format:

# """ + FORMAT_RULES_OPERATION_TEMPLATE

# 3个level的prompt
human_critique_existing_rules_template = """{instruction}
Here are the two previous trials to compare and critique:
TRIAL TASK:
{task}

SUCCESSFUL TRIAL:
{success_history}

FAILED TRIAL:
{fail_history}

Here are the EXISTING RULES:
{existing_rules}

Your goal is to extract, refine, and organize reusable experience of code completion from these trials into THREE DISTINCT TYPES of rules. Each rule MUST be assigned to exactly one of the following categories by adding a prefix tag:
[THINKING] Describe domain-agnostic cognitive strategies that regulate high-level planning and reasoning behavior. They are used to guide how the agent plans, allocates attention, and sequences reasoning steps, rather than how to solve a specific type of problem. Specify how the agent should structure its reasoning process before or during problem solving, independent of the concrete domain or problem class. Thinking Pattern Rules answer the question of how to think, not what method or formula to apply. For problem-type-specific reasoning, prefer [METHOD] or [TECHNIQUE]. Example: [THINKING] Decompose a complex problem into smaller subproblems before attempting detailed computation.
[METHOD] Capture structured solution paradigms associated with a specific class of problems. Describe canonical solution schemas, including the organization of steps and the logical flow between them, while remaining independent of concrete numerical values. Method Rules answer the question of how problems of this type are generally solved and can be directly translated into structured mathematical reasoning, such as induction, case analysis, or stepwise derivation. Example: [METHOD] Induction-based problem solving: step1. Establish the base case. step2. Assume the property holds for n=k. step3. Prove it for n=k+1 by systematically applying logical steps. step4. Conclude the result holds for all n.
[TECHNIQUE] Represent fine-grained, execution-level knowledge used to perform concrete computations or verify intermediate results. These rules encode reusable mathematical facts, formulas, or transformation laws that are applied within a single reasoning step. Example: [TECHNIQUE] To simplify a fraction, divide both numerator and denominator by their greatest common divisor (GCD).

By examining and contrasting the successful and failed trials, and the list of existing rules, you can perform the following operations: ADD or EDIT.

When updating rules:
- Prefer [THINKING] rules when successful trials demonstrate effective planning, appropriate planning order, or deliberate control of the reasoning process, or when failure is due to poor planning, improper act order, or premature termination rather than lack of domain knowledge.
- Prefer [METHOD] rules when successful trials consistently follow a clear and reusable solution structure for a specific problem type, or when failure is due to missing or incorrect solution structure tied to a specific problem type.
- Prefer [TECHNIQUE] rules for any reusable execution-level operation, identity, transformation, or verification step that appears as a correct and local computation in successful trials.
- Before assigning a rule to [THINKING] or [METHOD], explicitly check whether it could instead be expressed as a single mathematical operation or formula. If so, prefer [TECHNIQUE].
- Do NOT mix multiple categories in a single rule.

The resulting rules should be GENERAL, HIGH-LEVEL, and EXPLICITLY LABELED, so they can be reused to improve Thought and Action in future, unseen mathematics tasks. Follow the below format:

""" + FORMAT_RULES_OPERATION_TEMPLATE

human_existing_rules_critique = HumanMessagePromptTemplate.from_template(human_critique_existing_rules_template)

HUMAN_CRITIQUES = dict(
    compare_existing_rules=human_existing_rules_critique,
    all_success_existing_rules=human_all_success_existing_rules_critique,
)

RULE_TEMPLATE = dict(
    hotpotqa=HumanMessagePromptTemplate.from_template("""The following are some experience you gather on a similar task of question answering using Wikipedia API. Use these as references to help you perform this task:
{rules}
"""),
    webshop=HumanMessagePromptTemplate.from_template("""
The following are some experiences (in decreasing order of importance) you gathered on tasks of purchasing items requested by an user by interacting with an online website. Use these experiences as useful references to help you perform better on this task:
{rules}
"""),
    alfworld=HumanMessagePromptTemplate.from_template("""The following are some experience you gather on a similar task of completing a household task by interacting in a household environment. Use these as references to help you perform this task:
{rules}
"""),
    fever=HumanMessagePromptTemplate.from_template("""The following paragraph are insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the fact verification tasks efficiently:

In order to successfully complete factual verification tasks, begin by clearly understanding the claim. Then formulate a search query that is precise and directly related to the claim. Include the main subjects or context from the claim in your query. If the initial search doesn't yield desired results, consider refining the query, using synonyms, or breaking down the claim into smaller parts. Always verify the information you obtain against the claim before drawing a conclusion. If multiple searches fail, consider changing the search strategy or looking for related information that might indirectly provide the necessary information. If all else fails, consider that the answer might be found in the observations already made. When you're ready to draw a conclusion, double-check it against the information obtained and ensure its accuracy. Lastly, always be prepared to exhaust all possible search queries related to the task at hand before concluding. Remember, the claim can either be supported, refuted, or there might not be enough information to draw a conclusion.{rules}
"""),
    code2math_code=HumanMessagePromptTemplate.from_template("""The following are some experience you gathered on the task of Code Completion. Use these as references to help you perform this mathematics task:
{rules}
"""),
    math2code_math=HumanMessagePromptTemplate.from_template("""The following are some experience you gathered on the task of Math Problem Solving. Use these as references to help you perform this code completion task:
{rules}
"""),
)
