from agents import input_guardrail, RunContextWrapper, GuardrailFunctionOutput, Runner, ModelSettings
from agency_swarm import Agent
from openai.types.shared import Reasoning
from pydantic import BaseModel

# Get config for company context
try:
    from onboarding_config import config
except ImportError:
    config = {}

# Define output type for the guardrail agent
class RelevanceCheckOutput(BaseModel):
    is_relevant: bool
    reasoning: str


# Determine model based on user selection
selected_model = config.get("model", "gpt-5")
guardrail_model = "gpt-5-nano" if selected_model == "gpt-5" or selected_model == "gpt-5.1" else "gpt-4o-mini"

# Build guardrail agent parameters
guardrail_params = {
    "name": "Relevance Checker",
    "instructions": """You verify that every user request is strictly a read-only PostgreSQL query.

Focus on allowing SELECT/CTE/VALUES/EXPLAIN statements that retrieve data without modifying it.

IMPORTANT RULES:
1. Classify as IRRELEVANT (is_relevant: false) if the request attempts INSERT, UPDATE, DELETE, DDL, administrative commands, or any instruction that changes data or schema.
2. Classify as RELEVANT (is_relevant: true) if the request is clearly read-only, asks to inspect schemas/tables, or is a follow-up clarification about a safe query.
3. When uncertain, favor RELEVANT only if the request can be reasonably satisfied with a read-only statement.

Always return the classification along with a one-sentence rationale.""",
    "output_type": RelevanceCheckOutput,
    "model": guardrail_model,
}

# Add reasoning for gpt-5-nano
if selected_model == "gpt-5" or selected_model == "gpt-5.1":
    guardrail_params["model_settings"] = ModelSettings(
        reasoning=Reasoning(
            effort="low",
            summary="auto",
        ),
    )

# Create guardrail agent with structured output
guardrail_agent = Agent(**guardrail_params)

@input_guardrail
async def relevance_guardrail(
    context: RunContextWrapper, 
    agent: Agent, 
    user_input: str | list[str]
) -> GuardrailFunctionOutput:
    """
    Validates that user input can be satisfied with read-only PostgreSQL operations.
    Only triggers if the request attempts a write, DDL, or administrative action.
    """
    
    try:
        # Run the guardrail agent to classify the input
        result = await Runner.run(guardrail_agent, user_input, context=context.context)
        
        # Check if the input is irrelevant
        if not result.final_output.is_relevant:
            return GuardrailFunctionOutput(
                output_info=(
                    "This agent can only run read-only PostgreSQL queries. "
                    "Please rephrase your request as a SELECT/CTE/VALUES statement."
                ),
                tripwire_triggered=True,
            )
        
        # Input is relevant, allow it through
        return GuardrailFunctionOutput(
            output_info="",
            tripwire_triggered=False,
        )
        
    except Exception as e:
        # If classification fails, allow the message through (fail open)
        print(f"Warning: Guardrail classification failed: {str(e)}")
        return GuardrailFunctionOutput(
            output_info="",
            tripwire_triggered=False,
        )
