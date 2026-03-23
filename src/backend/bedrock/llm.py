import boto3

class LLM:
    def __init__(self, model_strength=1, max_tokens=1024,
        instructions="You are a social accountability app that helps users create and achieve their goals."):
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

    def query(self, content, flush=True):
        """Queries the LLM"""
        if not content or not content.strip():
            return "How can Reach Help?"

        prev_conv_head = "Previous Conversation:" if self.previous_conversation else ""
        full_user_input = "\n".join([] + "Context:" + self.context + prev_conv_head +
            self.previous_conversation + "Query:" + content)
        
        try:
            response = self.client.converse(
                modelId=self.model_id,
                # Pass the system instructions into the system field
                system=[{"text": self.system_instructions}], 
                # Put user input into messages field
                messages=[{
                    "role": "user",
                    "content": [{"text": full_user_input}]
                }],
                inferenceConfig={
                    "maxTokens": self.max_tokens,
                    "temperature": 0.7
                }
            )
        except Exception as e:
            return f"Error: {str(e)}"
        
        output = response["output"]["message"]["content"][0]["text"]

        # If flush variable set to True, wipe the context
        if flush:
            self.context = []
            self.previous_conversation = []
        # Otherwise append the content to the context
        else:
            self.previous_conversation.append("Human Query: " + content)
            self.previous_conversation.append("LLM Response: " + output)

        return output