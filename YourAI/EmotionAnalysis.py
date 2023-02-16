import re
from collections import Counter
from flair.models import TextClassifier
from flair.data import Sentence
import nltk
import openai
from nltk.corpus import stopwords

nltk.download('stopwords')
openai.api_key = "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"
sia = TextClassifier.load('en-sentiment')

'''
stopwords = [
    "a", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "if", "in", "into", "is", "it", "no", "not", "of",
    "on", "or", "such", "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with","were","them","just","very","have","from","than",
    "when"
]'''
stopwords = stopwords.words('english')


def predictEmotion(x):
    try:
        sentence = Sentence(x)
        sia.predict(sentence)
        pred = sentence.labels[0]
        score = int(float(sentence.score) * 100)
        if "POSITIVE" in str(pred):
            pred = "Positive"
        elif "NEGATIVE" in str(pred):
            pred = "Negative"
        else:
            pred = "Neutral"

        return (pred, score)
    except:
        return ('-1',0)


def predictSummary(text):

    try:
        model_engine = "text-davinci-003"
        prompt = f"Extract a very short summary of the following sentence {text}"
        completions = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5,
        )

        # Get the first completion
        message = completions.choices[0].text

        message = message.replace("\n","")

        # return result
        return message.strip()
    except:
        return '-1'


def extractKeywords(text):
    # Remove punctuation and convert text to lowercase
    text = re.sub(r'[^\w\s]', '', text).lower()

    # Split text into words
    words = text.split()

    # Remove words with less than 4 letters and stop words
    meaningful_words = [word for word in words if len(word) >= 4 and word not in stopwords]

    # Count the frequency of each word
    word_counts = Counter(meaningful_words)

    # Total number of words
    total_words = sum(word_counts.values())

    # Calculate the percentage of each word
    word_percentages = {word: count / total_words for word, count in word_counts.items()}

    # Return the top 10 words by percentage
    d = dict(sorted(word_percentages.items(), key=lambda item: item[1], reverse=True)[:10])

    words = []
    freqs = []

    for w in d:
        words.append(w)
        freqs.append(int(d[w]*10000))

    print(d)
    return words,freqs

#sentence = "i received the product today, it seems easy and good for use "
#print(predictEmotion(sentence))

