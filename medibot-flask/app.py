import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv, find_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient
from typing import Optional

# Load environment variables
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")
HUGGINGFACE_REPO_ID = "meta-llama/Llama-3.1-8B-Instruct"
DB_FAISS_PATH = "vectorstore/db_faiss"

# Custom LLM using InferenceClient with Together provider
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

def get_vectorstore():
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
    db = FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db

def set_custom_prompt(template):
    return PromptTemplate(template=template, input_variables=["context", "question"])

# Build app
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "MediBot Flask Backend Running ✅"

@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_input = request.json.get("question", "")
        if not user_input:
            return jsonify({"error": "Missing 'question' field"}), 400

        # Setup model + retriever + chain
        llm = HuggingFaceChatLLM(model_id=HUGGINGFACE_REPO_ID, api_key=HF_TOKEN)
        vectorstore = get_vectorstore()
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=False,  # don't include docs in response
            chain_type_kwargs={"prompt": set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
        )

        # Run LLM chain
        result = qa_chain.invoke({"query": user_input})
        return jsonify({"answer": result["result"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
