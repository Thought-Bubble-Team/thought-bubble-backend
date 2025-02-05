from transformers import pipeline

# Load the sentiment analysis model
sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

# Load the emotion classification model
emotion_model = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)

# Map sentiment model labels to human-readable labels
LABEL_MAPPING = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

# Emotion Weights
EMOTION_SENTIMENT_MAPPING = {
    "joy": ("positive", 1.0),         
    "gratitude": ("positive", 1.0),
    "love": ("positive", 1.0),
    "excitement": ("positive", 1.3),  
    "pride": ("positive", 1.1),       

    "sadness": ("negative", 1.2),     
    "disappointment": ("negative", 1.4),  
    "fear": ("negative", 1.1),
    "anger": ("negative", 1.3),
    "frustration": ("negative", 1.2),  

    "neutral": ("neutral", 0.8),      
    "curiosity": ("neutral", 0.6),   
    "surprise": ("neutral", 0.7)      
}

# Function to analyze sentiment in text (positive, negative, neutral)
def analyze_sentiment(text):
    """
    Analyze sentiment using a model with neutral support.
    :param text: Preprocessed text to analyze.
    :return: A dictionary with sentiment and confidence score.
    """
    if not text.strip():
        return {"sentiment": "Neutral", "confidence_score": 0.0}

    result = sentiment_model(text)[0]
    sentiment = LABEL_MAPPING.get(result["label"], "Unknown")
    confidence_score = round(result["score"], 2)

    return {
        "sentiment": sentiment,
        "confidence_score": confidence_score
    }

# Function to analyze emotions in text
def analyze_emotion(text):
    """
    Analyze emotions using the GoEmotions model.
    :param text: Preprocessed text to analyze.
    :return: A dictionary with emotion labels and their confidence scores.
    """
    if not text.strip():
        return {}

    emotion_results = emotion_model(text)
    emotions = {emotion["label"]: round(emotion["score"], 2) for emotion in emotion_results[0]}
    return emotions

def adjust_sentiment(sentiment_result, emotion_scores):
    """
    Adjust sentiment classification by incorporating fine-tuned emotion weights and generate nuanced labels.
    """
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

    # Determine adjusted sentiment
    if positive_score > negative_score:
        base_sentiment = "Positive"
    elif negative_score > positive_score:
        base_sentiment = "Negative"
    else:
        base_sentiment = "Mixed"

    # Calculate overall score for nuance
    overall_score = max(positive_score, negative_score)

    # Generate nuanced sentiment labels
    if base_sentiment != "Mixed":
        if overall_score > 0.7:
            nuanced_sentiment = f"Strongly {base_sentiment}"
        elif 0.4 < overall_score <= 0.7:
            nuanced_sentiment = f"Moderately {base_sentiment}"
        else:
            nuanced_sentiment = f"Slightly {base_sentiment}"
    else:
        nuanced_sentiment = "Mixed"

    # Adjust confidence score
    sentiment_result["confidence_score"] = round((sentiment_result["confidence_score"] + overall_score) / 2, 2)
    sentiment_result["sentiment"] = nuanced_sentiment

    return sentiment_result
