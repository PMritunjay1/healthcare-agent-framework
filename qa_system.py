# qa_system.py (Upgraded with Caching)

import os
from datasets import load_from_disk
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Define the path for our cached vector store ---
FAISS_INDEX_PATH = "./vector_store_cache/medqa_faiss_index"

class QASystem:
    def __init__(self, dataset_path='./datasets/medalpaca_medqa'):
        print("Initializing Clinical QA System...")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        # We always need the embeddings model for both loading and creating
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # --- SMART CACHING LOGIC ---
        # Check if the pre-built vector store already exists on disk
        if os.path.exists(FAISS_INDEX_PATH):
            print(f"Found cached vector store at '{FAISS_INDEX_PATH}'. Loading...")
            # If it exists, load it directly (this is very fast)
            self.vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("Vector store loaded successfully from cache.")
        else:
            print(f"No cached vector store found. Building a new one... (This is a one-time process)")
            # If it doesn't exist, perform the slow, one-time setup
            # 1. Load the dataset from disk
            dataset = load_from_disk(dataset_path)['train']
            
            # 2. Prepare data for the vector store
            questions = [row['input'] for row in dataset]
            
            # 3. Build the FAISS vector store (the slow part)
            print("Creating vector store from MedQA questions... (This may take several minutes)")
            self.vector_store = FAISS.from_texts(texts=questions, embedding=embeddings)
            print("Vector store created.")
            
            # 4. CRITICAL STEP: Save the newly created store to disk for future use
            print(f"Saving new vector store to '{FAISS_INDEX_PATH}'...")
            self.vector_store.save_local(FAISS_INDEX_PATH)
            print("Vector store saved successfully.")

        # --- The rest of the setup remains the same, but we need to load the full QA map ---
        print("Loading QA map...")
        full_dataset = load_from_disk(dataset_path)['train']
        self.qa_map = {row['input']: row['output'] for row in full_dataset}
        
        prompt_template = """
        You are a helpful medical assistant. Use the following example question and answer to help you answer the user's question.
        Provide a clear, helpful, and accurate response based on your knowledge.

        ---
        EXAMPLE QUESTION: {example_question}
        EXAMPLE ANSWER: {example_answer}
        ---

        Now, please answer the following question:
        USER'S QUESTION: {user_question}
        
        YOUR ANSWER:
        """
        self.prompt = PromptTemplate(template=prompt_template, input_variables=["example_question", "example_answer", "user_question"])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def answer_question(self, user_question: str) -> str:
        # ... (This method remains exactly the same) ...
        print(f"QA System received question: {user_question}")
        similar_docs = self.vector_store.similarity_search(user_question, k=1)
        if not similar_docs:
            return "I could not find a relevant example to help answer your question."
        example_question = similar_docs[0].page_content
        example_answer = self.qa_map.get(example_question, "No example answer found.")
        print("Found a relevant example to use as context.")
        response = self.chain.invoke({
            "example_question": example_question,
            "example_answer": example_answer,
            "user_question": user_question
        })
        return response