from __future__ import annotations
import secrets
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from core.security import PairingManager

class PairConfirm(BaseModel): token:str; code:str
class PairedCommand(BaseModel): text:str

def create_app(executor, settings):
    app=FastAPI(title="Personal AI Local Control",docs_url=None,redoc_url=None); pairing=PairingManager(settings.pairing_ttl_seconds); bearer_tokens=set()
    @app.get("/health")
    def health(): return {"ok":True}
    @app.post("/pair/start")
    def pair_start():
        offer=pairing.create(); return {"token":offer.token,"code":offer.code,"expires_at":offer.expires_at}
    @app.post("/pair/confirm")
    def pair_confirm(body:PairConfirm):
        if not pairing.consume(body.token,body.code): raise HTTPException(401,"Invalid or expired pairing offer")
        token=secrets.token_urlsafe(32); bearer_tokens.add(token); return {"bearer_token":token}
    @app.post("/command")
    def command(body:PairedCommand, authorization:str|None=Header(default=None)):
        token=(authorization or "").removeprefix("Bearer ").strip()
        if token not in bearer_tokens: raise HTTPException(401,"Unauthorized")
        return {"reply":executor.chat(body.text)}
    return app
