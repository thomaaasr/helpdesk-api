from fastapi import FastAPI

app = FastAPI(
    title="Help Desk API",
    description="API de chamados de TI: abertura, atendimento, comentários e SLA.",
    version="0.1.0",
)


@app.get("/saude", tags=["Saúde"])
def saude() -> dict[str, str]:
    """Usado para saber se a API está no ar."""
    return {"status": "ok"}
