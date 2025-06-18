from fastapi import WebSocket
from typing import List
import logging
import asyncio
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_cleanup = datetime.now()
        
    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
            
            # 发送连接成功消息
            await websocket.send_text("connected")
            
        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")
            try:
                await websocket.close()
            except:
                pass
            return False
        return True

    async def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        except:
            pass
        
        try:
            await websocket.close()
        except:
            pass

    async def broadcast(self, message: str):
        """
        广播消息给所有连接的客户端
        """
        if not self.active_connections:
            return
            
        # 记录广播消息
        logger.info(f"Broadcasting message to {len(self.active_connections)} clients")
        
        # 执行广播
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
                # 错误的连接会在下一次清理中移除
                
    async def cleanup_connections(self):
        """
        清理失效的连接
        """
        if not self.active_connections:
            return
            
        logger.info(f"Cleaning up connections. Before: {len(self.active_connections)}")
        
        valid_connections = []
        for connection in self.active_connections:
            try:
                # 发送ping消息测试连接
                await connection.send_text("ping")
                valid_connections.append(connection)
            except Exception as e:
                logger.info(f"Removing dead connection: {str(e)}")
                try:
                    await connection.close()
                except:
                    pass
                    
        self.active_connections = valid_connections
        self.last_cleanup = datetime.now()
        logger.info(f"Connections cleanup completed. After: {len(self.active_connections)}")

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    connected = await manager.connect(websocket)
    if not connected:
        return
        
    try:
        while True:
            try:
                # 等待客户端消息
                data = await websocket.receive_text()
                
                # 如果是ping消息，回复pong
                if data == "ping":
                    await websocket.send_text("pong")
                    continue
                    
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await manager.disconnect(websocket) 