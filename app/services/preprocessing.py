import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk

# Download necessary NLTK resources
nltk.download("punkt")
nltk.download("wordnet")
nltk.download("stopwords")

class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words("english"))
        self.lemmatizer = WordNetLemmatizer()

    def preprocess_text(self, text):
        """
        Preprocess the input text for emotion analysis.
        :param text: Raw journal entry.
        :return: Cleaned and preprocessed text.
        """
        # Step 1: Lowercase the text
        text = text.lower()

        # Step 2: Remove punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))

        # Step 3: Remove numbers
        text = re.sub(r'\d+', '', text)

        # Step 4: Tokenize text
        tokens = word_tokenize(text)

        # Step 5: Handle negations (e.g., "not happy" -> "not_happy")
        tokens = self._handle_negations(tokens)

        # Step 6: Remove stopwords
        filtered_tokens = [word for word in tokens if word not in self.stop_words]

        # Step 7: Lemmatize words
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in filtered_tokens]

        # Step 8: Reconstruct the text
        cleaned_text = " ".join(lemmatized_tokens)

        # Step 9: Remove excess whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        return cleaned_text

    def _handle_negations(self, tokens):
        """
        Handle negations in the text by combining negation words with the following word.
        :param tokens: List of tokens.
        :return: List of tokens with handled negations.
        """
        negations = {"not", "no", "never", "n't"}
        processed_tokens = []
        skip_next = False

        for i in range(len(tokens)):
            if skip_next:
                skip_next = False
                continue

            if tokens[i] in negations and i + 1 < len(tokens):
                # Combine negation with the next word (e.g., "not happy" -> "not_happy")
                processed_tokens.append(f"{tokens[i]}_{tokens[i + 1]}")
                skip_next = True
            else:
                processed_tokens.append(tokens[i])

        return processed_tokens

# Utility function for preprocessing
def preprocess(text):
    preprocessor = TextPreprocessor()
    return preprocessor.preprocess_text(text)
