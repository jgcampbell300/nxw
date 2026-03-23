"""
Factorio-style factory client for NXW
Handles factory building, automation, and resource processing at building level
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class MachineType(Enum):
    """Types of factory machines"""
    ASSEMBLER = "assembler"
    SMELTER = "smelter"
    CHEMICAL_PLANT = "chemical_plant"
    OIL_REFINERY = "oil_refinery"
    CENTRIFUGE = "centrifuge"
    ROCKET_SILO = "rocket_silo"
    LAB = "lab"
    POWER_PLANT = "power_plant"
    MINING_DRILL = "mining_drill"


class ResourceType(Enum):
    """Resource types for factory processing"""
    IRON_ORE = "iron_ore"
    COPPER_ORE = "copper_ore"
    COAL = "coal"
    STONE = "stone"
    URANIUM_ORE = "uranium_ore"
    CRUDE_OIL = "crude_oil"
    WATER = "water"
    IRON_PLATE = "iron_plate"
    COPPER_PLATE = "copper_plate"
    STEEL = "steel"
    ELECTRONIC_CIRCUIT = "electronic_circuit"
    ADVANCED_CIRCUIT = "advanced_circuit"
    PROCESSING_UNIT = "processing_unit"


@dataclass
class Recipe:
    """Production recipe"""
    id: str
    name: str
    inputs: Dict[ResourceType, float]
    outputs: Dict[ResourceType, float]
    energy_required: float  # seconds
    machine_type: MachineType


@dataclass
class Machine:
    """Factory machine instance"""
    id: str
    type: MachineType
    position: Dict[str, float]  # x, y in factory grid
    recipe: Optional[Recipe] = None
    inventory: Dict[ResourceType, float] = None
    power_consumption: float = 0.0
    is_active: bool = False
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = {}


@dataclass
class Belt:
"""Transport belt"""
    id: str
    start_pos: Dict[str, float]
    end_pos: Dict[str, float]
    items: List[ResourceType] = None
    speed: float = 1.0
    
    def __post_init__(self):
        if self.items is None:
            self.items = []


class FactoryClient:
    """Main factory client class"""
    
    def __init__(self, player_id: str, location_id: str, api_base: str):
        self.player_id = player_id
        self.location_id = location_id
        self.api_base = api_base
        self.machines: Dict[str, Machine] = {}
        self.belts: Dict[str, Belt] = {}
        self.recipes: Dict[str, Recipe] = {}
        self.grid_size = {"width": 100, "height": 100}
        self.inventory: Dict[ResourceType, float] = {}
        
        self._initialize_recipes()
    
    def _initialize_recipes(self):
        """Initialize basic factory recipes"""
        self.recipes = {
            "iron_plate": Recipe(
                id="iron_plate",
                name="Iron Plate",
                inputs={ResourceType.IRON_ORE: 1.0},
                outputs={ResourceType.IRON_PLATE: 1.0},
                energy_required=3.2,
                machine_type=MachineType.SMELTER
            ),
            "copper_plate": Recipe(
                id="copper_plate",
                name="Copper Plate",
                inputs={ResourceType.COPPER_ORE: 1.0},
                outputs={ResourceType.COPPER_PLATE: 1.0},
                energy_required=3.2,
                machine_type=MachineType.SMELTER
            ),
            "steel": Recipe(
                id="steel",
                name="Steel",
                inputs={ResourceType.IRON_PLATE: 5.0, ResourceType.COAL: 1.0},
                outputs={ResourceType.STEEL: 1.0},
                energy_required=16.0,
                machine_type=MachineType.SMELTER
            ),
            "electronic_circuit": Recipe(
                id="electronic_circuit",
                name="Electronic Circuit",
                inputs={ResourceType.IRON_PLATE: 1.0, ResourceType.COPPER_CABLE: 3.0},
                outputs={ResourceType.ELECTRONIC_CIRCUIT: 1.0},
                energy_required=0.5,
                machine_type=MachineType.ASSEMBLER
            ),
            "advanced_circuit": Recipe(
                id="advanced_circuit",
                name="Advanced Circuit",
                inputs={ResourceType.ELECTRONIC_CIRCUIT: 2.0, ResourceType.PLASTIC: 2.0, ResourceType.COPPER_CABLE: 4.0},
                outputs={ResourceType.ADVANCED_CIRCUIT: 1.0},
                energy_required=6.0,
                machine_type=MachineType.ASSEMBLER
            ),
            "processing_unit": Recipe(
                id="processing_unit",
                name="Processing Unit",
                inputs={ResourceType.ADVANCED_CIRCUIT: 2.0, ResourceType.ELECTRONIC_CIRCUIT: 20.0},
                outputs={ResourceType.PROCESSING_UNIT: 1.0},
                energy_required=10.0,
                machine_type=MachineType.ASSEMBLER
            )
        }
    
    async def place_machine(self, machine_type: MachineType, position: Dict[str, float]) -> Machine:
        """Place a new machine in the factory"""
        machine_id = f"machine_{len(self.machines)}"
        
        machine = Machine(
            id=machine_id,
            type=machine_type,
            position=position
        )
        
        self.machines[machine_id] = machine
        return machine
    
    async def remove_machine(self, machine_id: str) -> bool:
        """Remove a machine from the factory"""
        if machine_id in self.machines:
            # Return items to inventory
            machine = self.machines[machine_id]
            for resource, quantity in machine.inventory.items():
                self.inventory[resource] = self.inventory.get(resource, 0) + quantity
            
            del self.machines[machine_id]
            return True
        return False
    
    async def set_machine_recipe(self, machine_id: str, recipe_id: str) -> bool:
        """Set recipe for a machine"""
        if machine_id not in self.machines or recipe_id not in self.recipes:
            return False
        
        machine = self.machines[machine_id]
        recipe = self.recipes[recipe_id]
        
        # Check if machine type is compatible
        if machine.type != recipe.machine_type:
            return False
        
        machine.recipe = recipe
        return True
    
    async def start_production(self, machine_id: str) -> bool:
        """Start production on a machine"""
        if machine_id not in self.machines:
            return False
        
        machine = self.machines[machine_id]
        if not machine.recipe:
            return False
        
        # Check if we have enough inputs
        for resource, required_amount in machine.recipe.inputs.items():
            available = machine.inventory.get(resource, 0) + self.inventory.get(resource, 0)
            if available < required_amount:
                return False
        
        machine.is_active = True
        return True
    
    async def stop_production(self, machine_id: str) -> bool:
        """Stop production on a machine"""
        if machine_id not in self.machines:
            return False
        
        self.machines[machine_id].is_active = False
        return True
    
    async def update_production(self, dt: float):
        """Update production for all active machines"""
        for machine in self.machines.values():
            if machine.is_active and machine.recipe:
                # Calculate progress
                progress = dt / machine.recipe.energy_required
                
                # Consume inputs
                for resource, amount in machine.recipe.inputs.items():
                    needed = amount * progress
                    
                    # Take from machine inventory first, then player inventory
                    machine_amount = machine.inventory.get(resource, 0)
                    if machine_amount >= needed:
                        machine.inventory[resource] = machine_amount - needed
                    else:
                        remaining = needed - machine_amount
                        machine.inventory[resource] = 0
                        
                        player_amount = self.inventory.get(resource, 0)
                        if player_amount >= remaining:
                            self.inventory[resource] = player_amount - remaining
                        else:
                            # Not enough resources, stop production
                            machine.is_active = False
                            break
                
                if machine.is_active:
                    # Produce outputs
                    for resource, amount in machine.recipe.outputs.items():
                        produced = amount * progress
                        machine.inventory[resource] = machine.inventory.get(resource, 0) + produced
    
    async def extract_from_machine(self, machine_id: str, resource: ResourceType, amount: float) -> bool:
        """Extract resources from machine inventory"""
        if machine_id not in self.machines:
            return False
        
        machine = self.machines[machine_id]
        available = machine.inventory.get(resource, 0)
        
        if available >= amount:
            machine.inventory[resource] = available - amount
            self.inventory[resource] = self.inventory.get(resource, 0) + amount
            return True
        
        return False
    
    async def insert_to_machine(self, machine_id: str, resource: ResourceType, amount: float) -> bool:
        """Insert resources into machine inventory"""
        if machine_id not in self.machines:
            return False
        
        machine = self.machines[machine_id]
        available = self.inventory.get(resource, 0)
        
        if available >= amount:
            self.inventory[resource] = available - amount
            machine.inventory[resource] = machine.inventory.get(resource, 0) + amount
            return True
        
        return False
    
    def get_factory_status(self) -> Dict[str, Any]:
        """Get current factory status"""
        active_machines = sum(1 for m in self.machines.values() if m.is_active)
        total_power = sum(m.power_consumption for m in self.machines.values() if m.is_active)
        
        return {
            "machines": len(self.machines),
            "active_machines": active_machines,
            "total_power_consumption": total_power,
            "inventory": {r.value: v for r, v in self.inventory.items()},
            "machines_detail": [
                {
                    "id": m.id,
                    "type": m.type.value,
                    "position": m.position,
                    "recipe": m.recipe.name if m.recipe else None,
                    "is_active": m.is_active,
                    "inventory": {r.value: v for r, v in m.inventory.items()}
                }
                for m in self.machines.values()
            ]
        }
    
    def get_available_recipes(self) -> List[Dict[str, Any]]:
        """Get all available recipes"""
        return [
            {
                "id": recipe.id,
                "name": recipe.name,
                "inputs": {r.value: v for r, v in recipe.inputs.items()},
                "outputs": {r.value: v for r, v in recipe.outputs.items()},
                "energy_required": recipe.energy_required,
                "machine_type": recipe.machine_type.value
            }
            for recipe in self.recipes.values()
        ]


# Example usage
async def main():
    """Example factory client usage"""
    client = FactoryClient("player_123", "building_456", "http://localhost:8000")
    
    # Place some machines
    furnace = await client.place_machine(MachineType.SMELTER, {"x": 5, "y": 5})
    assembler = await client.place_machine(MachineType.ASSEMBLER, {"x": 10, "y": 5})
    
    # Set recipes
    await client.set_machine_recipe(furnace.id, "iron_plate")
    await client.set_machine_recipe(assembler.id, "electronic_circuit")
    
    # Add some resources to inventory
    client.inventory[ResourceType.IRON_ORE] = 100
    client.inventory[ResourceType.COPPER_ORE] = 50
    
    # Start production
    await client.start_production(furnace.id)
    
    # Update production
    for _ in range(10):
        await client.update_production(1.0)  # 1 second updates
        status = client.get_factory_status()
        print(f"Active machines: {status['active_machines']}")
        print(f"Iron plates in furnace: {status['machines_detail'][0]['inventory'].get('iron_plate', 0)}")
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
