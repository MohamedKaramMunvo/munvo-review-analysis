from flair.models import TextClassifier
from flair.data import Sentence
sia = TextClassifier.load('en-sentiment')

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
        return ('Error',0)

#sentence = "i received the product today, it seems easy and good for use "
#print(predictEmotion(sentence))