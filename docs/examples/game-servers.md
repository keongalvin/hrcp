# Game Server Configuration

Configure game servers with region-specific settings.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="game")

# Global game settings
tree.root.set_attribute("version", "2.1.0")
tree.root.set_attribute("tick_rate", 64)
tree.root.set_attribute("max_players", 100)
tree.root.set_attribute("anti_cheat", {"enabled": True, "level": "standard"})
tree.root.set_attribute("matchmaking", {
    "skill_range": 500,
    "wait_time_max": 120,
    "backfill": True
})

# Regional configurations
regions = {
    "na-east": {"latency_target": 30, "datacenter": "nyc"},
    "na-west": {"latency_target": 35, "datacenter": "lax"},
    "eu-west": {"latency_target": 25, "datacenter": "ams"},
    "asia": {"latency_target": 40, "datacenter": "sgp"},
}

for region, attrs in regions.items():
    tree.create(f"/game/{region}", attributes=attrs)
    # Each region has multiple server pools
    tree.create(f"/game/{region}/ranked", attributes={
        "mode": "ranked",
        "anti_cheat": {"level": "strict"},
        "matchmaking": {"skill_range": 200}
    })
    tree.create(f"/game/{region}/casual", attributes={
        "mode": "casual",
        "matchmaking": {"skill_range": 1000, "backfill": True}
    })

# Tournament servers with special config
tree.create("/game/tournament", attributes={
    "tick_rate": 128,
    "max_players": 10,
    "anti_cheat": {"enabled": True, "level": "maximum"},
    "matchmaking": {"skill_range": 0, "wait_time_max": 300}
})

def get_server_config(tree, server_path):
    """Get full server configuration."""
    server = tree.get(server_path)
    return {
        "version": get_value(server, "version", PropagationMode.DOWN),
        "tick_rate": get_value(server, "tick_rate", PropagationMode.DOWN),
        "max_players": get_value(server, "max_players", PropagationMode.DOWN),
        "latency_target": get_value(server, "latency_target", PropagationMode.DOWN),
        "anti_cheat": get_value(server, "anti_cheat", PropagationMode.MERGE_DOWN),
        "matchmaking": get_value(server, "matchmaking", PropagationMode.MERGE_DOWN),
    }

# Compare ranked vs casual in NA-East
ranked = get_server_config(tree, "/game/na-east/ranked")
casual = get_server_config(tree, "/game/na-east/casual")

print("NA-East Ranked:")
print(f"  Skill range: {ranked['matchmaking']['skill_range']}")  # 200
print(f"  Anti-cheat: {ranked['anti_cheat']['level']}")          # strict

print("\nNA-East Casual:")
print(f"  Skill range: {casual['matchmaking']['skill_range']}")  # 1000
print(f"  Anti-cheat: {casual['anti_cheat']['level']}")          # standard

# Tournament config
tournament = get_server_config(tree, "/game/tournament")
print(f"\nTournament tick rate: {tournament['tick_rate']}")      # 128
```

## Key Patterns

- **Global game settings** (version, tick rate) at root
- **Regional customization** for latency targets and datacenters
- **Game mode variations** (ranked, casual, tournament)
- **MERGE_DOWN** for anti-cheat and matchmaking allows granular control
