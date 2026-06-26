"""AWS Bedrock service with comprehensive logging and retry logic."""
import asyncio
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger, bedrock_logger
from app.db.models import BedrockCallLog

logger = get_logger("bedrock_service")


class BedrockRateLimitError(Exception):
    """Raised when Bedrock rate limit is hit."""
    pass


class BedrockService:
    """AWS Bedrock service with logging and rate limiting."""
    
    def __init__(self):
        self.config = Config(
            region_name=settings.AWS_REGION,
            retries={
                'max_attempts': settings.BEDROCK_MAX_RETRIES,
                'mode': 'adaptive'
            },
            read_timeout=settings.BEDROCK_REQUEST_TIMEOUT,
            connect_timeout=10
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=self.config
        )
        
        self.model_id = settings.AWS_BEDROCK_MODEL_ID
        self._semaphore = asyncio.Semaphore(settings.BEDROCK_MAX_CONCURRENT_REQUESTS)
        
    @retry(
        retry=retry_if_exception_type(BedrockRateLimitError),
        stop=stop_after_attempt(settings.BEDROCK_MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.BEDROCK_RETRY_DELAY, min=1, max=10)
    )
    async def invoke_model(
        self,
        prompt: str,
        agent_name: str,
        review_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Nova Pro model with comprehensive logging.
        
        Args:
            prompt: The user prompt to send
            agent_name: Name of the agent making the call
            review_id: Optional review ID for tracking
            db: Optional database session for logging
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Model temperature
            top_p: Top-p sampling parameter
            
        Returns:
            Dict containing the model response and metadata
        """
        async with self._semaphore:
            start_time = time.time()
            
            # Build the request payload for Nova Pro
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            
            request_payload = {
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p,
                }
            }
            
            if system_prompt:
                request_payload["system"] = [{"text": system_prompt}]
            
            # Log request start
            log_metadata = bedrock_logger.log_request(
                agent_name=agent_name,
                model_id=self.model_id,
                request_payload=request_payload,
                review_id=review_id
            )
            
            try:
                # Make the API call in a thread pool to not block
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(request_payload),
                        contentType="application/json",
                        accept="application/json"
                    )
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                # Calculate metrics
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract token usage from response
                usage = response_body.get("usage", {})
                input_tokens = usage.get("inputTokens", 0)
                output_tokens = usage.get("outputTokens", 0)
                
                # Extract the actual response text
                output_content = response_body.get("output", {}).get("message", {}).get("content", [])
                response_text = ""
                if output_content:
                    response_text = output_content[0].get("text", "")
                
                # Log successful response
                bedrock_logger.log_response(
                    metadata=log_metadata,
                    response_payload={"text_length": len(response_text)},
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    success=True
                )
                
                # Save to database if session provided
                if db and review_id:
                    await self._save_call_log(
                        db=db,
                        agent_name=agent_name,
                        review_id=review_id,
                        request_payload=request_payload,
                        response_payload={"text": response_text[:1000]},  # Truncate for storage
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=latency_ms,
                        success=True
                    )
                
                return {
                    "text": response_text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "latency_ms": latency_ms,
                    "model_id": self.model_id,
                    "agent_name": agent_name
                }
                
            except ClientError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = str(e)
                
                # Log failed response
                bedrock_logger.log_response(
                    metadata=log_metadata,
                    response_payload={},
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    success=False,
                    error=error_message
                )
                
                # Save error to database if session provided
                if db and review_id:
                    await self._save_call_log(
                        db=db,
                        agent_name=agent_name,
                        review_id=review_id,
                        request_payload=request_payload,
                        response_payload={},
                        input_tokens=0,
                        output_tokens=0,
                        latency_ms=latency_ms,
                        success=False,
                        error_message=error_message
                    )
                
                # Check for rate limiting
                if error_code in ['ThrottlingException', 'ServiceQuotaExceededException']:
                    logger.warning(f"Rate limited, will retry: {error_message}")
                    raise BedrockRateLimitError(error_message)
                
                raise
    
    async def _save_call_log(
        self,
        db: AsyncSession,
        agent_name: str,
        review_id: str,
        request_payload: Dict,
        response_payload: Dict,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Save Bedrock call log to database."""
        try:
            call_log = BedrockCallLog(
                agent_name=agent_name,
                model_id=self.model_id,
                review_id=review_id,
                request_payload=request_payload,
                response_payload=response_payload,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message
            )
            db.add(call_log)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to save Bedrock call log: {e}")
    
    async def health_check(self) -> bool:
        """Check if Bedrock service is accessible."""
        try:
            # Simple invoke to check connectivity
            result = await self.invoke_model(
                prompt="Respond with 'OK' only.",
                agent_name="health_check",
                max_tokens=10
            )
            return "OK" in result.get("text", "")
        except Exception as e:
            logger.error(f"Bedrock health check failed: {e}")
            return False


# Singleton instance
bedrock_service = BedrockService()
