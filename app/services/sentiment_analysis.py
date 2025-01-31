from transformers import pipeline

# Load the multilingual sentiment analysis model
pipe = pipeline("text-classification", model="tabularisai/multilingual-sentiment-analysis")

def analyze_sentiment(text):
    """
    Analyze sentiment using the Hugging Face pretrained model.
    :param text: Input text to analyze.
    :return: A dictionary with sentiment and confidence score.
    """
    result = pipe(text)[0]  # Get the first result from the pipeline
    return {
        "sentiment": result["label"],  # Sentiment label (e.g., POSITIVE, NEGATIVE, etc.)
        "confidence_score": round(result["score"], 2)  # Confidence score
    }