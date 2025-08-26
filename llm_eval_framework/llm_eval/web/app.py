"""
FastAPI web dashboard for LLM evaluation results visualization.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..config.models import EvaluationSummary


# Data models for API
class SharedResult(BaseModel):
    """Model for shared evaluation results."""
    id: str
    title: str
    summary: EvaluationSummary
    created_at: datetime
    expires_at: datetime


class ThumbsRequest(BaseModel):
    """Model for thumbs up/down requests."""
    result_id: str
    provider_id: str
    test_index: int
    thumbs_up: bool


# Initialize FastAPI app
app = FastAPI(
    title="LLM Evaluation Dashboard",
    description="Web interface for viewing and analyzing LLM evaluation results",
    version="0.1.0"
)

# Global state (in production, use Redis or database)
_shared_results: Dict[str, SharedResult] = {}
_current_results: Optional[EvaluationSummary] = None
_thumbs_data: Dict[str, Dict[str, bool]] = {}  # result_id -> provider_test -> bool

# Templates and static files
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
# app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    if not _current_results:
        return templates.TemplateResponse(
            "no_results.html", 
            {"request": request}
        )
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "summary": _current_results,
            "results_by_provider": _group_results_by_provider(_current_results.results)
        }
    )


@app.get("/api/results")
async def get_current_results():
    """Get current evaluation results."""
    if not _current_results:
        raise HTTPException(status_code=404, detail="No results available")
    
    return {
        "summary": _current_results.dict(),
        "thumbs_data": _thumbs_data.get("current", {})
    }


@app.post("/api/thumbs")
async def record_thumbs(request: ThumbsRequest):
    """Record thumbs up/down for a specific result."""
    result_key = f"{request.provider_id}_{request.test_index}"
    
    if "current" not in _thumbs_data:
        _thumbs_data["current"] = {}
    
    _thumbs_data["current"][result_key] = request.thumbs_up
    
    return {"success": True, "recorded": request.thumbs_up}


@app.post("/api/share")
async def share_results():
    """Create a shareable link for current results."""
    if not _current_results:
        raise HTTPException(status_code=404, detail="No results to share")
    
    # Generate unique ID
    share_id = str(uuid.uuid4())
    
    # Create shared result
    shared_result = SharedResult(
        id=share_id,
        title=f"LLM Evaluation - {_current_results.timestamp}",
        summary=_current_results,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(weeks=2)
    )
    
    _shared_results[share_id] = shared_result
    
    return {
        "share_id": share_id,
        "share_url": f"/shared/{share_id}",
        "expires_at": shared_result.expires_at.isoformat()
    }


@app.get("/shared/{share_id}", response_class=HTMLResponse)
async def view_shared(share_id: str, request: Request):
    """View shared evaluation results."""
    if share_id not in _shared_results:
        raise HTTPException(status_code=404, detail="Shared result not found")
    
    shared_result = _shared_results[share_id]
    
    # Check if expired
    if datetime.now() > shared_result.expires_at:
        del _shared_results[share_id]
        raise HTTPException(status_code=410, detail="Shared result has expired")
    
    return templates.TemplateResponse(
        "shared.html",
        {
            "request": request,
            "shared_result": shared_result,
            "summary": shared_result.summary,
            "results_by_provider": _group_results_by_provider(shared_result.summary.results)
        }
    )


@app.get("/api/compare")
async def compare_providers():
    """Get provider comparison data."""
    if not _current_results:
        raise HTTPException(status_code=404, detail="No results available")
    
    comparison_data = {}
    
    # Group results by provider
    provider_results = _group_results_by_provider(_current_results.results)
    
    for provider_id, results in provider_results.items():
        passed = sum(1 for r in results if r.success)
        total = len(results)
        avg_cost = sum(r.cost for r in results if r.cost) / total if total > 0 else 0
        avg_latency = sum(r.latency for r in results if r.latency) / total if total > 0 else 0
        
        comparison_data[provider_id] = {
            "pass_rate": passed / total if total > 0 else 0,
            "total_tests": total,
            "passed_tests": passed,
            "avg_cost": avg_cost,
            "avg_latency": avg_latency,
            "total_cost": sum(r.cost for r in results if r.cost)
        }
    
    return comparison_data


@app.get("/api/test-details/{test_index}")
async def get_test_details(test_index: int):
    """Get detailed information for a specific test."""
    if not _current_results or test_index >= len(_current_results.results):
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get all results for this test across providers
    test_results = []
    for result in _current_results.results:
        # This is a simplified approach - in reality, you'd need better test indexing
        test_results.append(result)
    
    return {"test_index": test_index, "results": [r.dict() for r in test_results]}


@app.post("/api/export/{format}")
async def export_results(format: str):
    """Export results in various formats."""
    if not _current_results:
        raise HTTPException(status_code=404, detail="No results available")
    
    if format == "json":
        return JSONResponse(
            content=_current_results.dict(),
            headers={"Content-Disposition": "attachment; filename=evaluation_results.json"}
        )
    
    elif format == "csv":
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "provider_id", "prompt", "response", "success", "cost", 
            "latency", "assertion_results", "error"
        ])
        
        # Write data
        for result in _current_results.results:
            writer.writerow([
                result.provider_id,
                result.prompt[:100] + "..." if len(result.prompt) > 100 else result.prompt,
                result.response[:100] + "..." if len(result.response) > 100 else result.response,
                result.success,
                result.cost,
                result.latency,
                json.dumps(result.assertion_results),
                result.error or ""
            ])
        
        return JSONResponse(
            content={"csv_data": output.getvalue()},
            headers={"Content-Disposition": "attachment; filename=evaluation_results.csv"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


# Utility functions
def _group_results_by_provider(results) -> Dict[str, List]:
    """Group evaluation results by provider ID."""
    grouped = {}
    for result in results:
        provider_id = result.provider_id
        if provider_id not in grouped:
            grouped[provider_id] = []
        grouped[provider_id].append(result)
    return grouped


# Functions to update results (called from CLI)
def update_current_results(summary: EvaluationSummary):
    """Update the current results displayed in the dashboard."""
    global _current_results
    _current_results = summary


def clear_results():
    """Clear current results."""
    global _current_results, _thumbs_data
    _current_results = None
    _thumbs_data.clear()


def get_app():
    """Get the FastAPI app instance."""
    return app