#!/usr/bin/env python3
"""Test script to execute a weather prompt with the LLM."""

import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Weather data from Boston, MA
weather_data = {
    "location": "Boston, MA",
    "temperature": "48.2°F (9.0°C)",
    "conditions": "Clear",
    "forecast": "Clear, with a low around 39. Northwest wind around 6 mph.",
    "humidity": "42.8%",
    "wind": "9.2 mph from 330°",
    "timestamp": "2025-10-10T03:21:20.356262+00:00",
    "source": "Weather.gov"
}

# Prompt template from weather_report prompt
prompt_template = """Given the following weather data:
{weather_data}

Generate a professional weather report that includes:
- Current conditions summary in natural language
- Temperature analysis with context (e.g., "cooler than average", "typical for this time of year")
- Wind and humidity details with practical implications
- Visibility and air quality if mentioned in conditions
- Practical recommendations for outdoor activities
- Appropriate clothing suggestions

Output format: {output_format}

The report should be informative yet accessible to a general audience.
Use clear, concise language and avoid excessive technical jargon.
Include relevant safety advisories if severe conditions are present."""

# Fill in the template
filled_prompt = prompt_template.format(
    weather_data=json.dumps(weather_data, indent=2),
    output_format="JSON"
)

# Prepare LLM request
llm_url = os.getenv("LLM_URL")
llm_model = os.getenv("LLM_MODEL_NAME")
llm_api_key = os.getenv("LLM_API_KEY")

if not all([llm_url, llm_model, llm_api_key]):
    print("Error: Missing LLM configuration in .env file")
    exit(1)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {llm_api_key}"
}

payload = {
    "model": llm_model,
    "messages": [
        {
            "role": "user",
            "content": filled_prompt
        }
    ],
    "max_tokens": 1000,
    "temperature": 0.7
}

print("=" * 80)
print("WEATHER DATA:")
print("=" * 80)
print(json.dumps(weather_data, indent=2))
print()

print("=" * 80)
print("FILLED PROMPT:")
print("=" * 80)
print(filled_prompt)
print()

print("=" * 80)
print("SENDING TO LLM...")
print("=" * 80)

# Send request to LLM
response = requests.post(
    f"{llm_url}/chat/completions",
    headers=headers,
    json=payload
)

if response.status_code == 200:
    result = response.json()
    llm_response = result["choices"][0]["message"]["content"]

    print("=" * 80)
    print("LLM RESPONSE:")
    print("=" * 80)
    print(llm_response)
    print()

    # Try to parse as JSON if it looks like JSON
    if llm_response.strip().startswith("{"):
        try:
            parsed = json.loads(llm_response)
            print("=" * 80)
            print("PARSED JSON STRUCTURE:")
            print("=" * 80)
            print(json.dumps(parsed, indent=2))
            print()

            # Validate expected fields
            print("=" * 80)
            print("VALIDATION:")
            print("=" * 80)
            expected_fields = ["summary", "temperature", "conditions", "recommendations"]
            for field in expected_fields:
                if field in parsed:
                    print(f"✓ {field}: Present")
                else:
                    print(f"✗ {field}: Missing")

        except json.JSONDecodeError as e:
            print(f"Warning: Response looks like JSON but failed to parse: {e}")

    print()
    print("=" * 80)
    print("TEST RESULT: SUCCESS")
    print("=" * 80)
else:
    print(f"Error: LLM request failed with status {response.status_code}")
    print(response.text)
    print()
    print("=" * 80)
    print("TEST RESULT: FAILED")
    print("=" * 80)
