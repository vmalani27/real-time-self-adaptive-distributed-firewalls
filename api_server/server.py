from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/push-rule")
async def push_rule(request: Request):
    """Endpoint to push a rule to a registered agent."""
    pass

@app.post("/ack")
async def ack(request: Request):
    """Endpoint for agent to acknowledge rule application."""
    pass 