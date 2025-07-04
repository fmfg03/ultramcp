"""
Action execution routes for actions-mcp service
"""

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..core.action_registry import ActionRegistry
from ..core.execution_engine import ExecutionEngine
from ..core.security_manager import SecurityManager
from ..core.audit_logger import AuditLogger

router = APIRouter(prefix="/actions", tags=["actions"])
security = HTTPBearer(auto_error=False)


@router.get("/")
async def list_actions(
    action_registry: ActionRegistry = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """List all available actions"""
    try:
        actions = action_registry.list_actions()
        return {
            "actions": actions,
            "total": len(actions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing actions: {str(e)}")


@router.get("/{action_id}")
async def get_action(
    action_id: str,
    action_registry: ActionRegistry = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get details of a specific action"""
    try:
        action = action_registry.get_action(action_id)
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found")
        
        return {
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving action: {str(e)}")


@router.post("/{action_id}/execute")
async def execute_action(
    action_id: str,
    parameters: Dict[str, Any],
    action_registry: ActionRegistry = Depends(),
    execution_engine: ExecutionEngine = Depends(),
    security_manager: SecurityManager = Depends(),
    audit_logger: AuditLogger = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute an action with given parameters"""
    try:
        # Validate action exists
        action = action_registry.get_action(action_id)
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found")
        
        # Extract user from credentials (mock implementation)
        user_id = "system"  # In production, extract from JWT token
        if credentials:
            user_id = "authenticated_user"  # Extract from token
        
        # Validate security permissions
        if not security_manager.can_execute_action(user_id, action_id):
            raise HTTPException(
                status_code=403, 
                detail=f"User {user_id} not authorized to execute action {action_id}"
            )
        
        # Execute the action
        result = await execution_engine.execute_action(
            action_id=action_id,
            parameters=parameters,
            user_id=user_id
        )
        
        # Log the execution
        await audit_logger.log_action_execution(
            action_id=action_id,
            user_id=user_id,
            parameters=parameters,
            result=result,
            success=result.get("success", False)
        )
        
        return {
            "execution_id": result.get("execution_id"),
            "success": result.get("success", False),
            "result": result.get("result"),
            "error": result.get("error"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error
        await audit_logger.log_action_execution(
            action_id=action_id,
            user_id=user_id if 'user_id' in locals() else "unknown",
            parameters=parameters,
            result={"error": str(e)},
            success=False
        )
        raise HTTPException(status_code=500, detail=f"Error executing action: {str(e)}")


@router.post("/{action_id}/validate")
async def validate_action_parameters(
    action_id: str,
    parameters: Dict[str, Any],
    action_registry: ActionRegistry = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Validate parameters for an action without executing it"""
    try:
        action = action_registry.get_action(action_id)
        if not action:
            raise HTTPException(status_code=404, detail=f"Action {action_id} not found")
        
        # Validate parameters against action schema
        validation_result = action_registry.validate_parameters(action_id, parameters)
        
        return {
            "valid": validation_result.get("valid", False),
            "errors": validation_result.get("errors", []),
            "warnings": validation_result.get("warnings", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating parameters: {str(e)}")


@router.get("/{action_id}/history")
async def get_action_history(
    action_id: str,
    limit: int = 10,
    offset: int = 0,
    audit_logger: AuditLogger = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get execution history for an action"""
    try:
        history = await audit_logger.get_action_history(
            action_id=action_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "history": history,
            "total": len(history),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.post("/batch")
async def execute_batch_actions(
    actions: List[Dict[str, Any]],
    execution_engine: ExecutionEngine = Depends(),
    security_manager: SecurityManager = Depends(),
    audit_logger: AuditLogger = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute multiple actions in batch"""
    try:
        user_id = "system"
        if credentials:
            user_id = "authenticated_user"
        
        results = []
        for action_request in actions:
            action_id = action_request.get("action_id")
            parameters = action_request.get("parameters", {})
            
            # Check permissions
            if not security_manager.can_execute_action(user_id, action_id):
                results.append({
                    "action_id": action_id,
                    "success": False,
                    "error": "Not authorized"
                })
                continue
            
            # Execute action
            try:
                result = await execution_engine.execute_action(
                    action_id=action_id,
                    parameters=parameters,
                    user_id=user_id
                )
                results.append({
                    "action_id": action_id,
                    "success": result.get("success", False),
                    "result": result.get("result"),
                    "error": result.get("error"),
                    "execution_id": result.get("execution_id")
                })
                
                # Log execution
                await audit_logger.log_action_execution(
                    action_id=action_id,
                    user_id=user_id,
                    parameters=parameters,
                    result=result,
                    success=result.get("success", False)
                )
                
            except Exception as e:
                results.append({
                    "action_id": action_id,
                    "success": False,
                    "error": str(e)
                })
                
                # Log error
                await audit_logger.log_action_execution(
                    action_id=action_id,
                    user_id=user_id,
                    parameters=parameters,
                    result={"error": str(e)},
                    success=False
                )
        
        return {
            "results": results,
            "total": len(results),
            "successful": len([r for r in results if r.get("success", False)]),
            "failed": len([r for r in results if not r.get("success", False)]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing batch actions: {str(e)}")


@router.get("/stats/summary")
async def get_action_stats(
    execution_engine: ExecutionEngine = Depends(),
    audit_logger: AuditLogger = Depends(),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get execution statistics summary"""
    try:
        engine_stats = execution_engine.get_stats()
        audit_stats = await audit_logger.get_stats()
        
        return {
            "engine_stats": engine_stats,
            "audit_stats": audit_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")