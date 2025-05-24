import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def get_gemini_answer(question, context):
    prompt = f"""You are a helpful code assistant.
Use the following context to answer the question.

Context:
{context}

Question:
{question}

Answer:"""
    response = model.generate_content(prompt)
    return response.text.strip()
