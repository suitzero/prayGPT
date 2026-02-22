import os
from groq import Groq
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, role: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.role = role
        self.model = model
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate_response(self, prompt: str, context: str = "") -> str:
        """
        Generates a response from the LLM based on the prompt and optional context.
        """
        try:
            full_prompt = f"Role: {self.role}\n\nContext: {context}\n\nTask: {prompt}"

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are {self.name}. {self.role}"
                    },
                    {
                        "role": "user",
                        "content": full_prompt,
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response for {self.name}: {e}")
            return f"Error: {e}"

class IdeatorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Agent A (Ideator)",
            role="You are a creative business strategist. Your goal is to generate innovative business ideas, strategies, or positive meditations on business growth."
        )

    def brainstorm(self, context: str) -> str:
        return self.generate_response(
            prompt="Generate a new business idea or strategy based on the current context. Focus on novelty and potential impact.",
            context=context
        )

class CriticAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Agent B (Critic)",
            role="You are a critical business analyst. Your goal is to review business ideas, identify potential flaws, risks, and offer practical refinements."
        )

    def critique(self, idea: str) -> str:
        return self.generate_response(
            prompt=f"Review the following business idea. Point out flaws, risks, and suggest improvements.\n\nIdea:\n{idea}",
            context=""
        )

class SynthesizerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Agent C (Synthesizer)",
            role="You are a synthesizer. Your goal is to combine business ideas and critiques into a cohesive, actionable insight. You also summarize the key takeaways."
        )

    def synthesize(self, idea: str, critique: str, history: str) -> str:
        return self.generate_response(
            prompt=f"Synthesize the following idea and critique into a refined business insight. Update the context/memory with this new insight.\n\nIdea:\n{idea}\n\nCritique:\n{critique}\n\nPrevious Context:\n{history}",
            context=""
        )
