from bedrock.llm import LLMClient
import chromaDB.chroma_db as chroma
import json

test_summary = True
test_talking = True
test_chroma = False
test_tasks = True

# run file with python3 -m tests.llm_test from src/backend

if test_summary:
    print("-------------------------------")
    print("TESTING SUMMARIZATION")
    client = LLMClient(LLMClient.UseCase.SUMMARIZE_TRANSCRIPTION)
    response, valid, retries = client.query(
        "Today I woke up at 9am. I have chronic fatigue syndrome so it's hard for me to wake up early. I also broke my femur today so it'll take a while to heal. I want to wake up at 7am though."
    )
    print("Summary:", response)
    print("Valid:", valid)
    print("Retries:", retries)
    assert valid

if test_talking:
    print("-------------------------------")
    print("TESTING TALKING POINT GENERATION")
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
    assert valid

if test_chroma:
    print("-------------------------------")
    print("TESTING CHROMA DB")
    tp = chroma.query(
        "I am trying to play more baseball but I get tired during training.",
        True,
        "Reach staff",
        n_results=10,
    )[0]

    print([a["verbose_summary"] for a in tp["metadatas"]])

if test_tasks:
    print("-------------------------------")
    print("TESTING TASK GENERATION")
    client = LLMClient(LLMClient.UseCase.GENERATE_TASKS)
    body = {
        "goal_name": "Get Better Sleep",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "difficulty": "medium",
        "days_of_week": "monday,tuesday,thursday,saturday",
    }
    response, valid, retries = client.query(json.dumps(body))
    for t in response:
        print("Task: ", t["task"])
        print("Reasoning: ", t["reasoning"])
        print("Weekly Frequency: ", t["weekly_frequency"])
        print("Weight: ", t["weight"])
        print("Days of Week: ", t["days_of_week"])
        print("Start Date: ", t["start_date"])
        print("End Date: ", t["end_date"])
        print("Impetus: ", t["impetus"])
        print()

    print("Valid:", valid)
    print("Retries:", retries)
    assert valid
