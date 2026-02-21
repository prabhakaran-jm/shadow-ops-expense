"""Bedrock runtime client for Amazon Nova 2 Lite (real inference)."""

import json

import boto3
from botocore.config import Config

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Reasonable timeouts for inference (Nova can take a few minutes for long outputs)
CONNECT_TIMEOUT = 120
READ_TIMEOUT = 300


def get_bedrock_runtime_client():
    """Return boto3 bedrock-runtime client for settings.aws_region."""
    config = Config(
        connect_timeout=CONNECT_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        retries={"max_attempts": 2, "mode": "standard"},
    )
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        config=config,
    )


def call_nova_2_lite(prompt: str) -> str:
    """
    Invoke Nova 2 Lite via Bedrock Messages API; return only the model text output.

    Uses settings.nova_model_id_lite and settings.aws_region.
    On-demand serverless invocation; no inference profile required.
    Raises on AWS/boto errors; does not log prompt or response content.
    """
    client = get_bedrock_runtime_client()
    model_id = settings.nova_model_id_lite
    payload = {
        "messages": [
            {"role": "user", "content": [{"text": prompt}]},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    logger.info("nova_invoke_start", model_id=model_id, region=settings.aws_region)
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    response_json = json.loads(response["body"].read().decode("utf-8"))
    try:
        text = response_json["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        text = ""
    if not text.strip():
        logger.warning("nova_invoke_empty_output")
    else:
        logger.info("nova_invoke_success", output_length=len(text))
    return text
