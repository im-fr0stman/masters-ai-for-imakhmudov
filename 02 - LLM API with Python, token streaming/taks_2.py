from openai import OpenAI
client = OpenAI()

with open("lesson-1-transcript.txt", "r") as file:
  file_content = file.read()
user_request = f"Write a blogpost the lecture based on this content:\n{file_content}"
completion = client.chat.completions.create(
  model="gpt-4o-mini-2024-07-18",
  max_tokens=100,
  messages=[
    {"role": "developer", "content": "You are a helpful assistant."},
    {"role": "user", "content": file_content}
  ]
)

print(completion.choices[0].message.content)