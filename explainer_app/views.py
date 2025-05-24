from django.shortcuts import render, redirect
from .models import CodeFile
from .utils.code_parser import extract_code_chunks 
from .utils.vector_store import store_code_chunks
import os # Or your own
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import chromadb
import google.generativeai as genai

from django.conf import settings
genai.configure(api_key=settings.GEMINI_API_KEY)

from django.utils.timezone import localtime
import pytz

from .utils.vector_store import store_code_chunks, retrieve_relevant_chunks

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('upload_file')  # redirect to upload page after login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('login')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('login')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')


@login_required(login_url='login')

def upload_file(request): 
    if request.method == "POST" and request.FILES["file"]:
        code_file = CodeFile(file=request.FILES["file"])
        code_file.save()
        return redirect("upload_file")

    files = CodeFile.objects.all()
    kolkata_tz = pytz.timezone("Asia/Kolkata")
    for file in files:
        file.local_uploaded_at = localtime(file.uploaded_at, kolkata_tz)
        if not os.path.exists(file.file.path):
            file.delete()

    return render(request, "upload.html", {"files": files})

def parse_chunks(request):
    files = CodeFile.objects.all()
    parsed_data = []

    for code_file in files:
        file_path = code_file.file.path
        if not os.path.exists(file_path):
            code_file.delete()
            continue
        if file_path.endswith(".py"):
            chunks = extract_code_chunks(file_path)
            for chunk in chunks:
                chunk["filename"] = code_file.file.name
            store_code_chunks(chunks)  # ✅ No extra arguments now
            parsed_data.append({
                "filename": os.path.basename(file_path),
                "chunks": chunks
            })

    return render(request, "parsed_chunks.html", {"parsed_data": parsed_data})


def search_chunks(request):
    query = request.GET.get("query")
    if not query:
        return redirect("chunk_list")

    client = chromadb.Client()
    collection = client.get_collection(name="code_chunks")


    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    matched_chunks = results["documents"][0]

    # Combine top 5 code chunks as context
    combined_context = "\n\n".join(matched_chunks)

    # Create Gemini prompt
    prompt = f"""You are a code explainer assistant. 
    Use the following code context to answer the user's question.

    Context:
    {combined_context}

    Question:
    {query}

    Answer:"""

    gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    response = gemini_model.generate_content(prompt)

    return render(request, "explainer_app/search_results.html", {
        "query": query,
        "chunks": matched_chunks,
        "answer": response.text
    })

from django.http import HttpResponseRedirect
from django.urls import reverse

def delete_file(request, file_id):
    try:
        code_file = CodeFile.objects.get(id=file_id)
        if code_file.file and os.path.exists(code_file.file.path):
            os.remove(code_file.file.path)  # 🗑️ Remove file from disk
        code_file.delete()  # ❌ Remove from DB
    except CodeFile.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('upload_file'))  # 👈 Redirect back

from django.shortcuts import render
from .utils.vector_store import retrieve_relevant_chunks
from .utils.gemini_client import get_gemini_answer
import logging

logger = logging.getLogger(__name__)
files = CodeFile.objects.all()
def question_answer(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        filename = request.POST.get('filename')  # Get filename from form

        logger.info(f"Received question: {question}")
        logger.info(f"Received filename: {filename}")

        try:
            relevant_chunks = retrieve_relevant_chunks(question, filename)
            logger.info(f"Retrieved code chunks:\n{relevant_chunks}")

            answer = get_gemini_answer(question, relevant_chunks)
            logger.info(f"Gemini Response: {answer}")
        except Exception as e:
            answer = f"Internal Error: {str(e)}"
            logger.error(f"Error while processing question: {str(e)}")

        return render(request, 'qa_result.html', {
            "files": files,
            'question': question,
            'answer': answer
        })

    return render(request, 'qa_result.html', {"files": files})
