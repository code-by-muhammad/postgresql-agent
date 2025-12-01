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

    def run(self):
        """
        Saves the configuration as a Python file with a config object
        """
        tool_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(tool_dir, "onboarding_config.py")
        config = self.model_dump(exclude_none=True)

        try:
            # Generate Python code with the config as a dictionary
            python_code = "# Auto-generated onboarding configuration\n\n"
            python_code += "config = {\n"

            for i, (key, value) in enumerate(config.items()):
                # Convert value to Python-compatible string
                if isinstance(value, bool):
                    value_str = "True" if value else "False"
                elif value is None:
                    value_str = "None"
                else:
                    value_str = json.dumps(value, ensure_ascii=False)
                
                python_code += f"    \"{key}\": {value_str}"
                if i < len(config) - 1:
                    python_code += ","
                python_code += "\n"

            python_code += "}\n"

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(python_code)

            return f"Configuration saved at: {config_path}\n\nYou can now import it with:\nfrom onboarding_config import config"
        except Exception as e:
            return f"Error writing config file: {str(e)}"


if __name__ == "__main__":
    tool = OnboardingTool(
        agent_name="PostgreSQL Analyst",
        agent_description="Runs SELECT queries to satisfy analytics requests.",
        model="gpt-5",
        enable_guardrail=True,
    )
    print(tool.run())
