import os
import sys
import yaml
import aiofiles
import configparser
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from git import Repo
from uuid import UUID
from typing import Optional
from starlette.responses import FileResponse
from fastapi.params import Path
import litellm

# Import our new modules
from config import Config
from llm_service import LLMService
from models import (
    InferenceRequest, InferenceResponse, AvailableModelsResponse,
    ErrorResponse, HealthCheckResponse, ConfigSummaryResponse,
    validate_prompt_data, validate_input_variables
)


app = FastAPI(
    title="pgit - Prompt Management with LiteLLM",
    description="A comprehensive tool for managing and executing LLM prompts",
    version="2.0.0"
)

# Initialize configuration and services
config = Config('../ps.conf')
llm_service = LLMService()

global REPO_HOME
REPO_HOME = config.get('main', 'repo_path')


def verify_dir_is_repo(repo_path: str) -> bool:
    try:
        repo = Repo(repo_path)
        return True
    except:
        return False


def parse_yaml(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data


@app.post('/{repo_name}')
async def upload_file(repo_name: str, file: UploadFile = File(...)):
    try:
        repo_path = os.path.join(REPO_HOME, repo_name)
        if not verify_dir_is_repo(repo_path):
            raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

        file_path = os.path.join(repo_path, file.filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        repo = Repo(repo_path)
        repo.git.add([file_path])
        repo.index.commit('Add file through API')
        msg = {'filename': file.filename, 'message': 'file uploaded and committed successfully'}
        
        return msg
    
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.get('/{repo_name}/_name/{prompt_name}', responses={200: {'content': {'application/x-yaml': {}}}})
async def read_file_by_name(repo_name: str, prompt_name: str, raw: Optional[bool] = Query(None)):
    repo_path = os.path.join(REPO_HOME, repo_name)
    if not verify_dir_is_repo(repo_path):
        raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

    file_path = os.path.join(repo_path, f'{prompt_name}.yml')
    
    if os.path.exists(file_path):
        data = parse_yaml(file_path)
        
        if raw:
            return {'prompt': data.get('prompt')}
        else:
            return FileResponse(file_path, media_type='application/x-yaml')
    
    else:
        raise HTTPException(status_code=404, detail=f'File not found: {file_path}')


@app.get('/{repo_name}/_uuid/{prompt_uuid}', responses={200: {'content': {'application/x-yaml': {}}}})
async def read_file_by_uuid(repo_name: str, prompt_uuid: UUID, raw: Optional[bool] = Query(None)):
    repo_path = os.path.join(REPO_HOME, repo_name)
    if not verify_dir_is_repo(repo_path):
        raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.yml'):
                file_location = os.path.join(root, file)
                data = parse_yaml(file_location)
                
                if data.get('uuid') == str(prompt_uuid):
                    if raw:
                        return {'prompt': data.get('prompt')}
                    else:
                        return FileResponse(file_location, media_type='application/x-yaml')
    
    raise HTTPException(status_code=404, detail=f'File not found for UUID: {prompt_uuid}')


# New LiteLLM Integration Endpoints

@app.get('/health', response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        return HealthCheckResponse(
            status="healthy",
            litellm_version=litellm.__version__,
            available_providers=config.get_available_providers()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get('/config', response_model=ConfigSummaryResponse)
async def get_config_summary():
    """Get configuration summary including API key status."""
    try:
        return ConfigSummaryResponse(**config.get_llm_config_summary())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@app.get('/{repo_name}/models', response_model=AvailableModelsResponse)
async def get_available_models(repo_name: str):
    """Get available models from repository prompts."""
    try:
        repo_path = os.path.join(REPO_HOME, repo_name)
        if not verify_dir_is_repo(repo_path):
            raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

        # Collect all prompt data
        prompts_data = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.yml'):
                    file_location = os.path.join(root, file)
                    try:
                        data = parse_yaml(file_location)
                        prompts_data.append(data)
                    except Exception:
                        continue  # Skip invalid YAML files

        # Get available models
        providers = llm_service.get_available_models(prompts_data)
        
        # Build detailed model list
        models = []
        for provider, model_list in providers.items():
            for model in model_list:
                models.append({
                    "provider": provider,
                    "model": model,
                    "display_name": f"{provider.title()} {model}",
                    "api_key_available": bool(config.get_api_key(provider)),
                    "supported_features": ["chat", "completion"]  # Default features
                })

        return AvailableModelsResponse(
            providers=providers,
            models=models,
            total_models=len(models)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")


@app.post('/{repo_name}/inference/name/{prompt_name}', response_model=InferenceResponse)
async def execute_prompt_by_name(
    repo_name: str, 
    prompt_name: str, 
    request: InferenceRequest
):
    """Execute a prompt by name using LiteLLM."""
    try:
        repo_path = os.path.join(REPO_HOME, repo_name)
        if not verify_dir_is_repo(repo_path):
            raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

        # Find and load the prompt file
        file_path = os.path.join(repo_path, f'{prompt_name}.yml')
        if not os.path.exists(file_path):
            # Try to find it in subdirectories
            found_path = None
            for root, _, files in os.walk(repo_path):
                if f'{prompt_name}.yml' in files:
                    found_path = os.path.join(root, f'{prompt_name}.yml')
                    break
            
            if not found_path:
                raise HTTPException(status_code=404, detail=f'Prompt not found: {prompt_name}')
            file_path = found_path

        # Load and validate prompt data
        prompt_data = parse_yaml(file_path)
        validate_prompt_data(prompt_data)
        validate_input_variables(prompt_data, request.input_variables)

        # Execute the prompt
        result = await llm_service.execute_prompt(
            prompt_data=prompt_data,
            input_variables=request.input_variables,
            override_settings=request.override_settings,
            stream=request.stream
        )

        # Format response
        response_data = {
            "response": result["response"],
            "metadata": result["metadata"]
        }

        if request.include_raw_response and "raw_response" in result:
            response_data["raw_response"] = result["raw_response"]

        return InferenceResponse(**response_data)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference execution failed: {str(e)}")


@app.post('/{repo_name}/inference/uuid/{prompt_uuid}', response_model=InferenceResponse)
async def execute_prompt_by_uuid(
    repo_name: str, 
    prompt_uuid: UUID, 
    request: InferenceRequest
):
    """Execute a prompt by UUID using LiteLLM."""
    try:
        repo_path = os.path.join(REPO_HOME, repo_name)
        if not verify_dir_is_repo(repo_path):
            raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

        # Find the prompt by UUID
        prompt_data = None
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.yml'):
                    file_location = os.path.join(root, file)
                    try:
                        data = parse_yaml(file_location)
                        if data.get('uuid') == str(prompt_uuid):
                            prompt_data = data
                            break
                    except Exception:
                        continue  # Skip invalid YAML files
            if prompt_data:
                break

        if not prompt_data:
            raise HTTPException(status_code=404, detail=f'Prompt not found for UUID: {prompt_uuid}')

        # Validate and execute
        validate_prompt_data(prompt_data)
        validate_input_variables(prompt_data, request.input_variables)

        result = await llm_service.execute_prompt(
            prompt_data=prompt_data,
            input_variables=request.input_variables,
            override_settings=request.override_settings,
            stream=request.stream
        )

        # Format response
        response_data = {
            "response": result["response"],
            "metadata": result["metadata"]
        }

        if request.include_raw_response and "raw_response" in result:
            response_data["raw_response"] = result["raw_response"]

        return InferenceResponse(**response_data)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference execution failed: {str(e)}")


@app.post('/{repo_name}/inference/stream/name/{prompt_name}')
async def stream_prompt_by_name(
    repo_name: str, 
    prompt_name: str, 
    request: InferenceRequest
):
    """Execute a prompt by name with streaming response."""
    try:
        # Force streaming
        request.stream = True
        
        # Get the prompt data first
        repo_path = os.path.join(REPO_HOME, repo_name)
        if not verify_dir_is_repo(repo_path):
            raise HTTPException(status_code=400, detail=f'directory is not a git repository: {repo_path}')

        # Find and load the prompt file
        file_path = os.path.join(repo_path, f'{prompt_name}.yml')
        if not os.path.exists(file_path):
            # Try to find it in subdirectories
            found_path = None
            for root, _, files in os.walk(repo_path):
                if f'{prompt_name}.yml' in files:
                    found_path = os.path.join(root, f'{prompt_name}.yml')
                    break
            
            if not found_path:
                raise HTTPException(status_code=404, detail=f'Prompt not found: {prompt_name}')
            file_path = found_path

        # Load and validate prompt data
        prompt_data = parse_yaml(file_path)
        validate_prompt_data(prompt_data)
        validate_input_variables(prompt_data, request.input_variables)

        # Execute the prompt with streaming
        result = await llm_service.execute_prompt(
            prompt_data=prompt_data,
            input_variables=request.input_variables,
            override_settings=request.override_settings,
            stream=True
        )

        # Create streaming response
        async def stream_generator():
            try:
                async for chunk in result["response"]:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        if chunk.choices[0].delta.content:
                            yield f"data: {chunk.choices[0].delta.content}\n\n"
                    elif hasattr(chunk, 'content'):
                        yield f"data: {chunk.content}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR: {str(e)}]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/plain"
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming execution failed: {str(e)}")