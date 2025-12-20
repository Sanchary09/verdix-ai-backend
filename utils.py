import joblib
import re
import tldextract
from urllib.parse import urlparse
from verification import verify_claim

# Load ML model
model = joblib.load("general_ml_model.pkl")
vectorizer = joblib.load("general_vectorizer.pkl")

def ml_predict(text):
    vec = vectorizer.transform([text])
    prob = model.predict_proba(vec)[0]
    return prob[1], prob[0]

def genome_map(text):
    t = text.lower()

    panic_words = ["urgent", "breaking", "shocking", "alert", "act now", "asap"]
    medical_words = ["covid", "vaccine", "health", "doctor", "virus", "cancer"]

    emotional = text.count("!") + text.count("?")
    caps = len(re.findall(r'\b[A-Z]{2,}\b', text))

    score = (
        sum(w in t for w in panic_words) * 3 +
        sum(w in t for w in medical_words) * 2 +
        emotional +
        caps
    )

    return {
        "panic_triggers": sum(w in t for w in panic_words),
        "medical_claims": sum(w in t for w in medical_words),
        "emotional_markers": emotional,
        "capital_word_count": caps,
        "manipulation_score": score
    }

def analyze_link(url):
    try:
        url = url.strip(".,!?)(")
        if not url.startswith("http"):
            url = "http://" + url

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        ext = tldextract.extract(url)
        main_domain = ext.registered_domain

        score = 0
        reasons = []

        if parsed.scheme != "https":
            score += 30
            reasons.append("No HTTPS")

        if re.match(r"\d+\.\d+\.\d+\.\d+", domain):
            score += 30
            reasons.append("IP-based URL")

        verdict = "High Risk" if score >= 50 else "Medium Risk" if score >= 30 else "Low Risk"

        return {
            "domain": main_domain,
            "fraud_score": score,
            "verdict": verdict,
            "reasons": reasons
        }
    except:
        return None

def virality_predictor(text):
    t = text.lower()
    urgency = sum(w in t for w in ["urgent", "breaking", "alert"])
    punctuation = text.count("!") + text.count("?")
    hashtags = len(re.findall(r"#\w+", text))

    score = urgency * 20 + punctuation * 5 + hashtags * 10

    return {
        "virality_score": min(100, score),
        "risk": "High" if score > 60 else "Medium" if score > 30 else "Low"
    }

def check_fake_news(text: str):
    real_p, fake_p = ml_predict(text)
    ml_status = "Real" if real_p > fake_p else "Fake"
    base_conf = int(max(real_p, fake_p) * 100)

    urls = re.findall(r'((?:https?://|www\.)[^\s]+)', text)
    link_info = analyze_link(urls[0]) if urls else None

    # 🔍 Always call SerpAPI verification
    verification = verify_claim(text, ml_status)

    # 🔥 FINAL STATUS COMES FROM VERIFICATION (NOT JUST SOURCE EXISTENCE)
    if verification and "verdict" in verification:
        final_status = verification["verdict"]

        if final_status == "Real":
            confidence = min(95, base_conf + 20)

        elif final_status == "Fake":
            confidence = min(98, base_conf + 15)

        else:  # Unverified
            confidence = max(40, base_conf - 20)

    else:
        # Fallback (should rarely happen)
        final_status = ml_status
        confidence = base_conf

    return {
        "status": final_status,
        "confidence": confidence,
        "genome_map": genome_map(text),
        "link_report": link_info,
        "virality": virality_predictor(text),
        "verification": verification   # ALWAYS RETURN
    }