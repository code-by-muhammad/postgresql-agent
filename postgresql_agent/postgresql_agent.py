import os
from agents import ModelSettings
from agency_swarm import Agent
from openai.types.shared import Reasoning
from dotenv import load_dotenv

load_dotenv()

# Import onboarding configuration
try:
    from onboarding_config import config
except ImportError:
    raise ImportError(
        "Onboarding configuration not found. Please run 'python onboarding_tool.py' "
        "to generate the configuration file before using this agent."
    )

current_dir = os.path.dirname(os.path.abspath(__file__))


def create_postgresql_agent():

    # Build agent parameters based on model selection
    agent_params = {
        "name": config["agent_name"],
        "description": config["agent_description"],
        "instructions": "./instructions.md",
        "tools_folder": "./tools",
        "model": config.get("model", "gpt-5"),
    }

    # Conditionally add input guardrail
    if config.get("enable_guardrail", True):
        import importlib.util
        
        # Load guardrail module
        guardrail_path = os.path.join(current_dir, "input_guardrail.py")
        spec = importlib.util.spec_from_file_location("input_guardrail", guardrail_path)
        guardrail_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guardrail_module)
        
        agent_params["input_guardrails"] = [guardrail_module.relevance_guardrail]
        agent_params["throw_input_guardrail_error"] = True

    # Conditionally add model settings based on model type
    selected_model = config.get("model", "gpt-5")
    if selected_model == "gpt-5":
        # gpt-5 uses reasoning
        agent_params["model_settings"] = ModelSettings(
            reasoning=Reasoning(
                effort="low",
                summary="auto",
            ),
        )
    else:
        # gpt-4.1 uses temperature instead of reasoning
        agent_params["model_settings"] = ModelSettings(
            temperature=0.3
        )

    postgresql_agent = Agent(**agent_params)
    return postgresql_agent

