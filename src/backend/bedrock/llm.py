import boto3
import chromaDB.chroma_db as chroma
from enum import Enum
from pathlib import Path
from json import loads
import time


class _LLM:
    def __init__(
        self,
        model_strength=1,
        max_tokens=1024,
        instructions="You are a social accountability app that helps users with their goals.",
    ):
        self.client = boto3.client("bedrock-runtime", region_name="us-east-2")
        self.system_instructions = instructions
        self.context = []
        self.previous_conversation = []
        self.max_tokens = max_tokens

        # Mapping strength to Bedrock Models, higher numbers equals stronger models
        strength_map = {
            1: "google.gemma-3-4b-it",
            2: "google.gemma-3-12b-it",
            3: "google.gemma-3-27b-it",
        }
        self.model_id = strength_map.get(model_strength, strength_map[1])

    def add_to_context(self, content):
        """Appends new info to the local context list."""
        self.context.append(content)

    def query(
        self, content: str, user_id: str, rag: bool, flush=True, rag_query: str = ""
    ):
        """
        Queries the AI model through AWS Bedrock

        Args:
            content:    The textual input from the user
            user_id:    The id of the user querying the LLM
            flush: True if all data stored in the LLM's context and conversation history
                   should be erased after the query is completed.
        """

        # If user provides an empty input, return a basic message without connecting to AWS Bedrock
        if not content or not content.strip():
            return "How can Reach Help?"

        # Add RAG-relevant docs to context if rag is set to true
        if rag:
            self.rag_retrieval(query=rag_query, userid=user_id)

        # Construct message using user-input (content) along with past context if available
        if self.context:
            past_context = "\n".join(self.context)
            full_message = f"Context: {past_context}\n\nQuery: {content}"
        else:
            full_message = content

        # Format message to be accepted by AWS Bedrock's converse method
        converse_message = [{"role": "user", "content": [{"text": full_message}]}]

        # Contact the Bedrock Agent
        try:
            response = self.client.converse(
                modelId=self.model_id,
                # Pass the system instructions into the system field
                system=[{"text": self.system_instructions}],
                # Put user input into messages field
                messages=converse_message,
                inferenceConfig={"maxTokens": self.max_tokens, "temperature": 0.3},
            )

            output = response["output"]["message"]["content"][0]["text"]

            # If flush variable set to True, wipe the context and previous conversation history
            if flush:
                self.flush()
            # Otherwise append the content to the conversation history
            else:
                self.previous_conversation.append("Human Query: " + content)
                self.previous_conversation.append("LLM Response: " + output)

            return output

        except Exception as e:
            return f"Error: {str(e)}"

    def flush(self):
        self.context = []
        self.previous_conversation = []

    def rag_retrieval(self, query: str, userid: str) -> None:
        # Get relevant docs related to query from chromadb
        results, nonstatic = chroma.query(
            query_text=query, check_end_timestamp=True, user_id=userid, n_results=25
        )

        metadata = results["metadatas"]
        vs = [meta["verbose_summary"] for meta in metadata]

        nonstatic_summaries = vs[:nonstatic]
        static_summaries = vs[nonstatic:]

        self.add_to_context("Current User Context")
        self.add_to_context("\n".join(nonstatic_summaries))

        self.add_to_context("User Details")
        self.add_to_context("\n".join(static_summaries))


