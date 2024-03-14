from argparse import ArgumentParser
from functools import cache
import os

from llama_index.embeddings.openai import OpenAIEmbedding

from openssa.l2.resource.file import FileResource

# pylint: disable=wrong-import-order
from data import FbId, DOC_NAMES_BY_FB_ID, QS_BY_FB_ID, cache_dir_path, enable_batch_qa, update_or_create_output_file


EMBED_MODEL = OpenAIEmbedding(model='text-embedding-3-large',
                              api_key=os.environ['AITO_KEY'],
                              api_base=f'http://{os.environ['AITO_HOST']}:8000/v1_aito')


@cache
def get_or_create_file_resource(doc_name: str) -> FileResource | None:
    return (FileResource(path=dir_path, embed_model=EMBED_MODEL)
            if (dir_path := cache_dir_path(doc_name))
            else None)


@enable_batch_qa
@update_or_create_output_file('RAG-FineTuned')
def answer(fb_id: FbId) -> str:
    return (file_resource.answer(QS_BY_FB_ID[fb_id])
            if (file_resource := get_or_create_file_resource(DOC_NAMES_BY_FB_ID[fb_id]))
            else 'ERROR: doc not found')


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('fb_id')
    args = arg_parser.parse_args()
    print(answer(args.fb_id))
