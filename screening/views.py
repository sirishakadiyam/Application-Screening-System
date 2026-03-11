from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .nlp_engine import (
    extract_text_from_resume,
    semantic_similarity,
    improvement_suggestions,
)


def index(request):
    return render(request, "index.html")


@require_POST
@csrf_exempt  # For demo. In production, remove and use CSRF token in JS.
def analyze(request):
    try:
        job_desc = request.POST.get("job_description", "").strip()
        resume_file = request.FILES.get("resume")

        if not job_desc:
            return JsonResponse({"error": "Job description is required."}, status=400)
        if not resume_file:
            return JsonResponse({"error": "Resume file is required (PDF/DOCX/TXT)."}, status=400)

        resume_text = extract_text_from_resume(resume_file)

        score = semantic_similarity(job_desc, resume_text)
        improvements = improvement_suggestions(job_desc, resume_text)

        return JsonResponse({
            "similarity_score": score,
            "improvements": improvements,
        })

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception:
        return JsonResponse({"error": "Something went wrong while analyzing."}, status=500)
