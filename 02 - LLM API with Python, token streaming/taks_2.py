from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
  model="gpt-4o-mini-2024-07-18",
  max_tokens=100,
  messages=[
    {"role": "developer", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is AI.!"}
  ]
)

print(completion.choices[0].message.content)