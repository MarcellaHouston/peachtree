import boto3
import backend.chromaDB.chroma_db as chroma
from enum import Enum
from pathlib import Path


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

    def query(self, content: str, user_id: str, rag: bool, flush=True):
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
            self.rag_retrieval(query=content, userid=user_id)

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
        results = chroma.query(
            query_text=query, check_end_timestamp=True, user_id=userid, n_results=25
        )

        summaries = [struct["verbose_summary"] for struct in results["metadatas"][0]]
        self.add_to_context("Past User Context")
        self.add_to_context("\n".join(summaries))

        details = chroma.get_static_traits(user_id=userid)
        detail_summaries = [
            struct["verbose_summary"] for struct in results["metadatas"][0]
        ]
        self.add_to_context("User Details")
        self.add_to_context("\n".join(detail_summaries))


class LLM_Client:
    class UseCase(Enum):
        GENERATE_TASKS = 1
        GENERATE_TALKING_POINTS = 2

    def __init__(
        self,
        use_case: UseCase,
        model_strength=1,
        max_tokens=4096,
        user_id: str = "Reach staff",
    ):
        self.use_case = use_case
        self.user_id = user_id
        prompts = Path(__file__).parent / prompts
        if use_case == self.UseCase.GENERATE_TASKS:
            file_path = prompts / "generate_tasks.txt"
            self.rag = True
            self.schema = [""]
        elif use_case == self.UseCase.GENERATE_TALKING_POINTS:
            file_path = prompts / "generate_talking_points.txt"
            self.rag = False
            self.schema = [
                "document",
                "verbose_summary",
                "static_trait",
                "end_timestamp",
            ]
        else:
            raise ValueError("Invalid use case for LLM Client.")
        with open(file_path, "r") as f:
            instructions = f.read()

        self.model = _LLM(
            model_strength=model_strength,
            instructions=instructions,
            max_tokens=max_tokens,
        )

    def query(self, content: str, max_retries=3):
        for _ in range(max_retries):

            response = self.model.query(
                content=content, user_id=self.user_id, rag=self.rag, flush=False
            )

            for key in self.schema:
                if key not in response:
                    print(f"Response missing key '{key}'. Retrying...")
                    print(response)
                    break

            return response
