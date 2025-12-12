# -------------------- UTILITIES --------------------
import json
import os
import random
import time
from typing import Dict, List

from main import FRAGMENTS_REQUIRED, ROOMS, SAVE_FILE


def slow(text: str, delay: float = 0.01):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def newline():
    print()

def press_enter():
    input("\n(Press Enter to continue...)")

# -------------------- WEAPONS --------------------
WEAPONS = {
    "Rusty Pipe": {"damage": 9, "durability": 20, "special": None},
    "Kitchen Knife": {"damage": 14, "durability": 15, "special": "Bleed"},
    "Revolver": {"damage": 26, "durability": 12, "special": "Critical"}
}

# -------------------- PLAYER --------------------
class Player:
    def __init__(self):
        self.max_health = 120
        self.health = 100
        self.inventory: List[str] = []
        self.weapon: str = None
        self.location: str = "Lobby"
        self.flashlight_on: bool = False
        self.flashlight_battery: int = 60
        self.map_fragments_found: int = 0
        self.map_unlocked: bool = False
        self.has_master_key: bool = False
        self.is_alive: bool = True
        self.visited_rooms: set = set(["Lobby"])

    def to_dict(self) -> Dict:
        return {
            "max_health": self.max_health,
            "health": self.health,
            "inventory": self.inventory,
            "weapon": self.weapon,
            "location": self.location,
            "flashlight_on": self.flashlight_on,
            "flashlight_battery": self.flashlight_battery,
            "map_fragments_found": self.map_fragments_found,
            "map_unlocked": self.map_unlocked,
            "has_master_key": self.has_master_key,
            "is_alive": self.is_alive,
            "visited_rooms": list(self.visited_rooms)
        }

    def from_dict(self, data: Dict):
        self.max_health = data.get("max_health", 120)
        self.health = data.get("health", 100)
        self.inventory = data.get("inventory", [])
        self.weapon = data.get("weapon", None)
        self.location = data.get("location", "Lobby")
        self.flashlight_on = data.get("flashlight_on", False)
        self.flashlight_battery = data.get("flashlight_battery", 60)
        self.map_fragments_found = data.get("map_fragments_found", 0)
        self.map_unlocked = data.get("map_unlocked", False)
        self.has_master_key = data.get("has_master_key", False)
        self.is_alive = data.get("is_alive", True)
        self.visited_rooms = set(data.get("visited_rooms", ["Lobby"]))

# -------------------- ENEMIES --------------------
ENEMY_TYPES = [
    {"name": "Shadow Minion", "min_hp": 18, "max_hp": 36, "min_dmg": 5, "max_dmg": 14},
    {"name": "Crawling Demon", "min_hp": 24, "max_hp": 40, "min_dmg": 8, "max_dmg": 16},
    {"name": "Twisted Bellhop", "min_hp": 20, "max_hp": 38, "min_dmg": 6, "max_dmg": 15}
]

BOSS = {"name": "The Matriarch", "hp": 180, "min_dmg": 12, "max_dmg": 26}

# -------------------- SAVE / LOAD --------------------
def auto_save(player: Player):
    data = player.to_dict()
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

def auto_load() -> Player:
    p = Player()
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            p.from_dict(data)
            slow("Loaded previous auto-save.")
        except:
            pass
    return p

# -------------------- INVENTORY & WEAPONS --------------------
def check_weapon(player: Player):
    if player.weapon:
        w = WEAPONS.get(player.weapon)
        slow(f"Equipped: {player.weapon} | Damage: {w['damage']} | Durability: {w['durability']} | Special: {w['special']}")
    else:
        slow("No weapon equipped.")

def switch_weapon(player: Player):
    weapons_in_inventory = [item for item in player.inventory if item in WEAPONS]
    if not weapons_in_inventory:
        slow("You have no weapons to equip.")
        return
    slow("Choose a weapon to equip:")
    for i, w in enumerate(weapons_in_inventory, 1):
        slow(f"[{i}] {w} (Damage: {WEAPONS[w]['damage']}, Durability: {WEAPONS[w]['durability']})")
    choice = input("> ")
    if choice.isdigit() and 1 <= int(choice) <= len(weapons_in_inventory):
        player.weapon = weapons_in_inventory[int(choice)-1]
        slow(f"You equip {player.weapon}.")
    else:
        slow("Invalid choice.")

