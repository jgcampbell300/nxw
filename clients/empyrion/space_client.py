"""
Empyrion-style space client for NXW
Handles space exploration, mining, and resource gathering at solar system level
"""

import asyncio
import json
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class CelestialBodyType(Enum):
    """Types of celestial bodies"""
    STAR = "star"
    PLANET = "planet"
    MOON = "moon"
    ASTEROID = "asteroid"
    GAS_GIANT = "gas_giant"
    SPACE_STATION = "space_station"
    DEBRIS_FIELD = "debris_field"


class ShipType(Enum):
    """Types of spacecraft"""
    SMALL_MINER = "small_miner"
    LARGE_MINER = "large_miner"
    EXPLORER = "explorer"
    CARGO = "cargo"
    FIGHTER = "fighter"
    CORVETTE = "corvette"
    CAPITAL = "capital"


class ResourceType(Enum):
    """Space resources"""
    IRON = "iron"
    COPPER = "copper"
    SILICON = "silicon"
    COBALT = "cobalt"
    MAGNESIUM = "magnesium"
    PROMETHIUM = "promethium"
    ERGO = "ergo"
    ZASCOSIUM = "zascosium"
    NEOTRYNIUM = "neotrynium"
    HYDROGEN = "hydrogen"
    OXYGEN = "oxygen"
    NITROGEN = "nitrogen"
    PENTAXID = "pentaxid"


@dataclass
class Vector3:
    """3D position/vector"""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'Vector3') -> float:
        """Calculate distance to another vector"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def normalize(self) -> 'Vector3':
        """Normalize vector"""
        length = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if length == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x/length, self.y/length, self.z/length)


@dataclass
class CelestialBody:
    """Celestial body in the solar system"""
    id: str
    name: str
    type: CelestialBodyType
    position: Vector3
    radius: float
    mass: float
    resources: Dict[ResourceType, float]  # Resource deposits
    is_explored: bool = False
    mining_operations: List[str] = None  # List of active mining operation IDs
    
    def __post_init__(self):
        if self.mining_operations is None:
            self.mining_operations = []


@dataclass
class Ship:
    """Player's spacecraft"""
    id: str
    type: ShipType
    name: str
    position: Vector3
    velocity: Vector3
    rotation: Vector3  # Pitch, yaw, roll
    cargo_capacity: float
    current_cargo: Dict[ResourceType, float]
    fuel: float
    max_fuel: float
    hull_integrity: float = 100.0
    shield_strength: float = 100.0
    mining_laser_power: float = 1.0
    is_mining: bool = False
    target_body_id: Optional[str] = None
    
    def __post_init__(self):
        if self.current_cargo is None:
            self.current_cargo = {}


@dataclass
class MiningOperation:
    """Active mining operation"""
    id: str
    ship_id: str
    body_id: str
    resource_type: ResourceType
    extraction_rate: float  # Resources per second
    fuel_consumption: float  # Fuel per second
    start_time: float
    total_extracted: float = 0.0