class LLMClient:
    class UseCase(Enum):
        GENERATE_TASKS = 1
        GENERATE_TALKING_POINTS = 2
        SUMMARIZE_TRANSCRIPTION = 3

    def __init__(
        self,
        use_case: UseCase,
        max_tokens=4096,
        user_id: str = "Reach staff",
    ):
        self.use_case = use_case
        self.user_id = user_id

        model_strength = {
            self.UseCase.GENERATE_TASKS: 3,
            self.UseCase.GENERATE_TALKING_POINTS: 3,
            self.UseCase.SUMMARIZE_TRANSCRIPTION: 2,
        }[self.use_case]

        prompts = Path(__file__).parent / "prompts"
        if use_case == self.UseCase.GENERATE_TASKS:
            file_path = prompts / "generate_tasks.txt"
            self.rag = True
            self.schema = [
                "task",
                "reasoning",
                "weekly_frequency",
                "weight",
                "days_of_week",
                "start_date",
                "end_date",
                "impetus",
            ]
        elif use_case == self.UseCase.GENERATE_TALKING_POINTS:
            file_path = prompts / "generate_talking_points.txt"
            self.rag = False
            self.schema = [
                "document",
                "verbose_summary",
                "static_trait",
                "impact_days",
            ]
        elif use_case == self.UseCase.SUMMARIZE_TRANSCRIPTION:
            file_path = prompts / "summarize_transcription.txt"
            self.rag = False
            self.schema = []

        else:
            raise ValueError("Invalid use case for LLM Client.")
        with open(file_path, "r") as f:
            instructions = f.read()

        self.model = _LLM(
            model_strength=model_strength,
            instructions=instructions,
            max_tokens=max_tokens,
        )

    def context(self, content: str):
        self.model.add_to_context(content)

    def query(self, content: str, max_retries=5):
        retries = 0
        # add today's date in yyyy-mm-dd format to the context
        if self.use_case in [
            self.UseCase.GENERATE_TASKS,
            self.UseCase.GENERATE_TALKING_POINTS,
        ]:
            self.context("Today's date: " + time.strftime("%Y-%m-%d"))
        for _ in range(max_retries):
            valid = True
            rag_query = ""
            if self.use_case == self.UseCase.GENERATE_TASKS:
                rag_query = loads(content).get("goal_name")
            response = self.model.query(
                content=content,
                user_id=self.user_id,
                rag=self.rag,
                flush=False,
                rag_query=rag_query,
            )
            if self.use_case == self.UseCase.GENERATE_TASKS:
                print("CONTEXT FOR TASK GENERATION:")
                print(self.model.context)

            # validate response is in correct JSON format
            if self.use_case in [
                self.UseCase.GENERATE_TASKS,
                self.UseCase.GENERATE_TALKING_POINTS,
            ]:
                try:
                    json_response = loads(response)
                    assert isinstance(json_response, list)
                except Exception as e:
                    print(
                        f"Failed to parse response as JSON: {str(e)}. Response was: {response}"
                    )
                    valid = False
                    self.model.previous_conversation.append(
                        "Error: The previous response was not valid JSON. Please provide a new response that is valid JSON and adheres to the schema."
                    )
                    continue

            # output validation based on use case
            match self.use_case:
                case self.UseCase.SUMMARIZE_TRANSCRIPTION:
                    output = response

                case self.UseCase.GENERATE_TASKS:
                    output = json_response

                    content_json = loads(content)
                    goal_start_date = content_json.get("start_date")
                    goal_end_date = content_json.get("end_date")
                    goal_days_of_week = set(content_json.get("days_of_week").split(","))

                    for json_obj in json_response:
                        missing_keys = []
                        for key in self.schema:
                            if key not in json_obj:
                                print(f"Response missing key '{key}'.")
                                missing_keys.append(key)
                                valid = False

                        if missing_keys:
                            print(json_obj)
                            self.model.previous_conversation.append(
                                "Error: The previous response was invalid because it was missing the following keys: "
                                + ", ".join(missing_keys)
                                + ". Please provide a new response that includes these keys."
                            )
                            continue

                        # validate days of week
                        days_of_week = set(json_obj.get("days_of_week").split(","))
                        if not days_of_week.issubset(goal_days_of_week):
                            print(
                                f"Invalid days_of_week value: {json_obj.get('days_of_week')}. Must be a subset of the goal's days_of_week: {content_json.get('days_of_week')}."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had invalid days_of_week values. Please provide a new response with days_of_week that is a subset of the goal's days_of_week: "
                                + content_json.get("days_of_week")
                                + "."
                            )

                        # validate start and end dates
                        start_date_timestamp = int(
                            time.mktime(
                                time.strptime(json_obj.get("start_date"), "%Y-%m-%d")
                            )
                        )
                        end_date_timestamp = int(
                            time.mktime(
                                time.strptime(json_obj.get("end_date"), "%Y-%m-%d")
                            )
                        )
                        goal_start_timestamp = int(
                            time.mktime(time.strptime(goal_start_date, "%Y-%m-%d"))
                        )
                        goal_end_timestamp = int(
                            time.mktime(time.strptime(goal_end_date, "%Y-%m-%d"))
                        )

                        if (
                            start_date_timestamp < goal_start_timestamp
                            or end_date_timestamp > goal_end_timestamp
                            or start_date_timestamp >= end_date_timestamp
                        ):
                            print(
                                f"Invalid start_date or end_date value: start_date={json_obj.get('start_date')}, end_date={json_obj.get('end_date')}. start_date must be >= {goal_start_date} and end_date must be <= {goal_end_date} and start_date must be before end_date."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had invalid start_date or end_date values. Please provide a new response with start_date and end_date that satisfy the following conditions: start_date must be on or after the goal's start date of "
                                + goal_start_date
                                + ", end_date must be on or before the goal's end date of "
                                + goal_end_date
                                + ", and start_date must be before end_date."
                            )

                        # validate impetus 1-5
                        impetus = json_obj["impetus"]
                        if not isinstance(impetus, int) or impetus < 1 or impetus > 5:
                            print(
                                f"Invalid impetus value: {impetus}. Must be an integer between 1 and 5."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid impetus value. Please provide a new response with impetus as an integer between 1 and 5."
                            )

                case self.UseCase.GENERATE_TALKING_POINTS:
                    output = json_response
                    for json_obj in json_response:
                        # validate keys
                        missing_keys = []
                        for key in self.schema:
                            if key not in json_obj:
                                print(f"Response missing key '{key}'.")
                                missing_keys.append(key)
                                valid = False

                        if missing_keys:
                            print(json_obj)
                            self.model.previous_conversation.append(
                                "Error: The previous response was invalid because it was missing the following keys: "
                                + ", ".join(missing_keys)
                                + ". Please provide a new response that includes these keys."
                            )
                            continue

                        # validate impact days
                        try:
                            impact_days = int(json_obj.get("impact_days"))
                            end_timestamp = int(time.time()) + impact_days * 24 * 3600
                            json_obj["end_timestamp"] = end_timestamp

                        except Exception as e:
                            print(e)
                            print(
                                f"Invalid impact_days value: {json_obj.get('impact_days')}. Must be a valid integer."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid impact_days value that was not an integer. Please provide a new response with impact_days between 3 and 80000."
                            )
                            continue

                        if impact_days <= 2 or impact_days > 80000:
                            print(
                                f"Invalid impact_days value: {impact_days}. Must be between 3 and 80000."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid impact_days value. Please provide a new response with impact_days between 3 and 80000."
                            )

            if valid:
                self.model.flush()
                return output, True, retries
            retries += 1

        return (
            f"Error: Failed to get a valid response after {max_retries} attempts.",
            False,
            retries,
        )
