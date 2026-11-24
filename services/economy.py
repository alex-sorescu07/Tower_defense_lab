class EconomyService:
    def init(self, start_coins: int) -> None:
        self.coins: int = start_coins
        self.coins_spent: int = 0
        self.kills: int = 0

    def can_afford(self, cost: int) -> bool:
        return self.coins >= cost

    def spend(self, cost: int) -> bool:
        if not self.can_afford(cost):
            return False
        self.coins -= cost
        self.coins_spent += cost
        return True

    def claim_enemy_reward(self, enemy: Enemy) -> int:
        """Acordă recompensa o singură dată la eliminarea inamicului."""
        if not enemy.alive and not enemy.reached_base and not enemy.reward_claimed:
            enemy.reward_claimed = True
            self.coins += enemy.reward
            self.kills += 1
            return enemy.reward
        return 0

    def upgrade_tower(self, tower: Tower) -> bool:
        """Permite exact 1 upgrade per turn dacă există fonduri suficiente."""
        if tower.upgraded:
            return False
        if not self.spend(tower.upgrade_cost):
            return False
        return tower.apply_upgrade()
