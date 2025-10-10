"""LLM integration tools for testing prompts.

This module provides tools for executing prompts with an LLM to test
the full workflow of prompt retrieval, rendering, and execution.
"""

import json
import logging
import os
import re
import time
from typing import Any

import httpx

from ..connection import ConnectionError, ConnectionManager

logger = logging.getLogger(__name__)


async def execute_prompt_with_llm(
    prompt_name: str,
    prompt_arguments: dict[str, Any] | None = None,
    fill_variables: dict[str, Any] | None = None,
    llm_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a prompt with an LLM and return the response.

    This tool performs the complete workflow:
    1. Retrieves the prompt from the connected MCP server with prompt_arguments
    2. Optionally fills template variables in the prompt messages
    3. Sends the prompt messages to an LLM
    4. Returns the LLM's response along with metadata

    Supports two prompt patterns:
    - Standard MCP prompts: Pass arguments via prompt_arguments, server handles substitution
    - Template variables: Use fill_variables to replace {variable} placeholders in messages

    Args:
        prompt_name: Name of the prompt to execute
        prompt_arguments: Dictionary of arguments to pass to the MCP prompt (default: {})
        fill_variables: Dictionary of template variables to fill in prompt messages (default: None)
            Used for manual string replacement of {variable_name} patterns.
            Values are JSON-serialized before substitution if they're not strings.
        llm_config: Optional LLM configuration with keys:
            - url: LLM endpoint URL (default: from LLM_URL env var)
            - model: Model name (default: from LLM_MODEL_NAME env var)
            - api_key: API key (default: from LLM_API_KEY env var)
            - max_tokens: Maximum tokens in response (default: 1000)
            - temperature: Sampling temperature (default: 0.7)

    Returns:
        Dictionary with execution results including:
        - success: True if execution succeeded
        - prompt: Original prompt information
        - llm_request: The request sent to the LLM
        - llm_response: The LLM's response
        - parsed_response: Attempted JSON parsing if response looks like JSON
        - metadata: Timing and configuration information

    Raises:
        Returns error dict for various failure scenarios:
        - not_connected: No active MCP connection
        - prompt_not_found: Prompt doesn't exist
        - llm_config_error: Missing or invalid LLM configuration
        - llm_request_error: LLM request failed
    """
    start_time = time.perf_counter()

    try:
        # Set default for prompt_arguments
        if prompt_arguments is None:
            prompt_arguments = {}

        # Verify connection exists
        client, state = ConnectionManager.require_connection()

        logger.info(
            f"Executing prompt '{prompt_name}' with LLM",
            extra={
                "prompt_name": prompt_name,
                "arguments": prompt_arguments,
                "has_fill_variables": fill_variables is not None,
            },
        )

        # Get the prompt from the MCP server
        prompt_start = time.perf_counter()
        result = await client.get_prompt(prompt_name, prompt_arguments)
        prompt_elapsed_ms = (time.perf_counter() - prompt_start) * 1000

        # Extract messages
        messages: list[dict[str, Any]] = []
        if hasattr(result, "messages") and result.messages:
            for message in result.messages:
                msg_dict: dict[str, Any] = {"role": message.role}
                # Extract content
                if hasattr(message, "content"):
                    content = message.content
                    if hasattr(content, "text"):
                        msg_dict["content"] = content.text
                    elif (
                        hasattr(content, "type")
                        and content.type == "text"
                        and hasattr(content, "text")
                    ):
                        msg_dict["content"] = content.text
                    else:
                        msg_dict["content"] = str(content)
                messages.append(msg_dict)

        # Fill template variables if provided
        if fill_variables:
            logger.debug(f"Filling template variables: {list(fill_variables.keys())}")
            for msg in messages:
                if "content" in msg and isinstance(msg["content"], str):
                    content_str = msg["content"]
                    # Fill each variable
                    for var_name, var_value in fill_variables.items():
                        placeholder = "{" + var_name + "}"
                        # Convert value to string (JSON serialize if not a string)
                        if isinstance(var_value, str):
                            replacement = var_value
                        else:
                            replacement = json.dumps(var_value, indent=2)
                        content_str = content_str.replace(placeholder, replacement)
                    msg["content"] = content_str

        # Get LLM configuration
        if llm_config is None:
            llm_config = {}

        llm_url = llm_config.get("url") or os.getenv("LLM_URL")
        llm_model = llm_config.get("model") or os.getenv("LLM_MODEL_NAME")
        llm_api_key = llm_config.get("api_key") or os.getenv("LLM_API_KEY")
        max_tokens = llm_config.get("max_tokens", 1000)
        temperature = llm_config.get("temperature", 0.7)

        if not all([llm_url, llm_model, llm_api_key]):
            return {
                "success": False,
                "error": {
                    "error_type": "llm_config_error",
                    "message": "Missing LLM configuration. Provide llm_config or set LLM_URL, LLM_MODEL_NAME, and LLM_API_KEY environment variables",
                    "details": {
                        "has_url": bool(llm_url),
                        "has_model": bool(llm_model),
                        "has_api_key": bool(llm_api_key),
                    },
                    "suggestion": "Set LLM_URL, LLM_MODEL_NAME, and LLM_API_KEY in your .env file",
                },
                "metadata": {
                    "request_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
                },
            }

        # Prepare LLM request
        llm_request = {
            "model": llm_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Send to LLM
        llm_start = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(
                f"{llm_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}",
                },
                json=llm_request,
            )

        llm_elapsed_ms = (time.perf_counter() - llm_start) * 1000
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        if response.status_code != 200:
            logger.error(
                f"LLM request failed with status {response.status_code}",
                extra={
                    "status_code": response.status_code,
                    "response_text": response.text[:500],
                },
            )
            return {
                "success": False,
                "error": {
                    "error_type": "llm_request_error",
                    "message": f"LLM request failed with status {response.status_code}",
                    "details": {
                        "status_code": response.status_code,
                        "response_text": response.text[:500],
                    },
                    "suggestion": "Check LLM endpoint configuration and API key",
                },
                "metadata": {
                    "request_time_ms": round(total_elapsed_ms, 2),
                },
            }

        # Parse LLM response
        llm_result = response.json()
        llm_response_text = llm_result["choices"][0]["message"]["content"]

        # Try to extract and parse JSON if present
        parsed_response = None
        json_match = re.search(r"```json\s*(.*?)\s*```", llm_response_text, re.DOTALL)
        if json_match:
            try:
                parsed_response = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse extracted JSON: {e}")
        elif llm_response_text.strip().startswith("{"):
            try:
                parsed_response = json.loads(llm_response_text)
            except json.JSONDecodeError:
                pass  # Not valid JSON, leave as None

        logger.info(
            f"Prompt '{prompt_name}' executed successfully with LLM",
            extra={
                "prompt_name": prompt_name,
                "prompt_ms": prompt_elapsed_ms,
                "llm_ms": llm_elapsed_ms,
                "total_ms": total_elapsed_ms,
            },
        )

        return {
            "success": True,
            "prompt": {
                "name": prompt_name,
                "arguments": prompt_arguments,
                "message_count": len(messages),
            },
            "llm_request": llm_request,
            "llm_response": {
                "text": llm_response_text,
                "usage": llm_result.get("usage", {}),
                "model": llm_result.get("model"),
            },
            "parsed_response": parsed_response,
            "metadata": {
                "prompt_retrieval_ms": round(prompt_elapsed_ms, 2),
                "llm_execution_ms": round(llm_elapsed_ms, 2),
                "total_time_ms": round(total_elapsed_ms, 2),
                "server_url": state.server_url,
                "llm_endpoint": llm_url,
                "llm_model": llm_model,
            },
        }

    except ConnectionError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.error(
            f"Not connected when executing prompt '{prompt_name}': {str(e)}",
            extra={"prompt_name": prompt_name, "duration_ms": elapsed_ms},
        )

        return {
            "success": False,
            "error": {
                "error_type": "not_connected",
                "message": str(e),
                "details": {"prompt_name": prompt_name},
                "suggestion": "Use connect_to_server() to establish a connection first",
            },
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Determine error type
        error_type = "execution_error"
        suggestion = "Check the prompt name, arguments, and LLM configuration"

        error_msg = str(e).lower()
        if "not found" in error_msg or "unknown prompt" in error_msg:
            error_type = "prompt_not_found"
            suggestion = f"Prompt '{prompt_name}' does not exist on the server"
        elif "timeout" in error_msg or "connection" in error_msg:
            error_type = "llm_request_error"
            suggestion = "LLM request timed out or connection failed"

        logger.error(
            f"Failed to execute prompt '{prompt_name}' with LLM: {str(e)}",
            extra={
                "prompt_name": prompt_name,
                "error_type": error_type,
                "duration_ms": elapsed_ms,
            },
        )

        ConnectionManager.increment_stat("errors")

        return {
            "success": False,
            "error": {
                "error_type": error_type,
                "message": f"Failed to execute prompt with LLM: {str(e)}",
                "details": {
                    "prompt_name": prompt_name,
                    "exception_type": type(e).__name__,
                },
                "suggestion": suggestion,
            },
            "metadata": {
                "request_time_ms": round(elapsed_ms, 2),
            },
        }
