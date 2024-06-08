from argparse import ArgumentParser
from functools import cache

from openssa import Agent, HTP, AutoHTPlanner, OodaReasoner, FileResource, LMConfig
from openssa.l2.util.lm.openai import LlamaIndexOpenAILM

# pylint: disable=wrong-import-order
from data_and_knowledge import (DocName, FbId, Answer, Doc, FB_ID_COL_NAME, DOC_NAMES_BY_FB_ID, QS_BY_FB_ID,
                                EXPERT_KNOWLEDGE, EXPERT_PLAN_MAP,
                                EXPERT_PLAN_TEMPLATES, EXPERT_PLAN_COMPANY_KEY, EXPERT_PLAN_PERIOD_KEY)
from util import QAFunc, enable_batch_qa_and_eval, log_qa_and_update_output_file


@cache
def get_or_create_agent(doc_name: DocName, expert_knowledge: bool = False,
                        max_depth=2, max_subtasks_per_decomp=4,
                        llama_index_openai_lm_name: str = 'gpt-4-1106-preview') -> Agent | None:
    return (Agent(planner=AutoHTPlanner(max_depth=max_depth, max_subtasks_per_decomp=max_subtasks_per_decomp),
                  reasoner=OodaReasoner(),
                  knowledge={EXPERT_KNOWLEDGE} if expert_knowledge else None,
                  resources={FileResource(path=dir_path,
                                          lm=LlamaIndexOpenAILM(model=llama_index_openai_lm_name,
                                                                temperature=LMConfig.DEFAULT_TEMPERATURE,
                                                                max_tokens=None,
                                                                additional_kwargs={'seed': LMConfig.DEFAULT_SEED},
                                                                max_retries=3, timeout=60, reuse_client=True,
                                                                api_key=None, api_base=None, api_version=None,
                                                                callback_manager=None, default_headers=None,
                                                                http_client=None, async_http_client=None,
                                                                system_prompt=None, messages_to_prompt=None, completion_to_prompt=None,
                                                                # pydantic_program_mode=...,
                                                                output_parser=None))})
            if (dir_path := Doc(name=doc_name).dir_path)
            else None)


@cache
def expert_plan_from_fb_id(fb_id: FbId) -> HTP:
    htp: HTP = HTP.from_dict(EXPERT_PLAN_TEMPLATES[EXPERT_PLAN_MAP[fb_id]])

    htp.task.ask: str = QS_BY_FB_ID[fb_id]

    htp.concretize_tasks_from_template(**{EXPERT_PLAN_COMPANY_KEY: (doc := Doc(name=DOC_NAMES_BY_FB_ID[fb_id])).company,
                                          EXPERT_PLAN_PERIOD_KEY: doc.period})

    return htp


@enable_batch_qa_and_eval(output_name='HTP-auto-static---OODAR')
@log_qa_and_update_output_file(output_name='HTP-auto-static---OODAR')
def solve_auto_htp_statically(fb_id: FbId) -> Answer:
    return (agent.solve(problem=QS_BY_FB_ID[fb_id], plan=None, dynamic=False)
            if (agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id]))
            else 'ERROR: doc not found')


@enable_batch_qa_and_eval(output_name='HTP-auto-dynamic---OODAR')
@log_qa_and_update_output_file(output_name='HTP-auto-dynamic---OODAR')
def solve_auto_htp_dynamically(fb_id: FbId) -> Answer:
    return (agent.solve(problem=QS_BY_FB_ID[fb_id], plan=None, dynamic=True)
            if (agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id]))
            else 'ERROR: doc not found')


@enable_batch_qa_and_eval(output_name='HTP-expert-static---OODAR')
@log_qa_and_update_output_file(output_name='HTP-expert-static---OODAR')
def solve_expert_htp_statically(fb_id: FbId) -> Answer:
    if agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id]):
        problem: str = QS_BY_FB_ID[fb_id]

        if fb_id in EXPERT_PLAN_MAP:
            return agent.solve(problem=problem, plan=expert_plan_from_fb_id(fb_id), dynamic=False)

        return agent.solve(problem=problem, plan=None, dynamic=True)

    return 'ERROR: doc not found'


