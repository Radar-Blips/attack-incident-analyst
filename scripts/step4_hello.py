from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=100,
messages=[{"role": "user", "content": "Say hello in 5 words."}],
)

##print(response.content[0].text)
print(response)
##print(response.usage)
