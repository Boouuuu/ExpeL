conda activate expel
for /f "tokens=2 delims==" %I in ('wmic os get localdatetime /value') do set datetime=%I

python train.py benchmark=math2code_math run_name=run-glm-RenewAction agent.llm=glm-4.7 testing=false resume=false > "run-glm-RenewAction_math_train_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=math2code_math run_name=run-glm-2k agent.llm=glm-4.7 testing=false resume=true manual_finish_review=true >> "run-glm-2k_math_train_20260705_111449.log" 2>&1

python train.py benchmark=math2code_math run_name=run-glm-2k agent.llm=glm-4.7 testing=false resume=true manual_finish_review=true >> "run-glm-2k_math_train_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=math2code_math load_run_name=run run_name=insights-math2code-run agent.llm=glm-4.7 agent.max_num_rules=30 agent.success_critique_num=2 testing=false resume=false 



python train.py benchmark=code2math_code run_name=run-codetrain agent.llm=glm-4.7 testing=false resume=false manual_finish_review=true > "run-codetrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=code2math_code run_name=run-cfcodetrain agent.llm=glm-4.7 testing=false resume=false > "run-cfcodetrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=code2math_code run_name=run-cfcodetrain-2 agent.llm=glm-4.7 testing=false resume=false > "run-cfcodetrain-2_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=code2math_code run_name=run-cfcodetrain agent.llm=glm-4.7 testing=false resume=true >> "run-cfcodetrain_20260924_193208.log" 2>&1



python train.py benchmark=code2math_code run_name=run-codetrain-2 agent.llm=glm-4.7 testing=false resume=true manual_finish_review=true >> "run-codetrain-2_20260915_173852.log" 2>&1

python train.py benchmark=code2math_code run_name=run-codetrain agent.llm=glm-4.7 testing=false resume=true manual_finish_review=true >> "run-codetrain_20260913_170117.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-glm-NewCodeData run_name=run-NewCodeData-insight agent.llm=glm-4.7 agent.max_num_rules=5000 agent.success_critique_num=2 testing=false resume=false > "run-codetrain-NewCodeData_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-codetrain run_name=run-codetrain-insight agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false > "run-codetrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-codetrain-2 run_name=run-codetrain-2-insight agent.llm=glm-4.7 agent.max_num_rules=1000 agent.success_critique_num=2 testing=false resume=false > "run-codeinsight-2_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-codetrain run_name=run-codetrain-insight agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false >> "run-codetrain_20260914_204442.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-cfcodetrain run_name=run-cfcodetrain-insight agent.llm=glm-4.7 agent.max_num_rules=1000 agent.success_critique_num=2 testing=false resume=false > "expel-cfcodetrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=code2math_code load_run_name=run-cfcodetrain run_name=run-glm-2k-expel agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false > "run-glm-2k-expel_math_train_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=math2code_math load_run_name=run-glm-2k run_name=run-glm-2k-expel agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false > "run-glm-2k-expel_math_train_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

conda env create -n expel -f "%USERPROFILE%\Desktop\expel-environment.yml

python train.py benchmark=physics2code_physics run_name=run-physicsTrain agent.llm=glm-4.7 testing=false resume=false > "run-physicsTrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=physics2code_physics run_name=run-physicsTrain agent.llm=glm-4.7 testing=false resume=true >> "run-physicsTrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=physics2code_physics load_run_name=run-physicsTrain-2 run_name=run-physicsTrain-insight agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false > "run-physicsTrain-insight_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python insight_extraction.py benchmark=physics2code_physics load_run_name=run-physicsTrain-insight run_name=run-physicsTrain-insight agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=true resume_fold=0 >> "run-physicsTrain-insight_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=chemistry2code_chemistry run_name=run-chemistryTrain agent.llm=glm-4.7 testing=false resume=false > "run-chemistryTrain_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python train.py benchmark=chemistry2code_chemistry run_name=run-chemistryTrain agent.llm=glm-4.7 testing=false resume=true >> "run-chemistryTrain_20260922_200627.log" 2>&1

python insight_extraction.py benchmark=chemistry2code_chemistry load_run_name=run-chemistryTrain run_name=run-chemistryTrain-insight agent.llm=glm-4.7 agent.max_num_rules=500 agent.success_critique_num=2 testing=false resume=false > "run-chemistryTrain-insight_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python eval.py benchmark=math2code_math load_run_name=extracted_insights/run-glm-2k-expel run_name=run-glm-2k-expel agent.llm=qwen eval_benchmark=code2math_code benchmark.eval_configs.k_folds=1 agent.fewshot_strategy=task_similarity agent.retrieval_kwargs.max_fewshot_tokens= auto testing=false resume=false > "qwen-mbpp-expel_eval_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

python transfer-expel.py > "expel_Math2Code_LiveCodebench_%datetime:~0,8%_%datetime:~8,6%.log" 2>&1

# agent.fewshot_strategy = {task_similarity, thought_similarity,task_thought_similarity)
# agent.llm = {gpt-3.5-turbo (default), gpt-4}
# agent.retrieval_kwargs.max_fewshot_tokens=auto
# benchmark.eval_configs.k_folds=2 
# agent.retrieval_kwargs.buffer_retrieve_ratio = safety measure to not retrieve 0 examples (bigger is safer)