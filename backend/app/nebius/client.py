import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger("nebius.client")

# Tool definitions in OpenAI format supported by Nebius / Nemotron
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists files in the repository workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path (empty for root)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the entire content of a file from the repository workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Searches for a keyword, symbol, or error message across all code files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term or pattern."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Creates or updates a file in the sandbox workspace (e.g., to write a regression test).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path."
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete file content."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Executes pytest inside the isolated sandbox and returns structured pass/fail results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "Optional specific test file or directory path."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": "Replaces old buggy code in a file with fixed code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file to patch."
                    },
                    "old_snippet": {
                        "type": "string",
                        "description": "Exact snippet of code to replace."
                    },
                    "new_snippet": {
                        "type": "string",
                        "description": "Replacement snippet."
                    }
                },
                "required": ["file_path", "old_snippet", "new_snippet"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Returns the git diff showing all modifications made in the sandbox compared to the original repository.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class NebiusClient:
    def __init__(self):
        self.api_key = settings.NEBIUS_API_KEY
        self.base_url = settings.NEBIUS_BASE_URL
        self.model = settings.NEMOTRON_MODEL
        self._client = None

        if self.api_key and self.api_key != "your-nebius-api-key-here" and self.api_key != "mock_key":
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Any:
        """Call Nebius Token Factory with NVIDIA Nemotron."""
        if not self.is_configured:
            raise ValueError(
                "Nebius API key is not configured. Please provide NEBIUS_API_KEY in your environment or .env file."
            )

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message
