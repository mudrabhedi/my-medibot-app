import os
import streamlit as st
from dotenv import load_dotenv, find_dotenv

from typing import Optional
from huggingface_hub import InferenceClient

from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# Load environment variable
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")
HUGGINGFACE_REPO_ID = "meta-llama/Llama-3.1-8B-Instruct"

# Custom LLM for novita
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

# Prompt template
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

# Vector DB
DB_FAISS_PATH = "vectorstore/db_faiss"

@st.cache_resource
def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        model_kwargs={"device": "cpu"}  # ✅ Add this line
    )
    db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db


def main():
    st.title("Ask MediBot!")

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        st.chat_message(message['role']).markdown(message['content'])

    prompt = st.chat_input("Ask your question here...")

    if prompt:
        st.chat_message('user').markdown(prompt)
        st.session_state.messages.append({'role': 'user', 'content': prompt})

        try:
            vectorstore = get_vectorstore()
            llm = HuggingFaceChatLLM(model_id=HUGGINGFACE_REPO_ID, api_key=HF_TOKEN)

            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={'k': 3}),
                return_source_documents=True,
                chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
            )

            response = qa_chain.invoke({'query': prompt})
            result = response["result"]
            source_docs = response["source_documents"]

            result_to_show = result
            st.chat_message('assistant').markdown(result_to_show)
            st.session_state.messages.append({'role': 'assistant', 'content': result_to_show})

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
