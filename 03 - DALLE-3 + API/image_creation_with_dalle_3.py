from openai import OpenAI
client = OpenAI()

response = client.images.generate(
  model="dall-e-3",
  prompt="A cute elephant",
  n=1,
  size="1024x1024"
)

print(response)