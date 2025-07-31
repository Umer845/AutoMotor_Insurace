# qa.py
import streamlit as st
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain_core.documents import Document

def show_question_answer():
    st.title("🤖 Ask your Question")

    if "pdf_context" not in st.session_state:
        st.warning("⚠️ Please upload a PDF first from the main page.")
        return

    question = st.text_area("💬 Your Question")

    if st.button("Ask"):
        # ---- Step 1: Simple match check ----
        pdf_text = st.session_state['pdf_context'].lower()
        question_text = question.lower()

        if any(word in pdf_text for word in question_text.split()):
            # Found a match → allow LLM to answer
            llm = Ollama(model="tinyllama")

            prompt = PromptTemplate(
                input_variables=["context", "question"],
                template="""
                You are an underwriting assistant.
                Use ONLY the context below to answer.
                If the answer is not there, say: "I don't know".

                Context:
                {context}

                Answer:
                """
            )

            chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
            doc = Document(page_content=st.session_state['pdf_context'])
            answer = chain.run(input_documents=[doc], question=question)

            if "i don't know" in answer.lower() or len(answer.strip()) == 0:
                st.info("Kindly ask questions related to insurance only. I’m unable to answer unrelated questions. If you have an insurance query, I’ll gladly help you further.")
            else:
                st.markdown(
                    f"""
                    <div style="
                        padding: 15px;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: 500;
                        color: #fff;
                        text-align:justify;
                    ">
                        🤖 LLM ANSWER: <br> {answer}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            # No match → fixed polite response
            st.info("Kindly ask questions related to insurance only. I’m unable to answer unrelated questions. If you have an insurance query, I’ll gladly help you further.")
