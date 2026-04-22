from db import player_repo, world_repo, graph_repo, story_repo, quest_repo
from models.llm_response import StateUpdate


class StateManager:
    """
    Validates player actions against the symbolic DB and applies
    all state updates returned by the LLM.
    """

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_action(self, action: str, player: dict) -> dict:
        """
        Cheap pre-flight check before rolling dice.
        Returns {"ok": bool, "notes": str}.
        """
        action_l = action.lower()
        notes    = []

        # Health gate — very low HP should warn narrator
        if player["health"] <= 15:
            notes.append("The player is critically wounded (low HP). Narrate their weakened state.")

        # Gold check for buying keywords
        if any(w in action_l for w in ("buy", "purchase", "pay")) and player["gold"] < 5:
            notes.append("Player has almost no gold — they cannot afford much.")

        return {"ok": True, "notes": " ".join(notes)}

    # ── State Application ─────────────────────────────────────────────────────

    def apply_updates(self, player_id: int, world_id: int, update: StateUpdate) -> list[str]:
        player = player_repo.get_player(player_id)
        if not player:
            return []
        
        notices = []

        # ── Stats
        if update.stat_changes:
            new_vals = {}
            for stat, delta in update.stat_changes.items():
                if stat in ("strength", "intelligence", "agility", "health", "gold"):
                    old_val = player[stat]
                    new_val = old_val + delta
                    
                    # Enforce caps/floors for core stats (1-20)
                    if stat in ("strength", "intelligence", "agility"):
                        new_val = max(1, min(new_val, 20))
                    else:
                        new_val = max(0, new_val) # Health/Gold just floored at 0
                    
                    if new_val != old_val:
                        new_vals[stat] = new_val
                        symbol = "+" if delta > 0 else ""
                        notices.append(f"[{stat.upper()[:3]} {symbol}{new_val - old_val}]")

            if new_vals:
                player_repo.update_player_stats(player_id, **new_vals)

        # ── Gold (legacy field, keeping for compatibility)
        if update.gold_change:
            new_gold = max(0, player["gold"] + update.gold_change)
            if new_gold != player["gold"]:
                player_repo.update_player_stats(player_id, gold=new_gold)
                symbol = "+" if update.gold_change > 0 else ""
                notices.append(f"[GOLD {symbol}{new_gold - player['gold']}]")

        # ── Inventory gains
        for item_name in update.items_gained:
            player_repo.add_item(player_id, item_name)
            notices.append(f"[ITEM + {item_name}]")

        # ── Inventory losses
        for item_name in update.items_lost:
            if player_repo.remove_item(player_id, item_name):
                notices.append(f"[ITEM - {item_name}]")

        # ── Quest updates
        for qu in update.quest_updates:
            if not isinstance(qu, dict):
                # If it's a narrative progress string, append it to the quest's hints log
                active_q = quest_repo.get_active_quest(world_id, player_id)
                if active_q:
                    hints = active_q.get("hints", [])
                    if qu not in hints:
                        hints.append(qu)
                        quest_repo.update_quest(active_q["id"], hints=hints)
                        notices.append("[QUEST PROGRESS]")
                continue
            qid    = qu.get("quest_id")
            status = qu.get("status", "").upper()
            if qid and status in ("COMPLETED", "FAILED", "ACTIVE", "INACTIVE"):
                quest_repo.update_quest_status(qid, status)
                notices.append(f"[QUEST {status}]")
                # Apply quest reward on completion
                if status == "COMPLETED":
                    self._apply_quest_reward(player_id, world_id, qid)

        # ── Relationship changes
        for rc in update.relationship_changes:
            src  = rc.get("source", "")
            tgt  = rc.get("target", "")
            rel  = rc.get("type", "Neutral")
            w    = float(rc.get("weight", 0.6))
            if src and tgt:
                graph_repo.upsert_edge(world_id, src, tgt, rel, w)
        
        return notices

    def _apply_quest_reward(self, player_id: int, world_id: int, quest_id: int):
        quest = quest_repo.get_active_quest(world_id, player_id)
        if not quest or quest["id"] != quest_id:
            return
        player = player_repo.get_player(player_id)
        if not player:
            return
        if quest["reward_gold"]:
            player_repo.update_player_stats(player_id, gold=player["gold"] + quest["reward_gold"])
        for item in quest.get("reward_items", []):
            player_repo.add_item(player_id, item, "misc")
