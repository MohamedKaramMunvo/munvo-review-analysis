
import openai

# Set up API key
openai.api_key = "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"

'''
# Define the input sentence
input_sentence = "As a reminder, you'll be billed at the end of each calendar month for all usage during that month, as outlined on our Pricing page."

# Use the OpenAI API to generate a summary
model_engine = "text-davinci-003"
prompt = "Extract a summary of the following sentence in 3 or 4 words: " + input_sentence
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

# Print the summary
print("Summary: " + message)
'''

'''
====== EXAMPLES =======
Product arrived labeled as Jumbo Salted Peanuts...the peanuts were actually small sized unsalted. --> The product was mislabeled.
As a reminder, you'll be billed at the end of each calendar month for all usage during that month, as outlined on our Pricing page. --> You will be billed monthly for usage.
'''

def extract_keywords(text):
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"ner the following {text}",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0, # 0 --> most probable , 1 --> variable
    )

    message = completions.choices[0].text
    return message

text = "I like this product, good quality and very good shipment service. Product arrived labeled as Jumbo Salted Peanuts...the peanuts were actually small sized unsalted."
keywords = extract_keywords(text)
print(keywords)