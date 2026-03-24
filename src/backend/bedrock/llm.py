import boto3

class LLM:
    def __init__(self, model_strength=1, max_tokens=1024,
        instructions="You are a social accountability app that helps users with their goals."):
        self.client = boto3.client("bedrock-runtime", region_name="us-east-2")
        self.system_instructions = instructions
        self.context = []
        self.previous_conversation = []
        self.max_tokens = max_tokens
        
        # Mapping strength to Bedrock Models, higher numbers equals stronger models
        strength_map = {
            1: "google.gemma-3-4b-it",
            2: "google.gemma-3-12b-it",
            3: "google.gemma-3-27b-it"
        }
        self.model_id = strength_map.get(model_strength, strength_map[1])

    def add_to_context(self, content):
        """Appends new info to the local context list."""
        self.context.append(content)

    def query(self, content: str, flush=True):
        """
        Queries the AI model through AWS Bedrock

        Args:
            content:    The textual input from the user
            flush: True if all data stored in the LLM's context and conversation history
                   should be erased after the query is completed.
        """

        # If user provides an empty input, return a basic message without connecting to AWS Bedrock
        if not content or not content.strip():
            return "How can Reach Help?"

        # Construct message using user-input (content) along with past context if available
        if self.context:
            past_context = '\n'.join(self.context)
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
                inferenceConfig={
                    "maxTokens": self.max_tokens,
                    "temperature": 0.3
                }
            )

            output = response["output"]["message"]["content"][0]["text"]

            # If flush variable set to True, wipe the context and previous conversation history
            if flush:
                self.context = []
                self.previous_conversation = []
            # Otherwise append the content to the conversation history
            else:
                self.previous_conversation.append("Human Query: " + content)
                self.previous_conversation.append("LLM Response: " + output)

            return output

        except Exception as e:
            return f"Error: {str(e)}"