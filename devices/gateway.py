from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class DeviceCommand:
    action: str
    parameters: dict[str,Any]
    request_id: str

class DeviceGateway:
    """Protocol/runtime foundation shared by desktop and future Android companion."""
    def __init__(self,registry,events):
        self.registry=registry; self.events=events; self._sessions={}

    def connect(self,device_id:str,session:Any):
        self._sessions[device_id]=session
        self.events.emit("device.connected",device_id=device_id)

    def disconnect(self,device_id:str):
        self._sessions.pop(device_id,None)
        self.events.emit("device.disconnected",device_id=device_id)

    async def send(self,device_id:str,command:DeviceCommand):
        session=self._sessions.get(device_id)
        if session is None: raise RuntimeError("device is offline")
        payload={"type":"command","request_id":command.request_id,"action":command.action,"parameters":command.parameters}
        await session.send_json(payload)
        return {"queued":True,"request_id":command.request_id}