class SpaceClient:
    """Main space client class"""
    
    def __init__(self, player_id: str, location_id: str, api_base: str):
        self.player_id = player_id
        self.location_id = location_id
        self.api_base = api_base
        self.ship: Optional[Ship] = None
        self.celestial_bodies: Dict[str, CelestialBody] = {}
        self.mining_operations: Dict[str, MiningOperation] = {}
        self.current_time = 0.0
        
        self._initialize_solar_system()
    
    def _initialize_solar_system(self):
        """Initialize a basic solar system"""
        # Central star
        self.celestial_bodies["star_1"] = CelestialBody(
            id="star_1",
            name="Sol",
            type=CelestialBodyType.STAR,
            position=Vector3(0, 0, 0),
            radius=696000,  # km (Sun's radius)
            mass=1.989e30,  # kg
            resources={}
        )
        
        # Planets
        self.celestial_bodies["planet_1"] = CelestialBody(
            id="planet_1",
            name="Mercury",
            type=CelestialBodyType.PLANET,
            position=Vector3(57.9e6, 0, 0),  # km from sun
            radius=2439.7,
            mass=3.301e23,
            resources={
                ResourceType.IRON: 1000000,
                ResourceType.COPPER: 500000,
                ResourceType.SILICON: 750000
            }
        )
        
        self.celestial_bodies["planet_2"] = CelestialBody(
            id="planet_2",
            name="Earth",
            type=CelestialBodyType.PLANET,
            position=Vector3(149.6e6, 0, 0),  # km from sun
            radius=6371,
            mass=5.972e24,
            resources={
                ResourceType.IRON: 2000000,
                ResourceType.COPPER: 1000000,
                ResourceType.SILICON: 1500000,
                ResourceType.COBALT: 100000
            }
        )
        
        # Asteroid belt
        for i in range(10):
            self.celestial_bodies[f"asteroid_{i}"] = CelestialBody(
                id=f"asteroid_{i}",
                name=f"Asteroid {i+1}",
                type=CelestialBodyType.ASTEROID,
                position=Vector3(
                    300e6 + (i * 5e6),  # Spread out in asteroid belt
                    (i % 3 - 1) * 2e6,
                    (i % 2) * 1e6
                ),
                radius=100 + (i * 50),
                mass=1e15 + (i * 1e14),
                resources={
                    ResourceType.IRON: 10000 + (i * 5000),
                    ResourceType.COBALT: 1000 + (i * 500),
                    ResourceType.MAGNESIUM: 5000 + (i * 1000)
                }
            )
    
    async def spawn_ship(self, ship_type: ShipType, name: str) -> Ship:
        """Spawn a new ship for the player"""
        ship_configs = {
            ShipType.SMALL_MINER: {"cargo": 1000, "fuel": 500, "mining": 1.0},
            ShipType.LARGE_MINER: {"cargo": 5000, "fuel": 2000, "mining": 2.0},
            ShipType.EXPLORER: {"cargo": 2000, "fuel": 3000, "mining": 0.5},
            ShipType.CARGO: {"cargo": 10000, "fuel": 1500, "mining": 0.0},
            ShipType.FIGHTER: {"cargo": 500, "fuel": 1000, "mining": 0.0},
        }
        
        config = ship_configs.get(ship_type, ship_configs[ShipType.SMALL_MINER])
        
        ship = Ship(
            id=f"ship_{self.player_id}_{len(self.mining_operations)}",
            type=ship_type,
            name=name,
            position=Vector3(150e6, 0, 0),  # Start near Earth
            velocity=Vector3(0, 0, 0),
            rotation=Vector3(0, 0, 0),
            cargo_capacity=config["cargo"],
            current_cargo={},
            fuel=config["fuel"],
            max_fuel=config["fuel"],
            mining_laser_power=config["mining"]
        )
        
        self.ship = ship
        return ship
    
    async def move_ship(self, direction: Vector3, thrust: float) -> bool:
        """Apply thrust to move the ship"""
        if not self.ship:
            return False
        
        if self.ship.fuel <= 0:
            return False
        
        # Apply thrust
        acceleration = direction.normalize()
        acceleration.x *= thrust / self.ship.mass if hasattr(self.ship, 'mass') else thrust
        acceleration.y *= thrust / self.ship.mass if hasattr(self.ship, 'mass') else thrust
        acceleration.z *= thrust / self.ship.mass if hasattr(self.ship, 'mass') else thrust
        
        # Update velocity
        self.ship.velocity.x += acceleration.x
        self.ship.velocity.y += acceleration.y
        self.ship.velocity.z += acceleration.z
        
        # Consume fuel
        self.ship.fuel -= thrust * 0.1
        self.ship.fuel = max(0, self.ship.fuel)
        
        return True
    
    async def update_position(self, dt: float):
        """Update ship position based on velocity"""
        if not self.ship:
            return
        
        # Update position
        self.ship.position.x += self.ship.velocity.x * dt
        self.ship.position.y += self.ship.velocity.y * dt
        self.ship.position.z += self.ship.velocity.z * dt
        
        # Apply drag (space friction simulation)
        drag = 0.99
        self.ship.velocity.x *= drag
        self.ship.velocity.y *= drag
        self.ship.velocity.z *= drag
    
    async def scan_nearby_bodies(self, range_km: float) -> List[CelestialBody]:
        """Scan for celestial bodies within range"""
        if not self.ship:
            return []
        
        nearby_bodies = []
        for body in self.celestial_bodies.values():
            distance = self.ship.position.distance_to(body.position)
            if distance <= range_km:
                nearby_bodies.append(body)
                body.is_explored = True
        
        return nearby_bodies
    
    async def start_mining(self, body_id: str, resource_type: ResourceType) -> bool:
        """Start mining operation on a celestial body"""
        if not self.ship:
            return False
        
        if body_id not in self.celestial_bodies:
            return False
        
        body = self.celestial_bodies[body_id]
        
        # Check if ship is close enough
        distance = self.ship.position.distance_to(body.position)
        if distance > body.radius + 1000:  # Within 1000 km of surface
            return False
        
        # Check if resource exists
        if resource_type not in body.resources or body.resources[resource_type] <= 0:
            return False
        
        # Check if ship has cargo space
        current_cargo = sum(self.ship.current_cargo.values())
        if current_cargo >= self.ship.cargo_capacity:
            return False
        
        # Create mining operation
        operation_id = f"mining_{len(self.mining_operations)}"
        extraction_rate = self.ship.mining_laser_power * 10  # Resources per second
        fuel_consumption = self.ship.mining_laser_power * 2  # Fuel per second
        
        operation = MiningOperation(
            id=operation_id,
            ship_id=self.ship.id,
            body_id=body_id,
            resource_type=resource_type,
            extraction_rate=extraction_rate,
            fuel_consumption=fuel_consumption,
            start_time=self.current_time
        )
        
        self.mining_operations[operation_id] = operation
        self.ship.is_mining = True
        self.ship.target_body_id = body_id
        body.mining_operations.append(operation_id)
        
        return True
    
    async def stop_mining(self) -> bool:
        """Stop current mining operation"""
        if not self.ship or not self.ship.is_mining:
            return False
        
        # Find and remove mining operation
        for op_id, operation in list(self.mining_operations.items()):
            if operation.ship_id == self.ship.id:
                # Remove from body
                body = self.celestial_bodies[operation.body_id]
                if op_id in body.mining_operations:
                    body.mining_operations.remove(op_id)
                
                # Remove operation
                del self.mining_operations[op_id]
                break
        
        self.ship.is_mining = False
        self.ship.target_body_id = None
        return True
    
    async def update_mining(self, dt: float):
        """Update active mining operations"""
        for operation in list(self.mining_operations.values()):
            if not self.ship or operation.ship_id != self.ship.id:
                continue
            
            # Check fuel
            if self.ship.fuel <= 0:
                await self.stop_mining()
                continue
            
            # Check cargo space
            current_cargo = sum(self.ship.current_cargo.values())
            if current_cargo >= self.ship.cargo_capacity:
                await self.stop_mining()
                continue
            
            # Extract resources
            body = self.celestial_bodies[operation.body_id]
            extracted = min(operation.extraction_rate * dt, body.resources[operation.resource_type])
            
            if extracted <= 0:
                await self.stop_mining()
                continue
            
            # Update resources
            body.resources[operation.resource_type] -= extracted
            operation.total_extracted += extracted
            
            # Add to ship cargo
            self.ship.current_cargo[operation.resource_type] = \
                self.ship.current_cargo.get(operation.resource_type, 0) + extracted
            
            # Consume fuel
            self.ship.fuel -= operation.fuel_consumption * dt
            self.ship.fuel = max(0, self.ship.fuel)
    
    async def refuel_ship(self, fuel_amount: float) -> bool:
        """Refuel the ship from cargo or station"""
        if not self.ship:
            return False
        
        # Check if ship has hydrogen fuel in cargo
        available_fuel = self.ship.current_cargo.get(ResourceType.HYDROGEN, 0)
        if available_fuel >= fuel_amount:
            self.ship.current_cargo[ResourceType.HYDROGEN] -= fuel_amount
            self.ship.fuel = min(self.ship.max_fuel, self.ship.fuel + fuel_amount)
            return True
        
        return False
    
    async def offload_cargo(self) -> Dict[ResourceType, float]:
        """Offload all cargo to storage"""
        if not self.ship:
            return {}
        
        cargo = self.ship.current_cargo.copy()
        self.ship.current_cargo.clear()
        return cargo
    
    def get_space_status(self) -> Dict[str, Any]:
        """Get current space client status"""
        if not self.ship:
            return {"error": "No ship spawned"}
        
        nearby_bodies = []
        for body in self.celestial_bodies.values():
            if body.is_explored:
                distance = self.ship.position.distance_to(body.position)
                nearby_bodies.append({
                    "id": body.id,
                    "name": body.name,
                    "type": body.type.value,
                    "distance": distance,
                    "resources": {r.value: v for r, v in body.resources.items()}
                })
        
        return {
            "ship": {
                "id": self.ship.id,
                "name": self.ship.name,
                "type": self.ship.type.value,
                "position": {"x": self.ship.position.x, "y": self.ship.position.y, "z": self.ship.position.z},
                "velocity": {"x": self.ship.velocity.x, "y": self.ship.velocity.y, "z": self.ship.velocity.z},
                "fuel": self.ship.fuel,
                "max_fuel": self.ship.max_fuel,
                "cargo": {r.value: v for r, v in self.ship.current_cargo.items()},
                "cargo_used": sum(self.ship.current_cargo.values()),
                "cargo_capacity": self.ship.cargo_capacity,
                "is_mining": self.ship.is_mining,
                "target_body": self.ship.target_body_id
            },
            "mining_operations": len(self.mining_operations),
            "explored_bodies": nearby_bodies
        }


