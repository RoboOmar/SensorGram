from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Dict
import json
import logging

from backend.database import get_db, SessionLocal
from backend.models.robot import Robot
from backend.models.message import Message
from backend.schemas.message import MessageOut, MessageCreate
from backend.routers.auth import get_current_robot
from backend.services.auth_service import decode_token

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        # Maps robot_id -> List[WebSocket]
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, robot_id: int):
        await websocket.accept()
        if robot_id not in self.active_connections:
            self.active_connections[robot_id] = []
        self.active_connections[robot_id].append(websocket)
        print(f"[WS] Robot {robot_id} connected. Active tabs/connections: {len(self.active_connections[robot_id])}")

    def disconnect(self, websocket: WebSocket, robot_id: int):
        if robot_id in self.active_connections:
            if websocket in self.active_connections[robot_id]:
                self.active_connections[robot_id].remove(websocket)
            if not self.active_connections[robot_id]:
                del self.active_connections[robot_id]
        print(f"[WS] Robot {robot_id} disconnected. Remaining connections: {len(self.active_connections.get(robot_id, []))}")

    async def send_personal_message(self, message: str, robot_id: int):
        print(f"[WS] Routing message to robot_id {robot_id}")
        connections = self.active_connections.get(robot_id, [])
        if not connections:
            print(f"[WS] FAILED: No active connections found for robot_id {robot_id}")
            return
            
        print(f"[WS] SUCCESS: Found {len(connections)} connections for robot_id {robot_id}. Sending...")
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception as e:
                print(f"[WS] ERROR sending to a connection for robot_id {robot_id}: {e}")

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=1008)
            return
        username = payload.get("sub")
        with SessionLocal() as db:
            robot = db.query(Robot).filter(Robot.username == username).first()
            if not robot:
                await websocket.close(code=1008)
                return
            robot_id = robot.id
    except Exception as e:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket, robot_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Expecting JSON: {"receiver_id": int, "text_content": "..."}
                msg_data = json.loads(data)
                receiver_id = msg_data.get("receiver_id")
                text_content = msg_data.get("text_content")
                
                if receiver_id and text_content:
                    receiver_id = int(receiver_id)
                    with SessionLocal() as db:
                        new_msg = Message(sender_id=robot_id, receiver_id=receiver_id, text_content=text_content)
                        db.add(new_msg)
                        db.commit()
                        db.refresh(new_msg)
                        
                        # Prepare payload
                        msg_out = MessageOut.from_orm(new_msg)
                        payload_str = msg_out.json()
                    
                    # Send back to sender so they have the confirmed message (optional, but good for UI)
                    await websocket.send_text(payload_str)
                    
                    # Send to receiver if online
                    await manager.send_personal_message(payload_str, receiver_id)
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, robot_id)

@router.get("/history/{user_id}", response_model=List[MessageOut])
def get_chat_history(user_id: int, db: Session = Depends(get_db), current_robot: Robot = Depends(get_current_robot)):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_robot.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_robot.id))
    ).order_by(Message.timestamp.asc()).all()
    return messages

@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db), current_robot: Robot = Depends(get_current_robot)):
    # Simple list of all users except the current one (could be optimized)
    robots = db.query(Robot).filter(Robot.id != current_robot.id).all()
    return [{"id": r.id, "username": r.username, "display_name": r.display_name, "avatar_url": r.avatar_url} for r in robots]
