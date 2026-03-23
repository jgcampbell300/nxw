"""
Main backend application for NXW MMORPG
Handles universe management, client coordination, and API endpoints
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime

from shared.models.universe import (
    UniverseEntity, UniverseLevel, ClientType, ResourceType,
    ResourceNode, Player, ClientSession,
    get_available_clients, get_available_resources
)


app = FastAPI(
    title="NXW - Nxverse Web API",
    description="API for multi-scale MMORPG universe",
    version="0.1.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database later)
universe_entities: Dict[str, UniverseEntity] = {}
players: Dict[str, Player] = {}
resource_nodes: Dict[str, ResourceNode] = {}
active_sessions: Dict[str, ClientSession] = {}


@app.get("/")
async def root():
    return {"message": "NXW API is running", "version": "0.1.0"}


@app.get("/universe/levels")
async def get_universe_levels():
    """Get all universe levels and their configurations"""
    return {
        "levels": [level.value for level in UniverseLevel],
        "client_types": [client.value for client in ClientType],
        "resource_types": [resource.value for resource in ResourceType]
    }


@app.post("/universe/entity")
async def create_universe_entity(entity: UniverseEntity):
    """Create a new universe entity"""
    universe_entities[entity.id] = entity
    return {"message": f"Entity {entity.name} created successfully", "id": entity.id}


@app.get("/universe/entity/{entity_id}")
async def get_universe_entity(entity_id: str):
    """Get a specific universe entity"""
    if entity_id not in universe_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    return universe_entities[entity_id]


@app.get("/universe/entity/{entity_id}/children")
async def get_entity_children(entity_id: str):
    """Get all children of a universe entity"""
    if entity_id not in universe_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = universe_entities[entity_id]
    children = []
    for child_id in entity.children_ids:
        if child_id in universe_entities:
            children.append(universe_entities[child_id])
    
    return {"children": children}


@app.get("/universe/entity/{entity_id}/clients")
async def get_available_clients_for_entity(entity_id: str):
    """Get available client types for a universe entity"""
    if entity_id not in universe_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    entity = universe_entities[entity_id]
    available_clients = get_available_clients(entity.level)
    
    return {
        "entity_id": entity_id,
        "level": entity.level.value,
        "available_clients": [client.value for client in available_clients]
    }


@app.post("/players")
async def create_player(player: Player):
    """Create a new player"""
    players[player.id] = player
    return {"message": f"Player {player.username} created successfully", "id": player.id}


@app.get("/players/{player_id}")
async def get_player(player_id: str):
    """Get player information"""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    return players[player_id]


@app.post("/players/{player_id}/teleport/{entity_id}")
async def teleport_player(player_id: str, entity_id: str):
    """Teleport player to a different universe entity"""
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    if entity_id not in universe_entities:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    players[player_id].current_location_id = entity_id
    players[player_id].updated_at = datetime.utcnow()
    
    return {"message": f"Player teleported to {universe_entities[entity_id].name}"}


@app.post("/sessions")
async def create_client_session(session: ClientSession):
    """Create a new client session"""
    active_sessions[session.id] = session
    return {"message": "Session created successfully", "session_id": session.id}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_sessions[session_id]


@app.post("/resources/node")
async def create_resource_node(node: ResourceNode):
    """Create a new resource gathering node"""
    resource_nodes[node.id] = node
    return {"message": "Resource node created successfully", "node_id": node.id}


@app.get("/resources/location/{location_id}")
async def get_resources_at_location(location_id: str):
    """Get all resource nodes at a specific location"""
    location_resources = []
    for node in resource_nodes.values():
        if node.location_id == location_id:
            location_resources.append(node)
    
    return {"location_id": location_id, "resources": location_resources}


@app.post("/resources/{node_id}/extract")
async def extract_resource(node_id: str, player_id: str, amount: float):
    """Extract resources from a node"""
    if node_id not in resource_nodes:
        raise HTTPException(status_code=404, detail="Resource node not found")
    if player_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")
    
    node = resource_nodes[node_id]
    player = players[player_id]
    
    if amount > node.quantity:
        raise HTTPException(status_code=400, detail="Insufficient resources")
    
    # Extract resources
    node.quantity -= amount
    resource_key = node.resource_type.value
    player.inventory[resource_key] = player.inventory.get(resource_key, 0) + amount
    
    return {
        "message": f"Extracted {amount} {resource_key}",
        "remaining": node.quantity,
        "player_inventory": player.inventory
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
