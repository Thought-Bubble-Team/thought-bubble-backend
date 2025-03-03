from transformers import pipeline
from typing import Dict, Tuple

# Load emotion model
try:
    emotion_model = pipeline(
        "text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None
    )
except Exception as e:
    raise Exception(f"Failed to load emotion analysis model: {e}")

# Emotion Sentiment Mapping
EMOTION_SENTIMENT_MAPPING = {
    "admiration": ("positive", 0.8),
    "amusement": ("positive", 0.9),
    "anger": ("negative", 1.7),
    "annoyance": ("negative", 1.5),
    "approval": ("positive", 0.7),
    "caring": ("positive", 0.8),
    "confusion": ("neutral", 0.6),
    "curiosity": ("neutral", 0.5),
    "desire": ("positive", 0.7),
    "disappointment": ("negative", 1.6),
    "disapproval": ("negative", 1.5),
    "disgust": ("negative", 1.8),
    "embarrassment": ("negative", 1.4),
    "excitement": ("positive", 1.0),
    "fear": ("negative", 2.1),  
    "anxiety": ("negative", 2.0),  
    "gratitude": ("positive", 0.9),
    "grief": ("negative", 2.2),
    "joy": ("positive", 0.9),
    "love": ("positive", 0.9),
    "nervousness": ("negative", 1.9),  
    "optimism": ("positive", 0.55),  
    "pride": ("positive", 0.7),
    "realization": ("neutral", 0.5),
    "relief": ("positive", 0.7),
    "remorse": ("negative", 1.6),
    "sadness": ("negative", 1.8),  
    "surprise": ("neutral", 0.6),
    "neutral": ("neutral", 0.4)
}

# Functions
def analyze_emotion(text: str) -> Dict[str, float]:
    # Analyze emotions using the GoEmotions model.
    text = text.strip()
    if not text:
        return {}

    emotion_results = emotion_model(text)
    emotions = {emotion["label"]: round(emotion["score"], 2) for emotion in emotion_results[0]}
    return emotions

def adjust_sentiment(
    sentiment_result: Dict[str, float | str], emotion_scores: Dict[str, float]
) -> Dict[str, float | str]:
    # Adjust sentiment classification by incorporating emotion weights.
    positive_score = sum(
        score * weight
        for emotion, (sentiment, weight) in EMOTION_SENTIMENT_MAPPING.items()
        if sentiment == "positive" and emotion in emotion_scores
        for score in [emotion_scores[emotion]]
    )

    negative_score = sum(
        score * weight
        for emotion, (sentiment, weight) in EMOTION_SENTIMENT_MAPPING.items()
        if sentiment == "negative" and emotion in emotion_scores
        for score in [emotion_scores[emotion]]
    )

    if positive_score > negative_score:
        base_sentiment = "Positive"
    elif negative_score > positive_score:
        base_sentiment = "Negative"
    else:
        base_sentiment = "Mixed"

    overall_score = max(positive_score, negative_score)

    if base_sentiment != "Mixed":
        if overall_score > 0.7:
            nuanced_sentiment = f"Strongly {base_sentiment}"
        elif 0.4 < overall_score <= 0.7:
            nuanced_sentiment = f"Moderately {base_sentiment}"
        else:
            nuanced_sentiment = f"Slightly {base_sentiment}"
    else:
        nuanced_sentiment = "Mixed"

    sentiment_result["confidence_score"] = round((float(sentiment_result["confidence_score"]) + overall_score) / 2, 2)
    sentiment_result["sentiment"] = nuanced_sentiment
    return sentiment_result

def refine_emotion_summary(emotion_result: Dict[str, float]) -> Tuple[str, str]:
    # Generate percentage-based and human-friendly emotion summaries.
    top_emotions = sorted(emotion_result.items(), key=lambda x: x[1], reverse=True)[:3]
    percentage_summary = ", ".join([f"{emotion} ({int(score * 100)}%)" for emotion, score in top_emotions])
    human_friendly_summary = (
        f"You primarily felt {top_emotions[0][0]}, with hints of {top_emotions[1][0]} and {top_emotions[2][0]}."
    )
    return percentage_summary, human_friendly_summary

def summarize_analysis(
    sentiment_result: Dict[str, float | str], emotion_result: Dict[str, float]
) -> Dict[str, Dict[str, str] | str]:
    # Summarize emotions and sentiment into human-readable format.
    sentiment_summary = f"Your journal today was mostly {sentiment_result['sentiment'].lower()}."
    percentage_summary, human_friendly_summary = refine_emotion_summary(emotion_result)

    # Extract the strongest emotion
    strongest_emotion = max(emotion_result, key=emotion_result.get, default="unknown")
    
    return {
        "sentiment_summary": sentiment_summary,
        "emotion_summary": {
            "percentage_based": f"You expressed a mix of {percentage_summary}.",
            "human_friendly": human_friendly_summary,
        },
        "strongest_emotion": strongest_emotion,  
    }
