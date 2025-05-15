connect_memory code:
import os
from dotenv import load_dotenv, find_dotenv

from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.language_models.llms import LLM
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

from huggingface_hub import InferenceClient
from typing import Optional

# Load .env
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")

# Custom LLM using InferenceClient with novita provider
class HuggingFaceChatLLM(LLM):
    model_id: str
    api_key: str
    provider: Optional[str] = "novita"

    def __init__(self, model_id: str, api_key: str, provider: Optional[str] = "novita"):
        super().__init__(model_id=model_id, api_key=api_key, provider=provider)
        self._client = InferenceClient(provider=provider, api_key=api_key)

    @property
    def _llm_type(self) -> str:
        return "huggingface_chat_llm"

    def _call(self, prompt: str, **kwargs) -> str:
        response = self._client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"]

# Set up model and prompt
HUGGINGFACE_REPO_ID = "meta-llama/Llama-3.1-8B-Instruct"
llm = HuggingFaceChatLLM(model_id=HUGGINGFACE_REPO_ID, api_key=HF_TOKEN)

CUSTOM_PROMPT_TEMPLATE = """
You are a highly knowledgeable AI medical assistant. Based only on the following context, answer the user's question clearly and accurately.

If the answer is not in the context, respond with: "Sorry, I don't know that based on the current information."

Context:
{context}

Question:
{question}

Answer:
"""

def set_custom_prompt(custom_prompt_template):
    return PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])

# Load FAISS vector DB
DB_FAISS_PATH = "vectorstore/db_faiss"
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(search_kwargs={'k': 3}),
    return_source_documents=True,
    chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
)

user_query = input("Write Query Here: ")
response = qa_chain.invoke({'query': user_query})
print("RESULT:", response["result"])
print("SOURCE DOCUMENTS:", response["source_documents"])
