# Prompt 模板：纯 dict + str.format，与 models/llm.py 阿里云 API 消息列表一致（不依赖 LangChain）

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

FORMAT_RULES_OPERATION_TEMPLATE = """
{{
  "type": "THINKING | METHOD | TECHNIQUE",
  "trigger": "<TRIGGER>",(except THINKING)
  "insight": "<INSIGHT>"
}}
Output only these JSON objects (one per line)."""

# CRITIQUE_SUMMARY_SUFFIX = dict(full = """ADD a new rule when it is VERY insightful.
# """, not_full = """ADD a new rule when it is VERY insightful.
# """)
CRITIQUE_SUMMARY_SUFFIX = dict(full = """ """, not_full = """ """)

### 3个level的prompt
human_critique_existing_rules_all_success_template = """{instruction}
Here are the trials:
{success_history}

Your goal is to extract, refine, and organize reusable experience from these trials into a set of structured insights. Every insight must be assigned to exactly one of the three categories listed below:
[THINKING] 
- Focus: reasoning strategies and high-level planning.
- Content: Procedures for regulating reasoning behavior, including how to allocate attention and sequence reasoning steps. These insights define the meta-structure of the thought process (how to think) rather than solving a specific problem type. Ignore differences that are solely caused by environment interaction policies.
- Example: {{
    "type": "THINKING",
    "insight": "Identify the chemical species, reaction conditions, relevant constraints, and target quantity from the complete problem description before selecting equations, reactions, or chemical principles."
}},
[METHOD]
- Focus: Structured solution paradigms for specific classes of problems.
- Content: Canonical solution schemas and the logical flow between reasoning steps. These insights provide a systematic template for solving a category of problems (e.g., induction, case analysis) without being tied to specific numerical values.
- Example: {{
    "type": "METHOD",
    "trigger": "When solving equilibrium problems in which the equilibrium composition must be determined from initial conditions and a known equilibrium relationship.",
    "insight": "Step 1. Define the chemical species involved and write the balanced reaction. Step 2. Represent the initial amounts or concentrations of the relevant species. Step 3. Introduce variables for the changes caused by the reaction and construct the equilibrium composition. Step 4. Express the equilibrium relationship using the equilibrium composition. Step 5. Solve for the unknown equilibrium quantities under the physical constraints of the system. Step 6. Check that the resulting composition is chemically admissible and consistent with the assumed reaction direction."
}}
[TECHNIQUE] 
- Focus: Fine-grained reasoning operations for local state transformation, constraint maintenance, and executing individual solution steps.ng individual solution steps.
- Content: Reusable local-level operations that describe how to carry out a specific reasoning step, such as transforming representations, applying local constraints, deriving intermediate results, simplifying expressions, or handling specific subcases. These insights are more concrete than METHOD and can be applied within a broader solution paradigm, but should remain general enough to transfer across related problem instances.
- Example: {{
    "type": "TECHNIQUE",
    "trigger": "When determining whether an oxidation-reduction process is chemically balanced.",
    "insight": "Track changes in oxidation state to identify the oxidized and reduced species, and verify that the total electron loss equals the total electron gain."
}}

Analyze the underlying structure of these successful trajectories and extract reusable knowledge based on the following two dimensions:
1. Individual Success Drivers: For each specific trial, identify the core strategy, method, or technical execution that was indispensable for reaching the correct result. Pinpoint what made the reasoning successful within its specific domain.
2. Cross-Task Generalization: Conduct a structural alignment across different tasks. Identify shared logic flows, similar state-transition patterns (e.g., consistent iterative updates), or common termination conditions that persist despite semantic differences. Formulate these as high-level, transferable solution schemas.
You can generate a set of insights, which must be generalized and actionable for follow-up tasks. Follow the below format:
""" + FORMAT_RULES_OPERATION_TEMPLATE


human_all_success_existing_rules_critique = {
    "role": "human",
    "content": human_critique_existing_rules_all_success_template,
}

# 3个level的prompt
human_critique_existing_rules_template = """{instruction}
Here are the two previous trials to compare and critique:
TRIAL TASK:
{task}

SUCCESSFUL TRIAL:
{success_history}

FAILED TRIAL:
{fail_history}

Your goal is to extract, refine, and organize reusable experience from these trials into a set of structured insights. Every insight must be assigned to exactly one of the three categories listed below:
[THINKING] 
- Focus: reasoning strategies and high-level planning.
- Content: Procedures for regulating reasoning behavior, including how to allocate attention and sequence reasoning steps. These insights define the meta-structure of the thought process (how to think) rather than solving a specific problem type. Ignore differences that are solely caused by environment interaction policies.
- Example: {{
      "type": "THINKING",
      "insight": "Resolve the intended input-output behavior and constraints from the complete task specification before constructing the solution."
    }},
[METHOD]
- Focus: Structured solution paradigms for specific classes of problems.
- Content: Canonical solution schemas and the logical flow between reasoning steps. These insights provide a systematic template for solving a category of problems (e.g., induction, case analysis) without being tied to specific numerical values.
- Example: {{
      "type": "METHOD",
      "trigger": "When solving problems involving hierarchical structures, exhaustive traversal, recursive decomposition, or exploring alternative branches.",
      "insight": "Step 1. Define the state represented by each recursive call. Step 2. Specify the base cases and termination conditions. Step 3. Define how the current state generates smaller subproblems. Step 4. Combine the returned results to construct the result for the current state."
    }}
[TECHNIQUE] 
- Focus: Fine-grained reasoning operations for local state transformation, constraint maintenance, and executing individual solution steps.
- Content: Reusable local-level operations that describe how to carry out a specific reasoning step, such as transforming representations, applying local constraints, deriving intermediate results, simplifying expressions, or handling specific subcases. These insights are more concrete than METHOD and can be applied within a broader solution paradigm, but should remain general enough to transfer across related problem instances.
- Example: {{
    "type": "TECHNIQUE",
    "trigger": "When updating a sequence boundary while iterating through an index range.",
    "insight": "Update the boundary only after verifying that the new index remains within the valid range."
  }}

Analyze the alignment of the reasoning steps between the two trials. Identify the specific step where the failed trajectory deviates from the correct path and extract reusable knowledge based on the following two dimensions:
1. Error Prevention (Negative): Identify the specific cause of failure (e.g., misinterpretation of constraints, incorrect sequencing of sub-tasks, or local operational errors). Formulate insights to detect and prevent these specific error patterns.
2. Success Factor (Positive): Identify the critical logic or state transition in the successful trial that directly led to the correct result. Formulate insights that define the necessary conditions or steps for achieving accuracy.
The output insights must be technical, generalized, and actionable for future tasks. Follow the below format:
""" + FORMAT_RULES_OPERATION_TEMPLATE

