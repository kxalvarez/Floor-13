"""
FLOOR 13 - Text Horror Adventure
Features:
- 13 connected rooms (the hotel)
- Inventory, weapons, health packs, batteries
- Flashlight (on/off) that drains while on; some rooms require light
- Map fragments to collect and repair the map; map unlocks when all fragments found
- Auto-save (savegame.json) after major events
- Random demon minion encounters; boss (The Matriarch)
- Weapon system: damage, durability, switching, dropping
- Multiple endings: Escape (coma), Consumed, Trapped Forever
"""

import json
import random
import time
import os
from typing import Dict, List

SAVE_FILE = "savegame.json"

# -------------------- UTILITIES --------------------
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

# -------------------- ROOMS --------------------
ROOMS = {
    "Lobby": {"desc": "An echoing hotel lobby, faded wallpaper, a broken chandelier.",
              "adj": ["Left Hall", "Right Hall", "Stairwell"], "required_light": False,
              "items": ["Map Fragment A"], "chance_enemy": 0.2, "is_fragment_room": True, "fragment_id": 1},
    "Left Hall": {"desc": "A long corridor with locked doors and peeling carpet.",
                  "adj": ["Room 101", "Room 102", "Lobby"], "required_light": False,
                  "items": ["Rusty Pipe"], "chance_enemy": 0.3, "is_fragment_room": False, "fragment_id": None},
    "Right Hall": {"desc": "The right wing smells of rot. Footprints that go nowhere.",
                   "adj": ["Room 103", "Room 104", "Lobby"], "required_light": False,
                   "items": ["Health Pack"], "chance_enemy": 0.35, "is_fragment_room": False, "fragment_id": None},
    "Stairwell": {"desc": "A spiraling stairwell; the lights buzz and sometimes go out.",
                  "adj": ["Basement", "Attic", "Lobby"], "required_light": True,
                  "items": [], "chance_enemy": 0.4, "is_fragment_room": False, "fragment_id": None},
    "Room 101": {"desc": "A child's drawing pinned to the wall. The bed is soaked.",
                 "adj": ["Left Hall"], "required_light": True,
                 "items": ["Map Fragment B"], "chance_enemy": 0.5, "is_fragment_room": True, "fragment_id": 2},
    "Room 102": {"desc": "Furniture strewn about. A lamp that never fully lights.",
                 "adj": ["Left Hall"], "required_light": False,
                 "items": ["Batteries"], "chance_enemy": 0.4, "is_fragment_room": False, "fragment_id": None},
    "Room 103": {"desc": "A mirror that doesn't reflect your face properly.",
                 "adj": ["Right Hall"], "required_light": True,
                 "items": ["Kitchen Knife"], "chance_enemy": 0.45, "is_fragment_room": False, "fragment_id": None},
    "Room 104": {"desc": "Scratches on the walls in a frantic pattern.",
                 "adj": ["Right Hall"], "required_light": False,
                 "items": ["Map Fragment C"], "chance_enemy": 0.5, "is_fragment_room": True, "fragment_id": 3},
    "Basement": {"desc": "Rusty boilers and a damp smell; something moves in the pipes.",
                 "adj": ["Boiler Room", "Stairwell"], "required_light": True,
                 "items": ["Health Pack", "Batteries"], "chance_enemy": 0.55, "is_fragment_room": False, "fragment_id": None},
    "Boiler Room": {"desc": "Machines clank. Shadows crawl between the furnaces.",
                    "adj": ["Basement"], "required_light": True,
                    "items": ["Map Fragment D"], "chance_enemy": 0.6, "is_fragment_room": True, "fragment_id": 4},
    "Attic": {"desc": "Cobwebs and trunks. Something whispers from a trunk.",
              "adj": ["Stairwell", "Room 105"], "required_light": True,
              "items": ["Revolver"], "chance_enemy": 0.5, "is_fragment_room": False, "fragment_id": None},
    "Room 105": {"desc": "A bathroom mirror cracked with a message: 'DON'T WAKE HER.'",
                 "adj": ["Attic", "Room 106"], "required_light": False,
                 "items": ["Map Fragment E"], "chance_enemy": 0.45, "is_fragment_room": True, "fragment_id": 5},
    "Room 106": {"desc": "A hallway inside a room; doors lead to nowhere.",
                 "adj": ["Room 105", "Room 107"], "required_light": True,
                 "items": ["Health Pack"], "chance_enemy": 0.5, "is_fragment_room": False, "fragment_id": None},
    "Room 107": {"desc": "A door with thirteen brass numbers, cold to the touch.",
                 "adj": ["Room 106", "Boss Antechamber"], "required_light": True,
                 "items": ["Map Fragment F"], "chance_enemy": 0.6, "is_fragment_room": True, "fragment_id": 6},
    "Boss Antechamber": {"desc": "A corridor of carpets stained black; a scent like old blood.",
                         "adj": ["Room 107", "Boss Chamber"], "required_light": True,
                         "items": ["Master Key"], "chance_enemy": 0.65, "is_fragment_room": False, "fragment_id": None},
    "Boss Chamber": {"desc": "A vast room where the air itself bends. The Matriarch waits.",
                     "adj": ["Boss Antechamber"], "required_light": True,
                     "items": [], "chance_enemy": 0.0, "is_fragment_room": False, "fragment_id": None}
}

