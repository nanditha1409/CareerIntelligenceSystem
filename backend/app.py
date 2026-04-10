from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import os
from utils import DOMAIN_DATA, DOMAIN_SKILLS, DOMAIN_QUESTIONS, SKILL_ALIASES

app = FastAPI()

# ----------- CORS -----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- LOAD MODEL -----------
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")
model = joblib.load(MODEL_PATH)

# MUST match training dataset
skills_list = [
    "python","sql","ml","html","css","js","docker","linux",
    "figma","react","node","java","dsa","aws","excel","powerbi",
    "tensorflow","networking","security"
]

# ----------- HELPERS -----------
def normalize_skills(user_skills):
    normalized = []

    for skill in user_skills:
        skill = skill.strip().lower()

        if skill in SKILL_ALIASES:
            normalized.append(SKILL_ALIASES[skill])
        else:
            normalized.append(skill)

    return normalized


# ----------- HOME -----------
@app.get("/")
def home():
    return {"message": "Career Intelligence API is running"}


# ----------- GET QUESTIONS -----------
@app.get("/get-questions/{domain}")
def get_questions(domain: str):
    domain = domain.strip()
    domain = domain.replace("-", "/")  # fix mismatch

    return {"questions": DOMAIN_QUESTIONS.get(domain, [])}


# ----------- RECOMMEND CAREER -----------
@app.post("/recommend-career")
def recommend(data: dict):

    user_skills = normalize_skills(data["skills"])

    input_vector = [1 if skill in user_skills else 0 for skill in skills_list]

    probs = model.predict_proba([input_vector])[0]
    classes = model.classes_

    top_indices = probs.argsort()[-3:][::-1]

    recommendations = []

    for i in top_indices:
        domain = classes[i]
        required_skills = DOMAIN_SKILLS[domain]

        matched_skills = list(set(user_skills) & set(required_skills))
        reason = [f"You know {skill.upper()}" for skill in matched_skills]

        recommendations.append({
            "domain": domain,
            "confidence": round(probs[i] * 100, 2),
            "salary": DOMAIN_DATA[domain]["salary"],
            "demand": DOMAIN_DATA[domain]["demand"],
            "reason": reason
        })

    return {"recommendations": recommendations}


# ----------- EVALUATE TEST -----------
@app.post("/evaluate-test")
def evaluate_test(data: dict):
    domain = data["domain"]
    user_answers = data["answers"]

    questions = DOMAIN_QUESTIONS.get(domain, [])

    correct = 0
    weak_areas = []

    for i, q in enumerate(questions):
        if i < len(user_answers) and user_answers[i] == q["answer"]:
            correct += 1
        else:
            weak_areas.append(q["question"])

    score = int((correct / len(questions)) * 100) if questions else 0

    if score >= 80:
        feedback = "Excellent! You are job-ready 🚀"
    elif score >= 50:
        feedback = "Good, but you need improvement."
    else:
        feedback = "You need to strengthen your fundamentals."

    return {
        "score": score,
        "feedback": feedback,
        "weak_areas": weak_areas[:3]
    }