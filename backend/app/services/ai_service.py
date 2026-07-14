class AIService:
    """Generative AI service placeholder for Azure AI Foundry integration."""

    async def analyze(self, prompt: str) -> dict:
        """Return a mock analysis payload until Azure OpenAI is connected."""
        return {
            "prompt": prompt,
            "summary": "TODO: Connect Azure AI Foundry to generate contextual business insights.",
            "suggestions": [
                "Review revenue by region",
                "Investigate top product trends",
                "Prepare a forecast scenario",
            ],
        }