# Example usage
async def main():
    """Example space client usage"""
    client = SpaceClient("player_123", "solar_system_1", "http://localhost:8000")
    
    # Spawn a ship
    ship = await client.spawn_ship(ShipType.SMALL_MINER, "Miner-1")
    print(f"Spawned ship: {ship.name}")
    
    # Move towards an asteroid
    asteroid = client.celestial_bodies["asteroid_0"]
    direction = Vector3(
        asteroid.position.x - ship.position.x,
        asteroid.position.y - ship.position.y,
        asteroid.position.z - ship.position.z
    )
    
    await client.move_ship(direction, 1000)  # Apply thrust
    
    # Update position for a few seconds
    for _ in range(10):
        await client.update_position(1.0)
        distance = ship.position.distance_to(asteroid.position)
        print(f"Distance to asteroid: {distance:.0f} km")
        
        if distance < asteroid.radius + 1000:
            print("Close enough to start mining!")
            break
        
        await asyncio.sleep(0.1)
    
    # Start mining
    if ResourceType.IRON in asteroid.resources:
        success = await client.start_mining(asteroid.id, ResourceType.IRON)
        if success:
            print("Started mining iron!")
            
            # Mine for a few seconds
            for _ in range(20):
                await client.update_mining(0.5)
                status = client.get_space_status()
                iron_mined = status["ship"]["cargo"].get("iron", 0)
                print(f"Mined {iron_mined:.1f} iron")
                await asyncio.sleep(0.1)
            
            await client.stop_mining()
            print("Stopped mining")


if __name__ == "__main__":
    asyncio.run(main())
