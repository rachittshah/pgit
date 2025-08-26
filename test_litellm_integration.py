#!/usr/bin/env python3
"""
Test script for pgit LiteLLM integration.

This script tests the new LiteLLM endpoints to ensure they work correctly.
"""

import os
import json
import requests
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"  # Adjust as needed
TEST_REPO = "pgit"  # Adjust to your test repository name


class PgitLiteLLMTester:
    """Test class for pgit LiteLLM integration."""
    
    def __init__(self, base_url: str, repo_name: str):
        self.base_url = base_url.rstrip('/')
        self.repo_name = repo_name
        
    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test the health check endpoint."""
        print("🏥 Testing health endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"📦 LiteLLM version: {data.get('litellm_version', 'unknown')}")
            print(f"🔌 Available providers: {', '.join(data.get('available_providers', []))}")
            
            return data
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {}
    
    def test_config_endpoint(self) -> Dict[str, Any]:
        """Test the configuration endpoint."""
        print("\n⚙️  Testing config endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/config")
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Config retrieved successfully")
            print(f"🔑 API key status:")
            
            for provider, status in data.get('api_key_status', {}).items():
                status_emoji = "✅" if status else "❌"
                print(f"    {status_emoji} {provider}: {'configured' if status else 'not configured'}")
            
            return data
            
        except Exception as e:
            print(f"❌ Config retrieval failed: {e}")
            return {}
    
    def test_models_endpoint(self) -> Dict[str, Any]:
        """Test the available models endpoint."""
        print(f"\n🤖 Testing models endpoint for repo '{self.repo_name}'...")
        
        try:
            response = requests.get(f"{self.base_url}/{self.repo_name}/models")
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Models retrieved successfully")
            print(f"📊 Total models: {data.get('total_models', 0)}")
            
            for provider, models in data.get('providers', {}).items():
                print(f"    🔌 {provider}: {', '.join(models)}")
            
            return data
            
        except Exception as e:
            print(f"❌ Models retrieval failed: {e}")
            return {}
    
    def test_inference_endpoint(self, prompt_name: str = "openai-gpt4-analysis") -> Dict[str, Any]:
        """Test the inference endpoint."""
        print(f"\n🧠 Testing inference endpoint with prompt '{prompt_name}'...")
        
        # Sample request data
        request_data = {
            "input_variables": {
                "text": "This is a great day! The weather is beautiful and I feel wonderful."
            },
            "override_settings": {
                "temperature": 0.5,
                "max_tokens": 200
            },
            "stream": False,
            "include_raw_response": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/{self.repo_name}/inference/name/{prompt_name}",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Inference successful!")
                print(f"🤖 Model: {data['metadata']['model']}")
                print(f"⏱️  Execution time: {data['metadata']['execution_time']:.2f}s")
                
                if data['metadata'].get('usage'):
                    usage = data['metadata']['usage']
                    print(f"💰 Tokens used: {usage.get('total_tokens', 'N/A')}")
                    if 'cost' in usage:
                        print(f"💵 Cost: ${usage['cost']:.4f}")
                
                print(f"📝 Response (first 200 chars): {data['response'][:200]}...")
                return data
                
            elif response.status_code == 404:
                print(f"❌ Prompt '{prompt_name}' not found")
                return {}
                
            elif response.status_code == 400:
                error_data = response.json()
                print(f"❌ Bad request: {error_data.get('detail', 'Unknown error')}")
                return {}
                
            else:
                print(f"❌ Inference failed with status {response.status_code}: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Inference request failed: {e}")
            return {}
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting pgit LiteLLM integration tests...\n")
        
        # Test health endpoint
        health_data = self.test_health_endpoint()
        
        # Test config endpoint
        config_data = self.test_config_endpoint()
        
        # Test models endpoint
        models_data = self.test_models_endpoint()
        
        # Test inference endpoint (only if we have at least one working provider)
        if config_data.get('total_providers_configured', 0) > 0:
            self.test_inference_endpoint()
        else:
            print("\n⚠️  Skipping inference test - no API keys configured")
        
        print("\n🎉 Test suite completed!")


def main():
    """Main function."""
    print("pgit LiteLLM Integration Test Suite")
    print("=" * 50)
    
    # Check if required environment variables are set
    print("🔍 Checking environment variables...")
    
    common_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    configured_keys = [key for key in common_keys if os.getenv(key)]
    
    if configured_keys:
        print(f"✅ Found API keys for: {', '.join(configured_keys)}")
    else:
        print("⚠️  No common API keys found in environment")
        print("   Set API keys in environment variables to test inference")
    
    print()
    
    # Run tests
    tester = PgitLiteLLMTester(API_BASE_URL, TEST_REPO)
    tester.run_all_tests()


if __name__ == "__main__":
    main()