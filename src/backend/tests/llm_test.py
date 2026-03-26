from bedrock.llm import LLMClient
import chromaDB.chroma_db as chroma

test_summary = False
test_talking = True

if test_summary:
    client = LLMClient(LLMClient.UseCase.SUMMARIZE_TRANSCRIPTION)
    response, valid, retries = client.query(
        "Today I woke up at 9am. I have chronic fatigue syndrome so it's hard for me to wake up early. I also broke my femur today so it'll take a while to heal. I want to wake up at 7am though."
    )
    print("Summary:", response)
    print("Valid:", valid)
    print("Retries:", retries)

if test_talking:
    client = LLMClient(LLMClient.UseCase.GENERATE_TALKING_POINTS)
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

    for resp in response:
        chroma.store_talking_point(
            user_id="Reach staff",
            document=resp.get("document"),
            verbose_summary=resp.get("verbose_summary"),
            static_trait=bool(resp.get("static_trait")),
            end_timestamp=int(resp.get("end_timestamp")),
        )