@enable_batch_qa_and_eval(output_name='HTP-expert-dynamic---OODAR')
@log_qa_and_update_output_file(output_name='HTP-expert-dynamic---OODAR')
def solve_expert_htp_dynamically(fb_id: FbId) -> Answer:
    if agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id]):
        problem: str = QS_BY_FB_ID[fb_id]

        if fb_id in EXPERT_PLAN_MAP:
            return agent.solve(problem=problem, plan=expert_plan_from_fb_id(fb_id), dynamic=True)

        return agent.solve(problem=problem, plan=None, dynamic=True)

    return 'ERROR: doc not found'


@enable_batch_qa_and_eval(output_name='HTP-auto-static---OODAR---Knowledge')
@log_qa_and_update_output_file(output_name='HTP-auto-static---OODAR---Knowledge')
def solve_auto_htp_statically_with_knowledge(fb_id: FbId) -> Answer:
    return (agent.solve(problem=QS_BY_FB_ID[fb_id], plan=None, dynamic=False)
            if (agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id], expert_knowledge=True))
            else 'ERROR: doc not found')


@enable_batch_qa_and_eval(output_name='HTP-auto-dynamic---OODAR---Knowledge')
@log_qa_and_update_output_file(output_name='HTP-auto-dynamic---OODAR---Knowledge')
def solve_auto_htp_dynamically_with_knowledge(fb_id: FbId) -> Answer:
    return (agent.solve(problem=QS_BY_FB_ID[fb_id], plan=None, dynamic=True)
            if (agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id], expert_knowledge=True))
            else 'ERROR: doc not found')


@enable_batch_qa_and_eval(output_name='HTP-expert-static---OODAR---Knowledge')
@log_qa_and_update_output_file(output_name='HTP-expert-static---OODAR---Knowledge')
def solve_expert_htp_statically_with_knowledge(fb_id: FbId) -> Answer:
    if agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id], expert_knowledge=True):
        problem: str = QS_BY_FB_ID[fb_id]

        if fb_id in EXPERT_PLAN_MAP:
            return agent.solve(problem=problem, plan=expert_plan_from_fb_id(fb_id), dynamic=False)

        return agent.solve(problem=problem, plan=None, dynamic=True)

    return 'ERROR: doc not found'


@enable_batch_qa_and_eval(output_name='HTP-expert-dynamic---OODAR---Knowledge')
@log_qa_and_update_output_file(output_name='HTP-expert-dynamic---OODAR---Knowledge')
def solve_expert_htp_dynamically_with_knowledge(fb_id: FbId) -> Answer:
    if agent := get_or_create_agent(DOC_NAMES_BY_FB_ID[fb_id], expert_knowledge=True):
        problem: str = QS_BY_FB_ID[fb_id]

        if fb_id in EXPERT_PLAN_MAP:
            return agent.solve(problem=problem, plan=expert_plan_from_fb_id(fb_id), dynamic=True)

        return agent.solve(problem=problem, plan=None, dynamic=True)

    return 'ERROR: doc not found'


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('fb_id')
    arg_parser.add_argument('--knowledge', action='store_true')
    arg_parser.add_argument('--expert-plan', action='store_true')
    arg_parser.add_argument('--dynamic-exec', action='store_true')
    args = arg_parser.parse_args()

    match (args.knowledge, args.expert_plan, args.dynamic_exec):
        case (False, False, False):
            solve: QAFunc = solve_auto_htp_statically

        case (False, False, True):
            solve: QAFunc = solve_auto_htp_dynamically

        case (False, True, False):
            solve: QAFunc = solve_expert_htp_statically

        case (False, True, True):
            solve: QAFunc = solve_expert_htp_dynamically

        case (True, False, False):
            solve: QAFunc = solve_auto_htp_statically_with_knowledge

        case (True, False, True):
            solve: QAFunc = solve_auto_htp_dynamically_with_knowledge

        case (True, True, False):
            solve: QAFunc = solve_expert_htp_statically_with_knowledge

        case (True, True, True):
            solve: QAFunc = solve_expert_htp_dynamically_with_knowledge

    solve(fb_id
          if (fb_id := args.fb_id).startswith(FB_ID_COL_NAME)
          else f'{FB_ID_COL_NAME}_{fb_id}')