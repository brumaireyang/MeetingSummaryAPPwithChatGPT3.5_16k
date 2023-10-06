import os
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.document_loaders import TextLoader
from langchain.chains.mapreduce import MapReduceChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import ReduceDocumentsChain, MapReduceDocumentsChain

class OpenAISummarizer:
    def __init__(self, api_key):
        self.api_key = api_key
        os.environ["OPENAI_API_KEY"] = self.api_key
        
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0)

    def summarize(self, inputData):
        # Load documents
        loader = TextLoader(inputData, encoding='utf-8')
        docs = loader.load()

        # Define map and reduce templates
        map_template = """以下是一份会议记录：\n{docs}\n,请使用以上记录中的语言（中文或者英文）, 以 Markdown 格式为会议进行严谨，严肃，的会议总结，要求按先后顺序列出所有重要信息，要求不要省略任何细节中的信息，要求标注会议发生时间和会议参加人员，要求输出语言与会议记录文本中的主要语言相同。\n会议报告: \n"""
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=self.llm, prompt=map_prompt)
        
        reduce_template = """以下是一份会议总结：\n{doc_summaries}\n，请使用以上记录中的语言（中文或者英文）, 作为一名会议助手，将这些内容合并，不要缩减内容，不要重复的内容，以 Markdown 格式输出，要求不要省略任何细节中的信息，要求输出语言与会议文本中的主要语言相同. \n会议报告:"""
        reduce_prompt = PromptTemplate.from_template(reduce_template)
        reduce_chain = LLMChain(llm=self.llm, prompt=reduce_prompt)

        # Combine documents and reduce them
        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_chain, document_variable_name="doc_summaries"
        )
        reduce_documents_chain = ReduceDocumentsChain(
            combine_documents_chain=combine_documents_chain,
            collapse_documents_chain=combine_documents_chain,
            token_max=15000,
        )

        # Map and reduce documents
        map_reduce_chain = MapReduceDocumentsChain(
            llm_chain=map_chain,
            reduce_documents_chain=reduce_documents_chain,
            document_variable_name="docs",
            return_intermediate_steps=False,
        )
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=15000, chunk_overlap=50
        )
        split_docs = text_splitter.split_documents(docs)

        # Final result
        outputResult = map_reduce_chain.run(split_docs)
        return outputResult
