from typing import Dict, Tuple

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
