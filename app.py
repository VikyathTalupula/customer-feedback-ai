import os, re, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
# Only your GitHub Pages site may call this API (set ALLOWED_ORIGIN on Render)
CORS(app, origins=[os.environ.get("ALLOWED_ORIGIN", "*")])

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])      # key lives only in Render's environment
MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-3.8-flash")   # same model as the notebook

# Same complaint themes as the notebook
THEMES = {
    "damaged":  r"\b(?:broken|broke|damaged|defective|torn|ripped|stained|stain|loose|faded|hole)\b",
    "delivery": r"\b(?:late|delay|delayed|delivery|shipping|tracking|lost)\b",
    "service":  r"\b(?:rude|unhelpful|ignored|refused|customer service|support)\b",
    "quality":  r"\b(?:poor quality|cheap|flimsy|thin|itchy|scratchy|stitching|seams|material)\b",
    "sizing":   r"\b(?:too small|too big|too tight|too large|wrong size|runs small|runs big|tight|baggy)\b",
    "refund":   r"\b(?:refund|money back|waste of money|overpriced|return)\b",
}

def clean_text(text):
    text = re.sub(r"[^a-z\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()

hits = {}   # simple rate limit: 5 requests per minute per visitor
def too_many(ip, limit=5, window=60):
    now = time.time()
    recent = [t for t in hits.get(ip, []) if now - t < window] + [now]
    hits[ip] = recent
    return len(recent) > limit

@app.get("/")
def health():
    return "ok"

@app.post("/generate")
def generate():
    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()
    if too_many(ip):
        return jsonify(error="Too many requests. Please wait a minute and try again."), 429

    data = request.get_json(silent=True) or {}
    review = str(data.get("review", "")).strip()
    try:
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        rating = 0
    if not review or len(review) > 1500 or rating not in (1, 2, 3, 4, 5):
        return jsonify(error="Enter a review (up to 1500 characters) and a rating from 1 to 5."), 400

    # Same rule as the notebook: apology emails are only for Critical (1-2 star) reviews
    if rating > 2:
        return jsonify(email=None, message="This review is not critical (3-5 stars), so no apology email is needed.")

    cleaned = clean_text(review)
    themes = [name for name, pattern in THEMES.items() if re.search(pattern, cleaned)]

    # Same prompt as the notebook
    prompt = f"""You are a friendly Customer Support Agent for an online clothing store.
A customer left this {rating}-star review:

"{review}"

Problems detected: {themes}

Write a short apology email (maximum 120 words) that:
- has a subject line and a greeting
- sincerely apologises and mentions the SPECIFIC problems the customer described
- offers a next step (refund, replacement or a call from our support team)
- sounds warm and human, and ends with "Customer Care Team"
Do not invent order numbers or facts that are not in the review."""

    for attempt in range(3):             # Gemini sometimes answers 503 when busy -> retry
        try:
            reply = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return jsonify(email=reply.text.strip())
        except Exception:
            time.sleep(4)
    return jsonify(error="The AI service is busy right now. Please try again in a moment."), 503
