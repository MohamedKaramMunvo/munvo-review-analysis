import openai

openai.api_key = "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"

def response(text):
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"classify the intention of {text} in the following choices (asking for contact,asking for features,others)",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7, # 0 --> most probable , 1 --> variable
    )

    message = completions.choices[0].text
    return message


print(response("hey"))