def drop_weapon(player: Player):
    weapons_in_inventory = [item for item in player.inventory if item in WEAPONS]
    if not weapons_in_inventory:
        slow("No weapons to drop.")
        return
    slow("Which weapon do you want to drop?")
    for i, w in enumerate(weapons_in_inventory, 1):
        slow(f"[{i}] {w}")
    choice = input("> ")
    if choice.isdigit() and 1 <= int(choice) <= len(weapons_in_inventory):
        w = weapons_in_inventory[int(choice)-1]
        player.inventory.remove(w)
        if player.weapon == w:
            player.weapon = None
        slow(f"You dropped {w}.")
    else:
        slow("Invalid choice.")

# -------------------- FLASHLIGHT & MAP --------------------
def toggle_flashlight(player: Player):
    if player.flashlight_on:
        player.flashlight_on = False
        slow("You switch the flashlight off.")
    else:
        if player.flashlight_battery <= 0:
            slow("The flashlight won't turn on — no battery power left.")
            return
        player.flashlight_on = True
        slow("You switch the flashlight on.")
    auto_save(player)

def drain_flashlight(player: Player, amount=8):
    if player.flashlight_on:
        player.flashlight_battery -= amount
        if player.flashlight_battery <= 0:
            player.flashlight_battery = 0
            player.flashlight_on = False
            slow("Your flashlight dies. Darkness surrounds you.")
            auto_save(player)

def use_batteries(player: Player):
    if "Batteries" in player.inventory:
        player.inventory.remove("Batteries")
        player.flashlight_battery = min(100, player.flashlight_battery + 50)
        slow("You recharge your flashlight.")
        auto_save(player)
    else:
        slow("No batteries available.")

def show_map(player: Player):
    if not player.map_unlocked:
        slow("You haven't repaired the map yet.")
    else:
        slow("\n-- MAP REPAIRED --")
        slow("Lobby -> Left Hall -> Rooms -> Stairwell -> Attic -> Boss Chamber etc.")

# -------------------- ITEM PICKUP --------------------
def find_items_in_room(player: Player, room_name: str):
    room = ROOMS[room_name]
    found_any = False
    while room["items"]:
        item = room["items"].pop(0)
        if item.startswith("Map Fragment"):
            player.map_fragments_found += 1
            slow(f"You found {item}!")
            found_any = True
            if player.map_fragments_found >= FRAGMENTS_REQUIRED:
                player.map_unlocked = True
                slow("All map fragments collected. The map repairs itself.")
        else:
            player.inventory.append(item)
            slow(f"You pick up: {item}")
            if item in WEAPONS and not player.weapon:
                player.weapon = item
                slow(f"You equip {item}.")
            found_any = True
        auto_save(player)
    return found_any

