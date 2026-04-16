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

        # Construct message using user-input, context, and retry feedback.
        # Validation errors are appended to previous_conversation by LLMClient;
        # include them here so retry attempts can actually correct themselves.
        message_parts = []
        if self.context:
            message_parts.append("Context:\n" + "\n".join(self.context))
        if self.previous_conversation:
            message_parts.append(
                "Previous invalid attempt and validation feedback:\n"
                + "\n".join(self.previous_conversation)
            )
        message_parts.append("Query:\n" + content)
        full_message = "\n\n".join(message_parts)

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
        GENERATE_WEEKLY_SUGGESTIONS = 4
        GENERATE_GUIDANCE_SUGGESTIONS = 5
        EXTRACT_SEMANTICS = 6
        EXTRACT_GOAL_CONTENT = 7

    def __init__(
        self,
        use_case: UseCase,
        max_tokens=8192,
        user_id: str = "Reach staff",
    ):
        self.files = {
            self.UseCase.GENERATE_TASKS: "generate_tasks.txt",
            self.UseCase.GENERATE_TALKING_POINTS: "generate_talking_points.txt",
            self.UseCase.SUMMARIZE_TRANSCRIPTION: "summarize_transcription.txt",
            self.UseCase.GENERATE_WEEKLY_SUGGESTIONS: "generate_weekly_suggestions.txt",
            self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS: "generate_guidance_suggestions.txt",
            self.UseCase.EXTRACT_SEMANTICS: "extract_semantics.txt",
            self.UseCase.EXTRACT_GOAL_CONTENT: "extract_goal_content.txt",
        }

        self.use_case = use_case
        self.user_id = user_id

        model_strength = {
            self.UseCase.GENERATE_TASKS: 3,
            self.UseCase.GENERATE_TALKING_POINTS: 3,
            self.UseCase.SUMMARIZE_TRANSCRIPTION: 2,
            self.UseCase.GENERATE_WEEKLY_SUGGESTIONS: 3,
            self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS: 3,
            self.UseCase.EXTRACT_SEMANTICS: 2,
            self.UseCase.EXTRACT_GOAL_CONTENT: 2,
        }[self.use_case]

        prompts = Path(__file__).parent / "prompts"
        match use_case:
            case self.UseCase.GENERATE_TASKS:
                file_path = prompts / self.files[self.UseCase.GENERATE_TASKS]
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
                    "difficulty_score",
                ]
            case self.UseCase.GENERATE_TALKING_POINTS:
                file_path = prompts / self.files[self.UseCase.GENERATE_TALKING_POINTS]
                self.rag = False
                self.schema = [
                    "document",
                    "verbose_summary",
                    "static_trait",
                    "impact_days",
                ]
            case self.UseCase.SUMMARIZE_TRANSCRIPTION:
                file_path = prompts / self.files[self.UseCase.SUMMARIZE_TRANSCRIPTION]
                self.rag = False
                self.schema = []
            case self.UseCase.GENERATE_WEEKLY_SUGGESTIONS:
                file_path = (
                    prompts / self.files[self.UseCase.GENERATE_WEEKLY_SUGGESTIONS]
                )
                self.rag = False
                self.schema = [
                    "changes_summary",
                    "suggested_changes",
                    "weekly_summary",
                    "changes_title",
                ]
            case self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS:
                file_path = (
                    prompts / self.files[self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS]
                )
                self.rag = True
                self.schema = ["changes_summary", "suggested_changes"]
            case self.UseCase.EXTRACT_SEMANTICS:
                file_path = prompts / self.files[self.UseCase.EXTRACT_SEMANTICS]
                self.rag = False
                self.schema = ["semantic", "summary"]
            case self.UseCase.EXTRACT_GOAL_CONTENT:
                file_path = prompts / self.files[self.UseCase.EXTRACT_GOAL_CONTENT]
                self.rag = False
                self.schema = []
            case _:
                raise ValueError("Invalid use case specified for LLMClient.")

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
            self.UseCase.GENERATE_WEEKLY_SUGGESTIONS,
            self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS,
            self.UseCase.EXTRACT_GOAL_CONTENT,
        ]:
            self.context("Today's date: " + time.strftime("%Y-%m-%d"))
        for _ in range(max_retries):
            valid = True
            rag_query = ""
            if self.use_case in [
                self.UseCase.GENERATE_TASKS,
                self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS,
            ]:
                rag_query = loads(content).get("goal_name")

            response = self.model.query(
                content=content,
                user_id=self.user_id,
                rag=self.rag,
                flush=False,
                rag_query=rag_query,
            )

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

            if self.use_case in [
                self.UseCase.GENERATE_WEEKLY_SUGGESTIONS,
                self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS,
                self.UseCase.EXTRACT_GOAL_CONTENT,
                self.UseCase.EXTRACT_SEMANTICS,
            ]:
                try:
                    json_response = loads(response)
                    assert isinstance(json_response, dict)
                except Exception as e:
                    print(
                        f"Failed to parse response as JSON dict: {str(e)}. Response was: {response}"
                    )
                    valid = False
                    self.model.previous_conversation.append(
                        "Error: The previous response was not a valid JSON object. Please provide a new response that is a valid JSON object and adheres to the schema."
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
                                + ", and start_date must be before end_date. Do not set end_date equal to start_date; choose an end_date at least one day after start_date."
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

                        # validate weekly_frequency is between 1 and length of days_of_week
                        weekly_frequency = json_obj["weekly_frequency"]
                        if (
                            not isinstance(weekly_frequency, int)
                            or weekly_frequency < 1
                            or weekly_frequency > len(days_of_week)
                        ):
                            print(
                                f"Invalid weekly_frequency value: {weekly_frequency}. Must be an integer between 1 and the number of days in days_of_week ({len(days_of_week)})."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid weekly_frequency value. Please provide a new response with weekly_frequency as an integer between 1 and the number of days in days_of_week ("
                                + str(len(days_of_week))
                                + ")."
                            )

                        # validate difficulty_score is between 1 and 100, inclusive
                        difficulty_score = json_obj.get("difficulty_score")
                        if difficulty_score is not None and (
                            not isinstance(difficulty_score, int)
                            or difficulty_score < 1
                            or difficulty_score > 100
                        ):
                            print(
                                f"Invalid difficulty_score value: {difficulty_score}. Must be an integer between 1 and 100."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid difficulty_score value. Please provide a new response with difficulty_score as an integer between 1 and 100."
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

                case (
                    self.UseCase.GENERATE_WEEKLY_SUGGESTIONS
                    | self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS
                ):
                    output = json_response

                    missing_keys = []
                    for key in self.schema:
                        if key not in json_response:
                            print(f"Response missing key '{key}'.")
                            missing_keys.append(key)
                            valid = False

                    if missing_keys:
                        self.model.previous_conversation.append(
                            "Error: The previous response was invalid because it was missing the following keys: "
                            + ", ".join(missing_keys)
                            + ". Please provide a new response that includes these keys."
                        )
                        continue

                    if not isinstance(json_response["suggested_changes"], list):
                        print(
                            "Invalid suggested_changes value: suggested_changes must be a list."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid suggested_changes value. Please provide suggested_changes as a list."
                        )
                        continue
                    if not isinstance(json_response["changes_summary"], str):
                        print(
                            "Invalid changes_summary value: changes_summary must be a string."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid changes_summary value. Please provide changes_summary as a string."
                        )
                        continue
                    if (
                        self.use_case == self.UseCase.GENERATE_WEEKLY_SUGGESTIONS
                        and not isinstance(json_response["weekly_summary"], str)
                    ):
                        print(
                            "Invalid weekly_summary value: weekly_summary must be a string."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid weekly_summary value. Please provide weekly_summary as a string."
                        )
                        continue
                    if (
                        self.use_case == self.UseCase.GENERATE_WEEKLY_SUGGESTIONS
                        and not isinstance(json_response["changes_title"], str)
                    ):
                        print(
                            "Invalid changes_title value: changes_title must be a string."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid changes_title value. Please provide changes_title as a string."
                        )
                        continue

                    allowed_changes = ["name", "end_date", "difficulty", "days_of_week"]
                    allowed_change_keys = allowed_changes + ["goal_id", "summary"]

                    # check changes in allowed_changes
                    for change in json_response["suggested_changes"]:
                        if not isinstance(change, dict):
                            print(
                                "Invalid suggested change value: each suggested change must be an object."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid suggested change. Please provide each suggested change as a JSON object."
                            )
                            continue
                        for key in change:
                            if key not in allowed_change_keys:
                                print(
                                    f"Invalid suggested change key: {key}. Must be one of the following: {', '.join(allowed_change_keys)}."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: The previous response had an invalid suggested change key. Please provide a new response with suggested changes that only use goal_id, summary, name, end_date, difficulty, and days_of_week."
                                )
                        change_set = set(change)

                        if "end_date" in change_set:
                            # validate is in YYYY-MM-DD format
                            try:
                                time.strptime(change["end_date"], "%Y-%m-%d")
                            except Exception as e:
                                print(e)
                                print(
                                    f"Invalid end_date value: {change['end_date']}. Must be in YYYY-MM-DD format."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: The previous response had an invalid end_date value in the suggested changes. Please provide a new response with end_date in YYYY-MM-DD format."
                                )
                        if "difficulty" in change_set:
                            # validate is one of "easy", "average", "hard"
                            if change["difficulty"] not in ["easy", "average", "hard"]:
                                print(
                                    f"Invalid difficulty value: {change['difficulty']}. Must be one of the following: easy, average, hard."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: The previous response had an invalid difficulty value in the suggested changes. Please provide a new response with difficulty as one of the following: easy, average, hard."
                                )
                        if "days_of_week" in change_set:
                            # validate is a comma separated list of days of the week
                            days = change["days_of_week"].split(",")
                            valid_days = {
                                "monday",
                                "tuesday",
                                "wednesday",
                                "thursday",
                                "friday",
                                "saturday",
                                "sunday",
                            }
                            if not set(days).issubset(valid_days):
                                print(
                                    f"Invalid days_of_week value: {change['days_of_week']}. Must be a comma separated list of days of the week."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: The previous response had an invalid days_of_week value in the suggested changes. Please provide a new response with days_of_week as a comma separated list of days of the week."
                                )
                        # assert name not empty
                        if "name" in change_set and not change["name"].strip():
                            print("Invalid name value: name cannot be empty.")
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: The previous response had an invalid name value in the suggested changes. Please provide a new response with a non-empty name."
                            )

                    if self.use_case == self.UseCase.GENERATE_GUIDANCE_SUGGESTIONS:
                        for change in json_response["suggested_changes"]:
                            # only one of allowed_changes
                            intersection = set(change) & set(allowed_changes)
                            if len(intersection) != 1:
                                print(
                                    f"Invalid suggested change keys: {', '.join(change.keys())}. Each suggested change must have exactly one key that is one of the following: {', '.join(allowed_changes)}."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: The previous response had invalid suggested change keys. Please provide a new response with suggested changes that each have exactly one key that is from the following list: name, end_date, difficulty, days_of_week."
                                )

                    # check summary not empty
                    if (
                        self.use_case == self.UseCase.GENERATE_WEEKLY_SUGGESTIONS
                        and not json_response["weekly_summary"].strip()
                    ):
                        print(
                            "Invalid weekly_summary value: weekly_summary cannot be empty."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid weekly_summary value. Please provide a new response with a non-empty weekly_summary."
                        )
                    if (
                        self.use_case == self.UseCase.GENERATE_WEEKLY_SUGGESTIONS
                        and not json_response["changes_title"].strip()
                    ):
                        print(
                            "Invalid changes_title value: changes_title cannot be empty."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid changes_title value. Please provide a new response with a non-empty changes_title."
                        )

                    if not json_response["changes_summary"].strip():
                        print(
                            "Invalid changes_summary value: changes_summary cannot be empty."
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid changes_summary value. Please provide a new response with a non-empty changes_summary."
                        )

                case self.UseCase.EXTRACT_SEMANTICS:
                    output = json_response

                    missing_keys = []
                    for key in self.schema:
                        if key not in json_response:
                            print(f"Response missing key '{key}'.")
                            missing_keys.append(key)
                            valid = False

                    if missing_keys:
                        self.model.previous_conversation.append(
                            "Error: The previous response was invalid because it was missing the following keys: "
                            + ", ".join(missing_keys)
                            + ". Please provide a new response that includes these keys."
                        )
                        continue

                    unexpected_keys = set(json_response.keys()) - set(self.schema)
                    if unexpected_keys:
                        print(
                            f"Unexpected keys: {unexpected_keys}. Only allowed keys are: {set(self.schema)}"
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had unexpected keys. Please provide a new response with only these allowed keys: semantic, summary."
                        )
                        continue

                    if not isinstance(json_response["semantic"], str):
                        print("Invalid semantic value: semantic must be a string.")
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid semantic value. Please provide semantic as a string."
                        )
                        continue
                    if not isinstance(json_response["summary"], str):
                        print("Invalid summary value: summary must be a string.")
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid summary value. Please provide summary as a string."
                        )
                        continue
                    if not json_response["semantic"].strip():
                        print("Invalid semantic value: semantic cannot be empty.")
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid semantic value. Please provide a non-empty semantic string."
                        )
                    if not json_response["summary"].strip():
                        print("Invalid summary value: summary cannot be empty.")
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had an invalid summary value. Please provide a non-empty summary string."
                        )

                case self.UseCase.EXTRACT_GOAL_CONTENT:
                    output = json_response

                    # Validate no unexpected keys
                    allowed_keys = {"name", "end_date", "days_of_week"}
                    unexpected = set(json_response.keys()) - allowed_keys
                    if unexpected:
                        print(
                            f"Unexpected keys: {unexpected}. Only allowed keys are: {allowed_keys}"
                        )
                        valid = False
                        self.model.previous_conversation.append(
                            "Error: The previous response had unexpected keys. Please provide a new response with only these allowed keys: name, end_date, days_of_week."
                        )

                    # Validate end_date if present
                    if "end_date" in json_response:
                        try:
                            end_date_timestamp = int(
                                time.mktime(
                                    time.strptime(json_response["end_date"], "%Y-%m-%d")
                                )
                            )
                            today_timestamp = int(
                                time.mktime(
                                    time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")
                                )
                            )
                            if end_date_timestamp < today_timestamp:
                                print(
                                    f"Invalid end_date: {json_response['end_date']} is in the past."
                                )
                                valid = False
                                self.model.previous_conversation.append(
                                    "Error: end_date must not be in the past. Today's date is "
                                    + time.strftime("%Y-%m-%d")
                                    + ". Please provide a future end_date."
                                )
                        except ValueError:
                            print(
                                f"Invalid end_date format: {json_response['end_date']}. Must be YYYY-MM-DD."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: end_date must be in YYYY-MM-DD format. Please fix the end_date."
                            )

                    # Validate days_of_week if present
                    if "days_of_week" in json_response:
                        days = json_response["days_of_week"].split(",")
                        valid_days = {
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        }
                        if not set(days).issubset(valid_days):
                            print(
                                f"Invalid days_of_week value: {json_response['days_of_week']}. Must be a comma separated list of days of the week."
                            )
                            valid = False
                            self.model.previous_conversation.append(
                                "Error: days_of_week must be a comma separated list of valid days (monday,tuesday,...,sunday). Please fix."
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
