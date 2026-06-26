"""Test Bedrock connection and model access."""
import asyncio
import json
import boto3
from botocore.config import Config

import os

# AWS Configuration — loaded from environment variables
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Model IDs to test
MODEL_IDS = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0", 
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]

def test_bedrock_connection():
    """Test connection to AWS Bedrock and list available models."""
    print("=" * 60)
    print("TESTING AWS BEDROCK CONNECTION")
    print("=" * 60)
    
    config = Config(
        region_name=AWS_REGION,
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
    
    # Test with bedrock client (for listing models)
    try:
        bedrock = boto3.client(
            'bedrock',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=config
        )
        
        print("\n✓ Connected to AWS Bedrock")
        
        # List foundation models
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        print(f"\n📋 Available Foundation Models ({len(models)} total):")
        print("-" * 50)
        
        # Filter for text models
        text_models = [m for m in models if 'TEXT' in m.get('outputModalities', [])]
        for model in text_models[:20]:  # Show first 20
            model_id = model.get('modelId', 'Unknown')
            provider = model.get('providerName', 'Unknown')
            print(f"  • {model_id} ({provider})")
        
        if len(text_models) > 20:
            print(f"  ... and {len(text_models) - 20} more")
            
    except Exception as e:
        print(f"\n✗ Failed to connect to Bedrock: {e}")
        return False
    
    # Test with bedrock-runtime client (for inference)
    try:
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            config=config
        )
        
        print("\n✓ Connected to AWS Bedrock Runtime")
        
    except Exception as e:
        print(f"\n✗ Failed to connect to Bedrock Runtime: {e}")
        return False
    
    # Test model invocation
    print("\n" + "=" * 60)
    print("TESTING MODEL INVOCATION")
    print("=" * 60)
    
    test_prompt = "Respond with exactly: 'Bedrock connection successful'"
    
    for model_id in MODEL_IDS:
        print(f"\n🔄 Testing model: {model_id}")
        
        try:
            # Build request based on model type
            if model_id.startswith("amazon.nova"):
                request_payload = {
                    "messages": [{"role": "user", "content": [{"text": test_prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": 100,
                        "temperature": 0.1,
                    }
                }
            elif model_id.startswith("anthropic.claude"):
                request_payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": test_prompt}]
                }
            else:
                print(f"   ⚠️ Unknown model format, skipping")
                continue
            
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_payload),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract response text
            if model_id.startswith("amazon.nova"):
                output = response_body.get("output", {}).get("message", {}).get("content", [])
                response_text = output[0].get("text", "") if output else ""
            elif model_id.startswith("anthropic.claude"):
                content = response_body.get("content", [])
                response_text = content[0].get("text", "") if content else ""
            else:
                response_text = str(response_body)
            
            print(f"   ✓ SUCCESS! Response: {response_text[:100]}...")
            
            # Get token usage if available
            usage = response_body.get("usage", {})
            if usage:
                print(f"   📊 Tokens - Input: {usage.get('inputTokens', 'N/A')}, Output: {usage.get('outputTokens', 'N/A')}")
            
        except Exception as e:
            error_msg = str(e)
            if "AccessDeniedException" in error_msg:
                print(f"   ✗ Access Denied - Model not enabled in your account")
            elif "ValidationException" in error_msg:
                print(f"   ✗ Validation Error - {error_msg[:100]}")
            else:
                print(f"   ✗ Error: {error_msg[:150]}")
    
    return True


def test_compliance_prompt():
    """Test a real compliance analysis prompt."""
    print("\n" + "=" * 60)
    print("TESTING COMPLIANCE ANALYSIS PROMPT")
    print("=" * 60)
    
    config = Config(region_name=AWS_REGION)
    
    bedrock_runtime = boto3.client(
        'bedrock-runtime',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        config=config
    )
    
    test_document = """
    Dear Valued Client,
    
    We are excited to offer you a GUARANTEED 25% annual return on your investment.
    This is a RISK-FREE opportunity that cannot lose money.
    
    Please wire $50,000 to our offshore account immediately.
    This offer expires in 24 hours - ACT NOW!
    
    Based on insider information, Company XYZ stock will triple next week.
    """
    
    compliance_prompt = f"""Analyze this financial document for regulatory compliance violations.

DOCUMENT:
{test_document}

Identify violations related to:
1. SEC regulations (securities fraud, misleading statements)
2. FINRA rules (suitability, fair dealing)
3. AML/KYC requirements

For each violation found, provide:
- Regulation violated
- Severity (critical/high/medium/low)  
- Specific text that violates the regulation
- Explanation of why it's a violation

Respond in JSON format:
{{
    "violations": [
        {{
            "regulation": "...",
            "severity": "...",
            "original_text": "...",
            "explanation": "..."
        }}
    ],
    "risk_score": 0-100,
    "summary": "..."
}}"""

    model_id = "amazon.nova-pro-v1:0"
    
    try:
        request_payload = {
            "messages": [{"role": "user", "content": [{"text": compliance_prompt}]}],
            "system": [{"text": "You are a compliance expert analyzing financial documents for regulatory violations. Be thorough and cite specific regulations."}],
            "inferenceConfig": {
                "maxTokens": 4096,
                "temperature": 0.1,
            }
        }
        
        print(f"\n🔄 Sending compliance analysis to {model_id}...")
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_payload),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        output = response_body.get("output", {}).get("message", {}).get("content", [])
        response_text = output[0].get("text", "") if output else ""
        
        print(f"\n✓ Analysis Complete!")
        print("-" * 50)
        print(response_text)
        print("-" * 50)
        
        usage = response_body.get("usage", {})
        print(f"\n📊 Token Usage - Input: {usage.get('inputTokens')}, Output: {usage.get('outputTokens')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests
    connection_ok = test_bedrock_connection()
    
    if connection_ok:
        test_compliance_prompt()
    
    print("\n" + "=" * 60)
    print("BEDROCK TEST COMPLETE")
    print("=" * 60)
