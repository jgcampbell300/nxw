"""
Universe hierarchy models for NXW MMORPG
Defines the cosmic to building scale structure
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UniverseLevel(Enum):
    """All universe levels from cosmic to building scale"""
    UNIVERSE = "universe"
    SUPERCLUSTER = "supercluster"
    GALAXY_CLUSTER = "galaxy_cluster"
    GALAXY_GROUP = "galaxy_group"
    GALAXY = "galaxy"
    SOLAR_NEIGHBORHOOD = "solar_neighborhood"
    SOLAR_SYSTEM = "solar_system"
    PLANET = "planet"
    BIOSPHERE = "biosphere"
    BIOME = "biome"
    CONTINENT = "continent"
    HEMISPHERE = "hemisphere"
    REGION = "region"
    COUNTRY = "country"
    STATE_PROVINCE = "state_province"
    COUNTY = "county"
    CITY_TOWN = "city_town"
    NEIGHBORHOOD = "neighborhood"
    STREET = "street"
    ADDRESS = "address"
    BUILDING = "building"
    UNIT_APARTMENT = "unit_apartment"
    ROOM = "room"


class ClientType(Enum):
    """Different client types for various gameplay styles"""
    FACTORIO = "factorio"  # Factory/industrial building
    EMPYRION = "empyrion"  # Space exploration/mining
    FPS = "fps"  # First person shooter
    SIMCITY = "simcity"  # City building
    SEVENDAYSTODIE = "7dtd"  # Survival/base building
    ADVENTURE = "adventure"  # RPG/dungeon style


class ResourceType(Enum):
    """Types of resources that can be gathered"""
    MINERAL = "mineral"
    ORGANIC = "organic"
    ENERGY = "energy"
    GAS = "gas"
    LIQUID = "liquid"
    MANUFACTURED = "manufactured"
    RARE = "rare"
    EXOTIC = "exotic"


class UniverseEntity(BaseModel):
    """Base model for all universe entities"""
    id: str
    name: str
    level: UniverseLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    position: Dict[str, float] = Field(default_factory=dict)  # x, y, z coordinates
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Client types available at this level
    available_clients: List[ClientType] = Field(default_factory=list)
    
    # Resources available at this level
    available_resources: List[ResourceType] = Field(default_factory=list)


class ResourceNode(BaseModel):
    """Resource gathering nodes"""
    id: str
    resource_type: ResourceType
    quantity: float
    regeneration_rate: Optional[float] = None  # Resources per time period
    location_id: str  # ID of universe entity where this node exists
    extraction_difficulty: float = 1.0  # 1.0 = easy, higher = harder
    required_technology_level: int = 1
    properties: Dict[str, Any] = Field(default_factory=dict)


class Player(BaseModel):
    """Player model"""
    id: str
    username: str
    current_location_id: str
    owned_entities: List[str] = Field(default_factory=list)
    inventory: Dict[str, int] = Field(default_factory=dict)  # resource_id -> quantity
    active_clients: List[ClientType] = Field(default_factory=list)
    technology_level: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClientSession(BaseModel):
    """Active client session"""
    id: str
    player_id: str
    client_type: ClientType
    location_id: str
    session_data: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


# Level-specific configurations
LEVEL_CONFIGS = {
    UniverseLevel.UNIVERSE: {
        "available_clients": [],
        "available_resources": [ResourceType.EXOTIC],
        "scale": "cosmic"
    },
    UniverseLevel.SUPERCLUSTER: {
        "available_clients": [],
        "available_resources": [ResourceType.EXOTIC, ResourceType.RARE],
        "scale": "cosmic"
    },
    UniverseLevel.GALAXY: {
        "available_clients": [],
        "available_resources": [ResourceType.RARE, ResourceType.ENERGY],
        "scale": "cosmic"
    },
    UniverseLevel.SOLAR_SYSTEM: {
        "available_clients": [ClientType.EMPYRION],
        "available_resources": [ResourceType.MINERAL, ResourceType.GAS, ResourceType.ENERGY],
        "scale": "stellar"
    },
    UniverseLevel.PLANET: {
        "available_clients": [ClientType.EMPYRION, ClientType.SIMCITY],
        "available_resources": [ResourceType.MINERAL, ResourceType.ORGANIC, ResourceType.LIQUID],
        "scale": "planetary"
    },
    UniverseLevel.BUILDING: {
        "available_clients": [ClientType.FACTORIO, ClientType.SEVENDAYSTODIE, ClientType.FPS],
        "available_resources": [ResourceType.MANUFACTURED, ResourceType.ORGANIC],
        "scale": "building"
    },
    UniverseLevel.CITY_TOWN: {
        "available_clients": [ClientType.SIMCITY, ClientType.FPS, ClientType.ADVENTURE],
        "available_resources": [ResourceType.MANUFACTURED, ResourceType.ORGANIC],
        "scale": "urban"
    },
    UniverseLevel.ROOM: {
        "available_clients": [ClientType.FPS, ClientType.ADVENTURE],
        "available_resources": [],
        "scale": "room"
    }
}


def get_available_clients(level: UniverseLevel) -> List[ClientType]:
    """Get available client types for a universe level"""
    config = LEVEL_CONFIGS.get(level, {})
    return config.get("available_clients", [])


def get_available_resources(level: UniverseLevel) -> List[ResourceType]:
    """Get available resource types for a universe level"""
    config = LEVEL_CONFIGS.get(level, {})
    return config.get("available_resources", [])
