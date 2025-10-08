"""
DEPRECATED: WebSocket receiver stub

This file previously provided a WebSocket endpoint for receiving rules from the
controller. WebSocket support has been removed and the project now uses REST
HTTP endpoints exclusively (POST /apply-rule). The original implementation was
deleted to remove runtime WebSocket behavior.

Left as a harmless stub for reference. If you want this file fully removed,
delete it from the repository.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get('/ws-deprecated')
async def ws_deprecated():
    return {'status': 'deprecated', 'message': 'WebSocket support removed; use REST /apply-rule'}