human_existing_rules_critique = {
    "role": "human",
    "content": human_critique_existing_rules_template,
}

HUMAN_CRITIQUES = dict(
    compare_existing_rules=human_existing_rules_critique,
    all_success_existing_rules=human_all_success_existing_rules_critique,
)

VERIFICATION_INSTRUCTION = """You are the Insight Pool Verifier. You will receive a BATCH of NEW candidate insights. For EACH candidate, similar insights were retrieved from the current pool (same "type", ranked by fusion retrieval). In ONE response, decide how to update the shared pool so it stays compact, non-redundant, and reusable.

Each insight is JSON:
{{"type":"THINKING|METHOD|TECHNIQUE","trigger":"..."(except THINKING),"insight":"..."}}

Batch input (list of objects):
{new_insights_with_retrieval}

Each batch item has:
- "proposed": one NEW candidate insight
- "retrieved_similar": similar existing pool rows for that candidate (may be empty)

Allowed operations (machine-parseable JSON only):
- add: append a new insight object (usually a NEW candidate or a merged generalization).
- edit: replace an existing pool row matched by exact "insight" string (use target_insight from a retrieved list).
- remove: delete a pool row matched by target_insight when it is fully superseded or redundant.

Consider ALL candidates together. You may output multiple operations across the whole batch (e.g. merge several candidates, edit one retrieved row, remove redundant rows).

Respond with ONE JSON object ONLY:
{{
  "operations": [
    {{"op": "add", "rule": {{"type": "TECHNIQUE", "trigger": "...", "insight": "..."}}}},
    {{"op": "edit", "target_insight": "<verbatim insight string from retrieved list>", "rule": {{"type": "...", "trigger": "...", "insight": "..."}}}},
    {{"op": "remove", "target_insight": "<verbatim insight string from retrieved list>"}}
  ]
}}
Prefer edit over add when new content refines an existing retrieved insight. Avoid duplicate adds for redundant candidates in the same batch."""

RULE_TEMPLATE = dict(
    hotpotqa={
        "role": "human",
        "content": """The following are some experience you gather on a similar task of question answering using Wikipedia API. Use these as references to help you perform this task:
{rules}
""",
    },
    webshop={
        "role": "human",
        "content": """
The following are some experiences (in decreasing order of importance) you gathered on tasks of purchasing items requested by an user by interacting with an online website. Use these experiences as useful references to help you perform better on this task:
{rules}
""",
    },
    alfworld={
        "role": "human",
        "content": """The following are some experience you gather on a similar task of completing a household task by interacting in a household environment. Use these as references to help you perform this task:
{rules}
""",
    },
    fever={
        "role": "human",
        "content": """The following paragraph are insights a teacher agent provided to you. It is MANDATORY for you to follow these insights as CLOSELY as possible as they will help you perform the fact verification tasks efficiently:

In order to successfully complete factual verification tasks, begin by clearly understanding the claim. Then formulate a search query that is precise and directly related to the claim. Include the main subjects or context from the claim in your query. If the initial search doesn't yield desired results, consider refining the query, using synonyms, or breaking down the claim into smaller parts. Always verify the information you obtain against the claim before drawing a conclusion. If multiple searches fail, consider changing the search strategy or looking for related information that might indirectly provide the necessary information. If all else fails, consider that the answer might be found in the observations already made. When you're ready to draw a conclusion, double-check it against the information obtained and ensure its accuracy. Lastly, always be prepared to exhaust all possible search queries related to the task at hand before concluding. Remember, the claim can either be supported, refuted, or there might not be enough information to draw a conclusion.{rules}
""",
    },
    code2math_code={
        "role": "human",
        "content": """The following are some experience you gathered on the task of Code Completion. Use these as references to help you perform this mathematics task:
{rules}
""",
    },
    math2code_math={
        "role": "human",
        "content": """The following are some experience you gathered on the task of Mathematics. Use these as references to help you perform this code completion task:
{rules}
""",
    },
    physics2code_physics={
        "role": "human",
        "content": """The following are some experience you gathered on the task of Physics. Use these as references to help you perform this code completion task:
{rules}
""",
    },
    chemistry2code_chemistry={
        "role": "human",
        "content": """The following are some experience you gathered on the task of Chemistry. Use these as references to help you perform this code completion task:
{rules}
""",
    },
)
