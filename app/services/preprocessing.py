import re
import string
import nltk
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from typing import List

# Set a writable directory for NLTK data
NLTK_DATA_PATH = "/opt/render/project/.nltk_data"
os.makedirs(NLTK_DATA_PATH, exist_ok=True)
nltk.data.path.append(NLTK_DATA_PATH)

# Ensure required NLTK datasets are downloaded
nltk.download("punkt", download_dir=NLTK_DATA_PATH)
nltk.download("stopwords", download_dir=NLTK_DATA_PATH)
nltk.download("wordnet", download_dir=NLTK_DATA_PATH)

class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

    def preprocess_text(self, text: str) -> str:
        """Preprocess the input text for sentiment analysis."""
        text = text.lower()
        text = self._remove_punctuation(text)
        text = self._remove_numbers(text)
        tokens = word_tokenize(text)
        tokens = self._handle_negations(tokens)
        tokens = self._remove_stopwords(tokens)
        tokens = self._lemmatize_words(tokens)
        cleaned_text = " ".join(tokens)
        cleaned_text = self._remove_whitespace(cleaned_text)
        return cleaned_text

    def _remove_punctuation(self, text: str) -> str:
        return text.translate(str.maketrans("", "", string.punctuation))

    def _remove_numbers(self, text: str) -> str:
        return re.sub(r"\d+", "", text)

    def _handle_negations(self, tokens: List[str]) -> List[str]:
        negations = {"not", "no", "never", "n't"}
        processed_tokens = []
        skip_next = False
        for i in range(len(tokens)):
            if skip_next:
                skip_next = False
                continue
            if tokens[i] in negations and i + 1 < len(tokens):
                processed_tokens.append(f"{tokens[i]}_{tokens[i + 1]}")
                skip_next = True
            else:
                processed_tokens.append(tokens[i])
        return processed_tokens

    def _remove_stopwords(self, tokens: List[str]) -> List[str]:
        return [word for word in tokens if word not in self.stop_words]

    def _lemmatize_words(self, tokens: List[str]) -> List[str]:
        return [self.lemmatizer.lemmatize(token) for token in tokens]

    def _remove_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()


# Utility function for preprocessing
def preprocess(text: str) -> str:
    """Utility function to preprocess text using TextPreprocessor."""
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess_text(text)
