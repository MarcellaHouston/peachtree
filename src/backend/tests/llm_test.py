from bedrock.llm import LLMClient
import json

client = LLMClient(LLMClient.UseCase.GENERATE_TALKING_POINTS, model_strength=3)
response, valid, retries = client.query(
    "I am trying to wake up earlier but I have chronic fatigue syndrome. Today I was able to wake up at 9am but I want to wake up at 7am. I also broke my femur today so it'll take a while to heal"
)
print(client.model.context)
for resp in response:
    print("Document: " + resp.get("document"))
    print("Verbose Summary: " + resp.get("verbose_summary"))
    print("Static Trait: " + str(resp.get("static_trait")))
    print("Impact Days: " + str(resp.get("impact_days")))
    print("End Timestamp: " + str(resp.get("end_timestamp")))
    print()
print("Valid:", valid)
print("Retries:", retries)