FRAGMENTS_REQUIRED = 6

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

# -------------------- NAVIGATION --------------------
def move_to_room(player: Player, dest: str):
    if dest not in ROOMS[player.location]["adj"]:
        slow("Cannot go there directly.")
        return
    if ROOMS[dest]["required_light"] and not player.flashlight_on:
        slow("Too dark to enter without flashlight.")
        return
    player.location = dest
    player.visited_rooms.add(dest)
    drain_flashlight(player, 6)
    auto_save(player)
    slow(f"You move into {dest}")
    if not find_items_in_room(player, dest):
        slow(ROOMS[dest]["desc"])
    if ROOMS[dest]["chance_enemy"] > 0 and random.random() < ROOMS[dest]["chance_enemy"]:
        if encounter_enemy(player):
            ending_consumed()
    if dest == "Boss Antechamber" and "Master Key" in player.inventory:
        slow("Door to Boss Chamber unlocked.")
    if dest == "Boss Chamber":
        if player.has_master_key or random.random() > 0.5:
            slow("You confront the Matriarch.")
            boss_battle(player)
        else:
            slow("You feel a wrong step... darkness surrounds you.")
            boss_battle(player)

# -------------------- STATUS & INVENTORY --------------------
def show_status(player: Player):
    slow(f"Location: {player.location} | HP: {player.health}/{player.max_health}")
    slow(f"Weapon: {player.weapon} | Flashlight: {'ON' if player.flashlight_on else 'OFF'} ({player.flashlight_battery}%)")
    slow(f"Map fragments: {player.map_fragments_found}/{FRAGMENTS_REQUIRED}")
    slow(f"Master Key: {'Yes' if player.has_master_key else 'No'}")

def show_inventory(player: Player):
    slow("INVENTORY:")
    if not player.inventory:
        slow("- Empty")
    else:
        for item in player.inventory:
            slow(f"- {item}")
    check_weapon(player)

# -------------------- INTRO & MAIN LOOP --------------------
def intro():
    slow("You awaken in darkness. A brass plate reads 'FLOOR 13'. You must escape.")
    press_enter()

def main_loop():
    player = auto_load()
    if not os.path.exists(SAVE_FILE):
        intro()
        auto_save(player)
    else:
        slow(f"Resuming at {player.location}")
        press_enter()

    while player.is_alive:
        show_status(player)
        slow("Actions: [move] [inventory] [flashlight] [map] [use batteries] [quit]")
        action = input("> ").strip().lower()
        if action == "move":
            adj = ROOMS[player.location]["adj"]
            slow("From here you can go: " + ", ".join(adj))
            dest = input("Where to? ").strip()
            if dest in ROOMS:
                move_to_room(player, dest)
            else:
                slow("Unknown location.")
        elif action == "inventory":
            show_inventory(player)
            slow("[S]witch weapon, [D]rop weapon, [Enter] back")
            sub = input("> ").strip().lower()
            if sub == "s":
                switch_weapon(player)
            elif sub == "d":
                drop_weapon(player)
        elif action == "flashlight":
            toggle_flashlight(player)
        elif action == "map":
            show_map(player)
        elif action == "use batteries":
            use_batteries(player)
        elif action == "quit":
            slow("Quit? [y/N]")
            if input("> ").lower() == "y":
                auto_save(player)
                exit(0)
        else:
            slow("Unknown command.")

        if player.health <= 0:
            ending_consumed()
        auto_save(player)

        if len(player.visited_rooms) > 30 and player.map_fragments_found < 2:
            ending_trapped_forever()

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        slow("\nExiting game (auto-saved).")
        exit(0)