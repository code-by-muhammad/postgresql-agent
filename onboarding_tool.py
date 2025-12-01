from agency_swarm.tools import BaseTool
from pydantic import Field
from dotenv import load_dotenv
from typing import Literal
import json
import os

load_dotenv()


class OnboardingTool(BaseTool):
    """
    Generates the minimal configuration needed for the PostgreSQL read-only agent.
    """

    agent_name: str = Field(
        "PostgreSQL Analyst",
        description="Name of the read-only data agent exposed to end users.",
    )
    agent_description: str = Field(
        "Answers questions by running safe, read-only SQL against PostgreSQL.",
        description="Short description that clarifies the agent's purpose.",
    )
    model: Literal["gpt-4.1", "gpt-5", 'gpt-5.1'] = Field(
        "gpt-5.1",
        description="Model to run the agent with. gpt-5, gpt-5.1 supports built-in reasoning.",
    )
    enable_guardrail: bool = Field(
        True,
        description="Keep enabled to block any write or unsafe SQL requests before they run.",
        json_schema_extra={
            "ui:widget": "checkbox",
            "ui:title": "Enforce read-only guardrail",
        },
    )

    def run(self) -> str:
        """
        Serialize the selected values into onboarding_config.py for the agent to consume.
        """
        tool_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(tool_dir, "onboarding_config.py")
        config = self.model_dump()

        json_str = json.dumps(config, indent=4)
        json_str = (
            json_str.replace(": true", ": True")
            .replace(": false", ": False")
            .replace(": null", ": None")
        )
        python_code = f"# Auto-generated onboarding configuration\n\nconfig = {json_str}\n"

        with open(config_path, "w", encoding="utf-8") as file:
            file.write(python_code)

        return (
            f"Configuration saved at: {config_path}\n\n"
            "You can now import it with:\nfrom onboarding_config import config"
        )


if __name__ == "__main__":
    tool = OnboardingTool(
        agent_name="PostgreSQL Analyst",
        agent_description="Runs SELECT queries to satisfy analytics requests.",
        model="gpt-5",
        enable_guardrail=True,
    )
    print(tool.run())