# -------------------- ENEMY ENCOUNTER --------------------
def encounter_enemy(player: Player) -> bool:
    enemy = random.choice(ENEMY_TYPES)
    enemy_hp = random.randint(enemy["min_hp"], enemy["max_hp"])
    slow(f"A {enemy['name']} attacks! HP: {enemy_hp}")
    while enemy_hp > 0 and player.health > 0:
        slow(f"Your HP: {player.health} | {enemy['name']} HP: {enemy_hp}")
        action = input("[A]ttack  [H]eal  [R]un  [W]eapon Switch  > ").strip().lower()
        if action in ("a", "attack"):
            if player.weapon:
                w = WEAPONS[player.weapon]
                damage = w["damage"] + random.randint(0,5)
                enemy_hp -= damage
                w["durability"] -= 1
                slow(f"You hit {enemy['name']} with {player.weapon} for {damage} damage. Durability left: {w['durability']}")
                if w["durability"] <= 0:
                    slow(f"Your {player.weapon} breaks!")
                    player.inventory.remove(player.weapon)
                    player.weapon = None
            else:
                damage = random.randint(3,8)
                enemy_hp -= damage
                slow(f"You punch for {damage} damage.")
        elif action in ("h", "heal"):
            if "Health Pack" in player.inventory:
                player.inventory.remove("Health Pack")
                healed = min(player.max_health - player.health, 30)
                player.health += healed
                slow(f"You use a Health Pack. HP +{healed}")
                auto_save(player)
            else:
                slow("No Health Packs.")
        elif action in ("r", "run"):
            if random.random() > 0.5:
                slow("You escape successfully!")
                return False
            else:
                slow("Failed to escape!")
        elif action in ("w", "weapon switch"):
            switch_weapon(player)
            continue
        else:
            slow("Invalid action.")
            continue

        if enemy_hp > 0:
            hit = random.randint(enemy["min_dmg"], enemy["max_dmg"])
            player.health -= hit
            slow(f"{enemy['name']} hits you for {hit} damage.")
            drain_flashlight(player, 4)

    if player.health <= 0:
        slow("You have been slain...")
        player.is_alive = False
        auto_save(player)
        return True

    slow(f"You defeat the {enemy['name']}.")
    if random.random() > 0.6:
        loot = random.choice(["Health Pack","Batteries"])
        player.inventory.append(loot)
        slow(f"The {enemy['name']} dropped: {loot}")
        auto_save(player)
    return False

# -------------------- BOSS FIGHT --------------------
def boss_battle(player: Player):
    slow("\nThe Matriarch looms before you!")
    boss_hp = BOSS["hp"]
    while boss_hp > 0 and player.health > 0:
        slow(f"Your HP: {player.health} | Matriarch HP: {boss_hp}")
        action = input("[A]ttack  [H]eal  [S]hutdown flashlight  [F]lashlight  [W]eapon Switch  > ").strip().lower()
        if action in ("a","attack"):
            if player.weapon:
                w = WEAPONS[player.weapon]
                dmg = w["damage"] + random.randint(5,10)
                boss_hp -= dmg
                w["durability"] -= 1
                slow(f"You hit Matriarch with {player.weapon} for {dmg}. Durability: {w['durability']}")
                if w["durability"] <= 0:
                    slow(f"Your {player.weapon} breaks!")
                    player.inventory.remove(player.weapon)
                    player.weapon = None
            else:
                dmg = random.randint(5,9)
                boss_hp -= dmg
                slow(f"You attack with fists for {dmg}")
        elif action in ("h","heal"):
            if "Health Pack" in player.inventory:
                player.inventory.remove("Health Pack")
                healed = min(player.max_health - player.health, 40)
                player.health += healed
                slow(f"Heal +{healed}")
            else:
                slow("No Health Packs.")
        elif action in ("s","shut"):
            player.flashlight_on = False
            slow("You turn off flashlight.")
        elif action in ("f","flashlight"):
            toggle_flashlight(player)
        elif action in ("w","weapon switch"):
            switch_weapon(player)
        else:
            slow("Invalid action.")
            continue

        hit = random.randint(BOSS["min_dmg"], BOSS["max_dmg"])
        player.health -= hit
        slow(f"Matriarch hits you for {hit} damage!")
        if random.random() > 0.7:
            slow("Matriarch summons a minion!")
            if encounter_enemy(player):
                return

        drain_flashlight(player, 6)
        auto_save(player)

    if player.health <= 0:
        ending_consumed()
    else:
        slow("Matriarch defeated! You find a note: 'Wake me.'")
        ending_escape()

# -------------------- ENDINGS --------------------
def ending_escape():
    slow("\nLight pierces your eyes. You wake in a hospital.")
    slow("You've been in a coma for weeks. Floor 13 is behind you.")
    try: os.remove(SAVE_FILE)
    except: pass
    exit(0)

def ending_consumed():
    slow("\nYou are consumed by the darkness. Forever lost in Floor 13.")
    try: os.remove(SAVE_FILE)
    except: pass
    exit(0)

def ending_trapped_forever():
    slow("\nThe hotel stretches endlessly. You are trapped forever.")
    try: os.remove(SAVE_FILE)
    except: pass
    exit(0)
