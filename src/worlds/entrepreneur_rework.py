import math
import random
import tkinter as tk
from typing import Any

from src.player import Player
from src.utils import HEIGHT, WIDTH, clamp
from src.worlds.base import BaseWorld


class TycoonWorld(BaseWorld):
    TOP_BAR_H = 44
    FOOTER_H = 28
    INFO_PANEL_H = 110
    SIDE_PANEL_W = 244
    BOARD_TOP = 58
    BOARD_BOTTOM = HEIGHT - 154
    BOARD_LEFT = 18
    BOARD_RIGHT = WIDTH - SIDE_PANEL_W - 18

    def __init__(self) -> None:
        super().__init__(
            name="Tycoon Empire",
            summary="Scout opportunities, manage a realistic portfolio, and finish the quarter with strong cash flow.",
            duration=240.0,
        )
        self.briefing = [
            "Start with $80,000 and build a balanced business empire.",
            "Every opportunity has tradeoffs: yield, maintenance, volatility, and market trend.",
            "Real estate pays slower but steadier cash flow. Funds and crypto move faster but swing harder.",
            "Buy from the board, review holdings in the portfolio, and sell weak positions before they drain you.",
            "Reach $180,000 net worth with positive cash flow before time expires.",
            "Research deals, negotiate discounts, and service operating issues to protect returns.",
        ]
        self.hints = [
            "Move with WASD or arrows. Stand near a deal and press SPACE to inspect it.",
            "Press R to research a highlighted deal and F to negotiate its asking price.",
            "Orange service calls appear on holdings you own. Move there and press E to resolve them.",
            "Press P to review holdings and ENTER to sell the selected position.",
            "Press M for the market board to see prices, drift, and recent events.",
            "Press L to borrow working capital and K to pay debt back down.",
            "Cash flow matters. This version moves slower, so active management matters more.",
        ]
        self.asset_specs: dict[str, dict[str, Any]] = {
            "apartment": {"label": "Apartment Building", "sector": "real_estate", "price_key": "real_estate", "price_scale": 1.18, "yield_range": (0.070, 0.100), "expense_range": (0.015, 0.028), "volatility": 0.05, "color": "#4dabf7", "icon": "APT"},
            "retail": {"label": "Retail Plaza", "sector": "real_estate", "price_key": "real_estate", "price_scale": 0.95, "yield_range": (0.078, 0.110), "expense_range": (0.018, 0.030), "volatility": 0.06, "color": "#51cf66", "icon": "RTL"},
            "logistics": {"label": "Logistics Hub", "sector": "industrial", "price_key": "industrial", "price_scale": 1.10, "yield_range": (0.072, 0.098), "expense_range": (0.013, 0.024), "volatility": 0.05, "color": "#15aabf", "icon": "IND"},
            "tech_fund": {"label": "Tech Growth Fund", "sector": "tech_fund", "price_key": "tech_fund", "price_scale": 1.0, "yield_range": (0.010, 0.020), "expense_range": (0.001, 0.003), "volatility": 0.14, "color": "#845ef7", "icon": "ETF"},
            "dividend_fund": {"label": "Dividend Fund", "sector": "dividend_fund", "price_key": "dividend_fund", "price_scale": 1.0, "yield_range": (0.038, 0.058), "expense_range": (0.001, 0.002), "volatility": 0.08, "color": "#fcc419", "icon": "DIV"},
            "bond_ladder": {"label": "Bond Ladder", "sector": "bond_ladder", "price_key": "bond_ladder", "price_scale": 1.0, "yield_range": (0.040, 0.055), "expense_range": (0.000, 0.001), "volatility": 0.03, "color": "#94d82d", "icon": "BND"},
            "crypto_miner": {"label": "Crypto Position", "sector": "crypto_miner", "price_key": "crypto_miner", "price_scale": 1.0, "yield_range": (-0.010, 0.012), "expense_range": (0.002, 0.006), "volatility": 0.20, "color": "#ff922b", "icon": "CRY"},
        }
        self.board_zones = [
            {"name": "Midtown", "x": 180.0, "y": 155.0, "radius": 88.0, "focus": ("apartment", "retail")},
            {"name": "Industrial Ring", "x": self.BOARD_RIGHT - 120.0, "y": 155.0, "radius": 82.0, "focus": ("logistics", "bond_ladder")},
            {"name": "Capital Row", "x": 180.0, "y": 320.0, "radius": 86.0, "focus": ("dividend_fund", "bond_ladder")},
            {"name": "Founder District", "x": self.BOARD_RIGHT - 120.0, "y": 320.0, "radius": 94.0, "focus": ("tech_fund", "crypto_miner")},
        ]
        self.target_net_worth = 180000.0
        self.starting_cash = 80000.0
        self.seconds_per_year = 28.0
        self.market_timer = 0.0
        self.spawn_timer = 0.0
        self.event_timer = 0.0
        self.event_message = ""
        self.task_spawn_timer = 0.0
        self.ui_state = "game"
        self.cash = self.starting_cash
        self.net_worth = self.starting_cash
        self.total_profit = 0.0
        self.monthly_cash_flow = 0.0
        self.market_prices: dict[str, float] = {}
        self.market_drifts: dict[str, float] = {}
        self.price_history: dict[str, list[float]] = {}
        self.properties: list[dict[str, Any]] = []
        self.portfolio: list[dict[str, Any]] = []
        self.active_tasks: list[dict[str, Any]] = []
        self.transaction_history: list[str] = []
        self.highlighted_property = -1
        self.highlighted_task = -1
        self.selected_detail_idx = -1
        self.selected_portfolio_idx = 0
        self.achievements: list[str] = []
        self.buy_count = 0
        self.sell_count = 0
        self.peak_net_worth = self.starting_cash
        self.message = ""
        self._pressed: dict[str, bool] = {}
        self.loan_balance = 0.0
        self.loan_rate = 0.082
        self.loan_increment = 25000.0
        self.reset_market_state()

    def down_payment_ratio(self, risk: float) -> float:
        # Keep deals accessible; higher risk still requires more equity up front.
        return clamp(0.12 + risk * 0.22, 0.12, 0.25)

    def reset_market_state(self) -> None:
        self.market_prices = {
            "real_estate": 52000.0,
            "industrial": 61000.0,
            "tech_fund": 21000.0,
            "dividend_fund": 17500.0,
            "bond_ladder": 12000.0,
            "crypto_miner": 16000.0,
        }
        self.market_drifts = {
            "real_estate": 0.030,
            "industrial": 0.036,
            "tech_fund": 0.065,
            "dividend_fund": 0.040,
            "bond_ladder": 0.026,
            "crypto_miner": 0.110,
        }
        self.price_history = {key: [value] for key, value in self.market_prices.items()}

    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, (self.BOARD_TOP + self.BOARD_BOTTOM) / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.grade = "-"
        self.message = "Scout the market and keep your empire solvent."
        self.shake = 0.0
        self.particles = []
        self.hint_display_timer = 0.0
        self.current_hint_index = 0
        self.cash = self.starting_cash
        self.net_worth = self.starting_cash
        self.total_profit = 0.0
        self.monthly_cash_flow = 0.0
        self.ui_state = "game"
        self.properties = []
        self.portfolio = []
        self.transaction_history = []
        self.highlighted_property = -1
        self.selected_detail_idx = -1
        self.selected_portfolio_idx = 0
        self.achievements = []
        self.buy_count = 0
        self.sell_count = 0
        self.peak_net_worth = self.starting_cash
        self.loan_balance = 0.0
        self.market_timer = 0.0
        self.spawn_timer = 0.0
        self.event_timer = 0.0
        self.event_message = ""
        self.task_spawn_timer = 6.0
        self._pressed = {}
        self.reset_market_state()
        self.active_tasks = []
        for _ in range(8):
            self.properties.append(self.spawn_property())

    def just_pressed(self, keys: set[str], key: str) -> bool:
        is_down = key in keys
        was_down = self._pressed.get(key, False)
        self._pressed[key] = is_down
        return is_down and not was_down

    def spawn_property(self) -> dict[str, Any]:
        zone = random.choice(self.board_zones)
        catalog = list(zone["focus"]) + random.sample(list(self.asset_specs.keys()), 2)
        asset_type = random.choice(catalog)
        spec = self.asset_specs[asset_type]
        angle = random.uniform(0.0, math.tau)
        radius = random.uniform(0.0, zone["radius"])
        x = clamp(zone["x"] + math.cos(angle) * radius, self.BOARD_LEFT + 52.0, self.BOARD_RIGHT - 52.0)
        y = clamp(zone["y"] + math.sin(angle) * radius, self.BOARD_TOP + 18.0, self.BOARD_BOTTOM - 18.0)
        market_price = self.market_prices[spec["price_key"]] * random.uniform(0.88, 1.12) * spec["price_scale"]
        annual_yield = random.uniform(*spec["yield_range"])
        annual_expense = random.uniform(*spec["expense_range"])
        return {
            "id": len(self.properties) + 1,
            "asset_type": asset_type,
            "name": f"{spec['label']} {random.randint(11, 98)}",
            "zone": zone["name"],
            "sector": spec["sector"],
            "price_key": spec["price_key"],
            "price": round(market_price, 2),
            "annual_yield": annual_yield,
            "annual_expense": annual_expense,
            "risk": spec["volatility"],
            "quality": random.uniform(0.82, 1.14),
            "occupancy": random.uniform(0.84, 0.98),
            "research": 0,
            "negotiated_discount": 0.0,
            "x": x,
            "y": y,
            "color": spec["color"],
            "icon": spec["icon"],
        }

    def trigger_market_event(self) -> None:
        events = [
            ("Rates ease, bond prices improve.", {"bond_ladder": 1.04, "real_estate": 1.02}),
            ("Industrial demand jumps with shipping volume.", {"industrial": 1.05}),
            ("Tech multiples compress on earnings misses.", {"tech_fund": 0.94}),
            ("Dividend buyers rotate into defensives.", {"dividend_fund": 1.04, "tech_fund": 0.98}),
            ("Crypto sentiment breaks sharply lower.", {"crypto_miner": 0.88}),
            ("Urban rents firm up across the market.", {"real_estate": 1.05}),
        ]
        text, effects = random.choice(events)
        for key, multiplier in effects.items():
            self.market_prices[key] *= multiplier
        self.event_message = text
        self.event_timer = 6.0

    def open_detail_for_highlight(self) -> None:
        if self.highlighted_property >= 0:
            self.selected_detail_idx = self.highlighted_property
            self.ui_state = "detail"

    def buy_selected_property(self) -> None:
        if self.selected_detail_idx < 0 or self.selected_detail_idx >= len(self.properties):
            return
        prop = self.properties[self.selected_detail_idx]
        price = float(prop["price"]) * (1.0 - float(prop.get("negotiated_discount", 0.0)))
        risk = float(prop["risk"])
        down_payment_ratio = self.down_payment_ratio(risk)
        down_payment = price * down_payment_ratio
        financed_amount = price - down_payment
        if self.cash < down_payment:
            self.message = "Not enough cash for the down payment."
            return
        annual_income = price * float(prop["annual_yield"]) * float(prop["occupancy"])
        annual_expense = price * float(prop["annual_expense"]) / max(0.70, float(prop["quality"]))
        annual_debt_service = financed_amount * self.loan_rate
        holding = {
            "name": str(prop["name"]),
            "asset_type": str(prop["asset_type"]),
            "zone": str(prop["zone"]),
            "sector": str(prop["sector"]),
            "price_key": str(prop["price_key"]),
            "purchase_price": price,
            "market_value": price,
            "annual_income": annual_income,
            "annual_expense": annual_expense,
            "quality": float(prop["quality"]),
            "risk": float(prop["risk"]),
            "cash_flow": annual_income - annual_expense - annual_debt_service,
            "profit": 0.0,
            "x": float(prop["x"]),
            "y": float(prop["y"]),
            "stress": 0.0,
            "loan_principal": financed_amount,
            "annual_debt_service": annual_debt_service,
            "down_payment": down_payment,
        }
        self.cash -= down_payment
        self.loan_balance += financed_amount
        self.portfolio.append(holding)
        self.transaction_history.append(f"BUY {holding['name']} for {self.money(down_payment)} down")
        self.transaction_history = self.transaction_history[-8:]
        self.properties.pop(self.selected_detail_idx)
        self.buy_count += 1
        self.selected_detail_idx = -1
        self.ui_state = "game"
        self.message = f"Acquired {holding['name']}."
        if "First Deal" not in self.achievements:
            self.achievements.append("First Deal")
        self.shake = 1.4

    def sell_selected_holding(self) -> None:
        if not self.portfolio:
            return
        self.selected_portfolio_idx = clamp(self.selected_portfolio_idx, 0, len(self.portfolio) - 1)
        index = int(self.selected_portfolio_idx)
        holding = self.portfolio.pop(index)
        sale_price = float(holding["market_value"]) * random.uniform(0.985, 1.015)
        payoff = min(sale_price, float(holding.get("loan_principal", 0.0)))
        self.loan_balance = max(0.0, self.loan_balance - payoff)
        self.cash += sale_price - payoff
        self.transaction_history.append(f"SELL {holding['name']} for {self.money(sale_price - payoff)} net")
        self.transaction_history = self.transaction_history[-8:]
        self.sell_count += 1
        self.message = f"Sold {holding['name']}."
        self.selected_portfolio_idx = max(0, min(index, len(self.portfolio) - 1))
        self.active_tasks = [task for task in self.active_tasks if task["holding_name"] != holding["name"]]

    def borrow_capital(self) -> None:
        self.cash += self.loan_increment
        self.loan_balance += self.loan_increment
        self.message = f"Borrowed {self.money(self.loan_increment)} in working capital."
        self.transaction_history.append(f"LOAN +{self.money(self.loan_increment)}")
        self.transaction_history = self.transaction_history[-8:]

    def repay_loan(self) -> None:
        if self.loan_balance <= 0.0:
            self.message = "No loan balance to repay."
            return
        payment = min(self.cash, self.loan_increment, self.loan_balance)
        if payment <= 0.0:
            self.message = "Need cash before paying down debt."
            return
        self.cash -= payment
        self.loan_balance -= payment
        self.message = f"Paid down {self.money(payment)} of debt."
        self.transaction_history.append(f"LOAN -{self.money(payment)}")
        self.transaction_history = self.transaction_history[-8:]

    def research_highlighted_property(self) -> None:
        if self.highlighted_property < 0:
            return
        prop = self.properties[self.highlighted_property]
        if int(prop.get("research", 0)) >= 2:
            self.message = f"{prop['name']} is already fully researched."
            return
        prop["research"] = int(prop.get("research", 0)) + 1
        prop["quality"] = min(1.25, float(prop["quality"]) + 0.03)
        prop["occupancy"] = min(0.99, float(prop["occupancy"]) + 0.02)
        self.message = f"Research complete on {prop['name']}."

    def negotiate_highlighted_property(self) -> None:
        if self.highlighted_property < 0:
            return
        prop = self.properties[self.highlighted_property]
        current_discount = float(prop.get("negotiated_discount", 0.0))
        if current_discount >= 0.08:
            self.message = f"{prop['name']} will not budge any further."
            return
        improvement = 0.02 + 0.01 * int(prop.get("research", 0))
        prop["negotiated_discount"] = min(0.08, current_discount + improvement)
        self.message = f"Negotiated {prop['name']} down to {self.money(float(prop['price']) * (1.0 - prop['negotiated_discount']))}."

    def resolve_highlighted_task(self) -> None:
        if self.highlighted_task < 0 or self.highlighted_task >= len(self.active_tasks):
            return
        task = self.active_tasks.pop(self.highlighted_task)
        for holding in self.portfolio:
            if holding["name"] != task["holding_name"]:
                continue
            holding["annual_expense"] *= 0.94
            holding["annual_income"] *= 1.02
            holding["stress"] = max(0.0, float(holding.get("stress", 0.0)) - 0.5)
            self.cash -= task["cost"]
            self.message = f"Resolved {task['title']} for {holding['name']}."
            break

    def update_market(self, dt: float) -> None:
        year_fraction = dt / self.seconds_per_year
        self.market_timer += dt
        if self.event_timer > 0.0:
            self.event_timer = max(0.0, self.event_timer - dt)
        for key, price in list(self.market_prices.items()):
            drift = self.market_drifts[key]
            noise = random.uniform(-1.0, 1.0) * (0.012 + abs(drift) * 0.18)
            growth = drift * year_fraction + noise * math.sqrt(year_fraction) * 0.06
            if key == "crypto_miner":
                growth *= 1.10
            new_price = max(3500.0, price * (1.0 + growth))
            self.market_prices[key] = new_price
            history = self.price_history[key]
            history.append(new_price)
            if len(history) > 180:
                history.pop(0)
        if self.market_timer >= 20.0:
            self.market_timer = 0.0
            if random.random() < 0.30:
                self.trigger_market_event()

    def update_properties(self, dt: float) -> None:
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self.spawn_timer = random.uniform(2.7, 4.6)
            if len(self.properties) < 12:
                self.properties.append(self.spawn_property())
        kept: list[dict[str, Any]] = []
        for prop in self.properties:
            if random.random() < 0.012 * dt:
                continue
            spec = self.asset_specs[prop["asset_type"]]
            target = self.market_prices[prop["price_key"]] * spec["price_scale"] * prop["quality"]
            prop["price"] = max(2500.0, prop["price"] * 0.84 + target * 0.16)
            kept.append(prop)
        self.properties = kept

    def update_highlight(self, player: Player) -> None:
        best_idx = -1
        best_dist = 56.0
        for index, prop in enumerate(self.properties):
            dist = math.hypot(player.x - float(prop["x"]), player.y - float(prop["y"]))
            if dist < best_dist:
                best_idx = index
                best_dist = dist
        self.highlighted_property = best_idx
        task_idx = -1
        task_dist = 58.0
        for index, task in enumerate(self.active_tasks):
            dist = math.hypot(player.x - float(task["x"]), player.y - float(task["y"]))
            if dist < task_dist:
                task_idx = index
                task_dist = dist
        self.highlighted_task = task_idx

    def update_tasks(self, dt: float) -> None:
        self.task_spawn_timer -= dt
        for holding in self.portfolio:
            holding["stress"] = min(1.6, float(holding.get("stress", 0.0)) + dt * 0.015)
        if self.task_spawn_timer <= 0.0 and self.portfolio:
            self.task_spawn_timer = random.uniform(8.0, 13.0)
            candidates = [holding for holding in self.portfolio if not any(task["holding_name"] == holding["name"] for task in self.active_tasks)]
            if candidates:
                holding = random.choice(candidates)
                task_type = random.choice(
                    [
                        ("Tenant complaint", 240.0),
                        ("Equipment tune-up", 320.0),
                        ("Compliance review", 280.0),
                    ]
                )
                self.active_tasks.append(
                    {
                        "holding_name": holding["name"],
                        "title": task_type[0],
                        "cost": task_type[1],
                        "x": clamp(float(holding["x"]) + random.uniform(-34.0, 34.0), self.BOARD_LEFT + 28.0, self.BOARD_RIGHT - 28.0),
                        "y": clamp(float(holding["y"]) + random.uniform(-34.0, 34.0), self.BOARD_TOP + 28.0, self.BOARD_BOTTOM - 28.0),
                    }
                )

    def update_portfolio_metrics(self, dt: float) -> None:
        year_fraction = dt / self.seconds_per_year
        total_value = 0.0
        cash_flow = 0.0
        for holding in self.portfolio:
            market_base = self.market_prices[holding["price_key"]]
            target_value = market_base * holding["quality"]
            blend = 0.30 if holding["sector"] in {"real_estate", "industrial"} else 0.52
            holding["market_value"] = holding["market_value"] * (1.0 - blend) + target_value * blend
            if holding["sector"] in {"real_estate", "industrial"} and random.random() < 0.18 * dt:
                holding["annual_expense"] *= random.uniform(1.01, 1.05)
            stress = float(holding.get("stress", 0.0))
            if stress > 0.75:
                holding["annual_expense"] *= 1.0 + dt * 0.01
                holding["annual_income"] *= max(0.998, 1.0 - dt * 0.003)
            annual_debt_service = float(holding.get("loan_principal", 0.0)) * self.loan_rate
            holding["annual_debt_service"] = annual_debt_service
            principal_payment = min(float(holding.get("loan_principal", 0.0)), float(holding.get("loan_principal", 0.0)) * year_fraction * 0.28)
            holding["loan_principal"] = max(0.0, float(holding.get("loan_principal", 0.0)) - principal_payment)
            self.loan_balance = max(0.0, self.loan_balance - principal_payment)
            period_cash = (holding["annual_income"] - holding["annual_expense"] - annual_debt_service) * year_fraction
            self.cash += period_cash
            cash_flow += holding["annual_income"] - holding["annual_expense"] - annual_debt_service
            holding["cash_flow"] = holding["annual_income"] - holding["annual_expense"] - annual_debt_service
            holding["profit"] = holding["market_value"] - holding["purchase_price"] + float(holding.get("down_payment", 0.0)) - float(holding.get("loan_principal", 0.0))
            total_value += holding["market_value"]
        self.net_worth = self.cash + total_value - self.loan_balance
        self.total_profit = self.net_worth - self.starting_cash
        self.monthly_cash_flow = cash_flow / 12.0
        self.peak_net_worth = max(self.peak_net_worth, self.net_worth)
        for threshold, badge in ((100000.0, "Six Figures"), (140000.0, "Operator"), (180000.0, "Empire Builder")):
            if self.peak_net_worth >= threshold and badge not in self.achievements:
                self.achievements.append(badge)

    def handle_ui(self, keys: set[str]) -> None:
        if self.ui_state == "game":
            if self.just_pressed(keys, "space"):
                self.open_detail_for_highlight()
            if self.just_pressed(keys, "r"):
                self.research_highlighted_property()
            if self.just_pressed(keys, "f"):
                self.negotiate_highlighted_property()
            if self.just_pressed(keys, "e"):
                self.resolve_highlighted_task()
            if self.just_pressed(keys, "l"):
                self.borrow_capital()
            if self.just_pressed(keys, "k"):
                self.repay_loan()
            if self.just_pressed(keys, "p"):
                self.ui_state = "portfolio"
            if self.just_pressed(keys, "m"):
                self.ui_state = "market"
        elif self.ui_state == "detail":
            if self.just_pressed(keys, "BackSpace"):
                self.ui_state = "game"
                self.selected_detail_idx = -1
            if self.just_pressed(keys, "Return"):
                self.buy_selected_property()
        elif self.ui_state == "portfolio":
            if self.just_pressed(keys, "BackSpace") or self.just_pressed(keys, "p"):
                self.ui_state = "game"
            if self.just_pressed(keys, "Up"):
                self.selected_portfolio_idx = max(0, self.selected_portfolio_idx - 1)
            if self.just_pressed(keys, "Down"):
                self.selected_portfolio_idx = min(max(0, len(self.portfolio) - 1), self.selected_portfolio_idx + 1)
            if self.just_pressed(keys, "Return"):
                self.sell_selected_holding()
        elif self.ui_state == "market":
            if self.just_pressed(keys, "BackSpace") or self.just_pressed(keys, "m"):
                self.ui_state = "game"

    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        self.keys = keys
        if self.finished:
            self.draw(canvas, player)
            return

        self.tick_timer(dt)
        if self.ui_state == "game":
            player.update(dt, keys, (self.BOARD_LEFT, self.BOARD_TOP, self.BOARD_RIGHT, self.BOARD_BOTTOM))
        self.update_market(dt)
        self.update_properties(dt)
        self.update_tasks(dt)
        self.update_highlight(player)
        self.handle_ui(keys)
        self.update_portfolio_metrics(dt)

        if self.cash < -15000.0:
            self.finished = True
            self.success = False
            self.grade = "F"
            self.message = f"Empire collapsed under negative liquidity. Net worth {self.money(self.net_worth)}."
        elif self.timer <= 0.0:
            self.finished = True
            self.success = self.net_worth >= self.target_net_worth and self.monthly_cash_flow >= 0.0
            if self.net_worth >= 225000.0 and self.monthly_cash_flow >= 1200.0:
                self.grade = "S"
            elif self.net_worth >= self.target_net_worth and self.monthly_cash_flow >= 800.0:
                self.grade = "A"
            elif self.net_worth >= 145000.0 and self.monthly_cash_flow >= 250.0:
                self.grade = "B"
            elif self.net_worth >= 115000.0:
                self.grade = "C"
            else:
                self.grade = "F"
            if self.success:
                self.message = f"Quarter closed strong: {self.money(self.net_worth)} net worth and {self.money(self.monthly_cash_flow)}/mo cash flow."
            else:
                self.message = f"Quarter ended at {self.money(self.net_worth)} with {self.money(self.monthly_cash_flow)}/mo cash flow."

        self.update_particles(dt)
        self.draw(canvas, player)

    def money(self, value: float) -> str:
        sign = "-" if value < 0 else ""
        return f"{sign}${abs(value):,.0f}"

    def draw_background(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#0a1623", outline="")
        canvas.create_rectangle(0, self.TOP_BAR_H, WIDTH, HEIGHT - self.FOOTER_H, fill="#0e1d2d", outline="")
        canvas.create_rectangle(self.BOARD_LEFT, self.BOARD_TOP, self.BOARD_RIGHT, self.BOARD_BOTTOM, fill="#102336", outline="#24435b")
        canvas.create_rectangle(self.BOARD_RIGHT + 10, self.BOARD_TOP, WIDTH - 18, self.BOARD_BOTTOM, fill="#0b1723", outline="#24435b")
        for zone in self.board_zones:
            canvas.create_oval(zone["x"] - zone["radius"], zone["y"] - zone["radius"], zone["x"] + zone["radius"], zone["y"] + zone["radius"], fill="", outline="#274861", width=2)
            canvas.create_text(zone["x"], zone["y"] - zone["radius"] - 12, text=zone["name"], fill="#7fb3d5", font=("Helvetica", 10, "bold"))

    def draw_top_bar(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, 0, WIDTH, self.TOP_BAR_H, fill="#08111b", outline="")
        canvas.create_text(14, 22, anchor="w", text="Tycoon Empire", fill="#e8f4ff", font=("Helvetica", 14, "bold"))
        canvas.create_text(WIDTH / 2, 22, text=f"Target {self.money(self.target_net_worth)}", fill="#82cfff", font=("Helvetica", 11, "bold"))
        canvas.create_text(WIDTH - 16, 22, anchor="e", text=f"Time {self.timer:05.1f}s", fill="#e8f4ff", font=("Helvetica", 12, "bold"))

    def draw_footer(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(0, HEIGHT - self.FOOTER_H, WIDTH, HEIGHT, fill="#08111b", outline="")
        canvas.create_text(WIDTH / 2, HEIGHT - self.FOOTER_H / 2, text=self.hints[self.current_hint_index], fill="#8fc3eb", font=("Helvetica", 10, "italic"), width=WIDTH - 80)

    def draw_game_hud(self, canvas: tk.Canvas) -> None:
        y1 = HEIGHT - self.INFO_PANEL_H - self.FOOTER_H
        y2 = HEIGHT - self.FOOTER_H
        canvas.create_rectangle(0, y1, WIDTH, y2, fill="#0a131d", outline="#28445d")
        labels = [
            ("Cash", self.money(self.cash), "#7ee787"),
            ("Net Worth", self.money(self.net_worth), "#7cc8ff"),
            ("Cash Flow", f"{self.money(self.monthly_cash_flow)}/mo", "#ffd166"),
            ("Debt", self.money(self.loan_balance), "#ffb4a2"),
        ]
        for index, (label, value, color) in enumerate(labels):
            x1 = 18 + index * 183
            x2 = x1 + 172
            canvas.create_rectangle(x1, y1 + 14, x2, y1 + 62, fill="#122131", outline="#33526a")
            canvas.create_text(x1 + 14, y1 + 28, anchor="w", text=label, fill="#9bc0da", font=("Helvetica", 9, "bold"))
            canvas.create_text(x1 + 14, y1 + 48, anchor="w", text=value, fill=color, font=("Helvetica", 11, "bold"))
        status = self.message if self.message else "Scout opportunities, then buy only when the yield justifies the price."
        canvas.create_rectangle(18, y1 + 72, WIDTH - 18, y2 - 10, fill="#101a27", outline="#2c495e")
        canvas.create_text(32, y1 + 88, anchor="w", text=status, fill="#d7ebfb", font=("Helvetica", 10, "bold"), width=WIDTH - 120)
        if self.event_timer > 0.0:
            canvas.create_text(WIDTH - 24, y1 + 88, anchor="e", text=self.event_message, fill="#ffca7a", font=("Helvetica", 9, "bold"), width=220)

    def draw_properties(self, canvas: tk.Canvas) -> None:
        for index, prop in enumerate(self.properties):
            x = float(prop["x"])
            y = float(prop["y"])
            selected = index == self.highlighted_property
            radius = 19 if selected else 16
            outline = "#ffffff" if selected else "#24435b"
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=prop["color"], outline=outline, width=3 if selected else 2)
            canvas.create_text(x, y, text=prop["icon"], fill="#08111b", font=("Helvetica", 8, "bold"))
            canvas.create_text(x, y + 28, text=self.money(float(prop["price"])), fill="#e4f0fa", font=("Helvetica", 8, "bold"))
            if selected:
                label_y = y - 30 if y > self.BOARD_TOP + 42 else y + 42
                canvas.create_text(x, label_y, text=prop["name"], fill="#ffffff", font=("Helvetica", 9, "bold"))

    def draw_tasks(self, canvas: tk.Canvas) -> None:
        for index, task in enumerate(self.active_tasks):
            selected = index == self.highlighted_task
            radius = 13 if selected else 11
            canvas.create_oval(task["x"] - radius, task["y"] - radius, task["x"] + radius, task["y"] + radius, fill="#ff922b", outline="#fff3bf" if selected else "#5c3d19", width=3 if selected else 2)
            canvas.create_text(task["x"], task["y"], text="!", fill="#2b1400", font=("Helvetica", 10, "bold"))

    def draw_market_strip(self, canvas: tk.Canvas) -> None:
        x1 = self.BOARD_RIGHT + 10
        y1 = self.BOARD_TOP
        x2 = WIDTH - 18
        y2 = self.BOARD_BOTTOM
        canvas.create_text(x1 + 14, y1 + 14, anchor="nw", text="Market Snapshot", fill="#d8f0ff", font=("Helvetica", 11, "bold"))
        row_y = y1 + 38
        for key in ("real_estate", "industrial", "tech_fund", "dividend_fund", "bond_ladder", "crypto_miner"):
            history = self.price_history[key]
            lookback = min(120, len(history) - 1) if len(history) > 1 else 1
            drift = history[-1] - history[max(0, len(history) - 1 - lookback)] if len(history) > 1 else 0.0
            color = "#69db7c" if drift >= 0 else "#ff8787"
            label = key.replace("_", " ").title()
            canvas.create_text(x1 + 14, row_y, anchor="w", text=label, fill="#93b9d6", font=("Helvetica", 9))
            canvas.create_text(x2 - 14, row_y, anchor="e", text=self.money(self.market_prices[key]), fill=color, font=("Helvetica", 9, "bold"))
            row_y += 18
        row_y += 10
        canvas.create_text(x1 + 14, row_y, anchor="w", text="Active Play", fill="#ffd166", font=("Helvetica", 11, "bold"))
        row_y += 22
        sidebar_lines = [
            "R Research deal",
            "F Negotiate price",
            "E Resolve service call",
            "L Borrow / K repay",
            "SPACE Inspect",
            f"Open tasks: {len(self.active_tasks)}",
        ]
        for line in sidebar_lines:
            canvas.create_text(x1 + 14, row_y, anchor="w", text=line, fill="#d6e9f8", font=("Helvetica", 9), width=self.SIDE_PANEL_W - 36)
            row_y += 18
        row_y += 8
        canvas.create_text(x1 + 14, row_y, anchor="w", text="Recent Activity", fill="#ffd166", font=("Helvetica", 11, "bold"))
        row_y += 20
        history_lines = self.transaction_history[-6:] if self.transaction_history else ["No trades yet."]
        for line in history_lines:
            canvas.create_text(x1 + 14, row_y, anchor="w", text=line, fill="#d6e9f8", font=("Helvetica", 9), width=self.SIDE_PANEL_W - 36)
            row_y += 18

    def draw_detail_modal(self, canvas: tk.Canvas) -> None:
        if self.selected_detail_idx < 0 or self.selected_detail_idx >= len(self.properties):
            return
        prop = self.properties[self.selected_detail_idx]
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="")
        x1 = 215
        y1 = 96
        x2 = WIDTH - 215
        y2 = HEIGHT - 116
        canvas.create_rectangle(x1, y1, x2, y2, fill="#102033", outline="#4f88b6", width=3)
        canvas.create_text((x1 + x2) / 2, y1 + 26, text=prop["name"], fill="#eef7ff", font=("Helvetica", 16, "bold"))
        lines = [
            f"Sector: {str(prop['sector']).replace('_', ' ').title()}",
            f"Zone: {prop['zone']}",
            f"Asking Price: {self.money(float(prop['price']))}",
            f"Negotiated Price: {self.money(float(prop['price']) * (1.0 - float(prop.get('negotiated_discount', 0.0)) ))}",
            f"Down Payment: {self.money(float(prop['price']) * (1.0 - float(prop.get('negotiated_discount', 0.0))) * self.down_payment_ratio(float(prop['risk'])))}",
            f"Projected Annual Yield: {float(prop['annual_yield']) * 100:.1f}%",
            f"Projected Annual Expense: {float(prop['annual_expense']) * 100:.1f}%",
            f"Occupancy / Utilization: {float(prop['occupancy']) * 100:.0f}%",
            f"Research Level: {int(prop.get('research', 0))}/2",
            f"Risk Score: {int(float(prop['risk']) * 100)} / 100",
            f"Estimated Monthly Cash Flow: {self.money((float(prop['price']) * (1.0 - float(prop.get('negotiated_discount', 0.0))) * (float(prop['annual_yield']) * float(prop['occupancy']) - float(prop['annual_expense'])) - (float(prop['price']) * (1.0 - float(prop.get('negotiated_discount', 0.0))) * (1.0 - self.down_payment_ratio(float(prop['risk']))) * self.loan_rate)) / 12.0)}",
            f"Cash Available: {self.money(self.cash)}",
        ]
        y = y1 + 68
        for line in lines:
            canvas.create_text(x1 + 26, y, anchor="w", text=line, fill="#d6e9f8", font=("Helvetica", 11))
            y += 28
        down_payment_needed = float(prop["price"]) * (1.0 - float(prop.get("negotiated_discount", 0.0))) * self.down_payment_ratio(float(prop["risk"]))
        can_afford = self.cash >= down_payment_needed
        button_fill = "#2f9e44" if can_afford else "#7f8c8d"
        canvas.create_rectangle(x1 + 42, y2 - 76, x2 - 42, y2 - 34, fill=button_fill, outline="")
        canvas.create_text((x1 + x2) / 2, y2 - 55, text="Press ENTER to acquire with financing" if can_afford else "Insufficient down payment", fill="#ffffff", font=("Helvetica", 12, "bold"))
        canvas.create_text((x1 + x2) / 2, y2 - 14, text="BACKSPACE closes the card", fill="#9bc0da", font=("Helvetica", 10))

    def draw_portfolio(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(22, 62, WIDTH - 22, HEIGHT - 40, fill="#0b1520", outline="#355670", width=2)
        canvas.create_text(38, 82, anchor="w", text="Portfolio", fill="#eef7ff", font=("Helvetica", 16, "bold"))
        canvas.create_text(WIDTH - 38, 82, anchor="e", text="ENTER sells selected holding", fill="#8fb9d8", font=("Helvetica", 10))
        summary = [("Cash", self.money(self.cash)), ("Net Worth", self.money(self.net_worth)), ("Cash Flow", f"{self.money(self.monthly_cash_flow)}/mo"), ("Debt", self.money(self.loan_balance))]
        for index, (label, value) in enumerate(summary):
            x1 = 36 + index * 220
            canvas.create_rectangle(x1, 100, x1 + 200, 148, fill="#132435", outline="#31506a")
            canvas.create_text(x1 + 12, 115, anchor="w", text=label, fill="#89b5d8", font=("Helvetica", 9, "bold"))
            canvas.create_text(x1 + 12, 135, anchor="w", text=value, fill="#eef7ff", font=("Helvetica", 13, "bold"))
        list_top = 166
        list_bottom = HEIGHT - 118
        canvas.create_rectangle(36, list_top, WIDTH - 36, list_bottom, fill="#101b28", outline="#2c495e")
        if not self.portfolio:
            canvas.create_text(WIDTH / 2, (list_top + list_bottom) / 2, text="No holdings yet. Buy from the board first.", fill="#8fb9d8", font=("Helvetica", 12, "bold"))
        else:
            max_rows = 9
            start = 0
            if self.selected_portfolio_idx >= max_rows:
                start = self.selected_portfolio_idx - max_rows + 1
            visible = self.portfolio[start:start + max_rows]
            row_y = list_top + 18
            for offset, holding in enumerate(visible):
                actual_index = start + offset
                selected = actual_index == self.selected_portfolio_idx
                fill = "#17314b" if selected else "#0f1a27"
                outline = "#67b7ff" if selected else "#1f3346"
                canvas.create_rectangle(48, row_y, WIDTH - 48, row_y + 38, fill=fill, outline=outline)
                text = f"{holding['name']}  |  Value {self.money(float(holding['market_value']))}  |  Debt {self.money(float(holding.get('loan_principal', 0.0)))}  |  Cash Flow {self.money(float(holding['cash_flow']) / 12.0)}/mo"
                canvas.create_text(62, row_y + 20, anchor="w", text=text, fill="#edf6ff", font=("Helvetica", 10), width=WIDTH - 160)
                row_y += 46
        ach_text = ", ".join(self.achievements[-4:]) if self.achievements else "No milestones yet."
        canvas.create_text(40, HEIGHT - 86, anchor="w", text=f"Milestones: {ach_text}", fill="#ffd166", font=("Helvetica", 10, "bold"), width=WIDTH - 80)
        canvas.create_text(WIDTH / 2, HEIGHT - 58, text="UP/DOWN select  |  ENTER sell  |  P or BACKSPACE return", fill="#9bc0da", font=("Helvetica", 10))

    def draw_market_screen(self, canvas: tk.Canvas) -> None:
        canvas.create_rectangle(22, 62, WIDTH - 22, HEIGHT - 40, fill="#0b1520", outline="#355670", width=2)
        canvas.create_text(38, 82, anchor="w", text="Market Board", fill="#eef7ff", font=("Helvetica", 16, "bold"))
        canvas.create_text(WIDTH - 38, 82, anchor="e", text="M or BACKSPACE returns to the floor", fill="#8fb9d8", font=("Helvetica", 10))
        left_x = 42
        right_x = WIDTH / 2 + 12
        row_y = 122
        for key in ("real_estate", "industrial", "tech_fund", "dividend_fund", "bond_ladder", "crypto_miner"):
            history = self.price_history[key]
            trend = history[-1] - history[0]
            fill = "#69db7c" if trend >= 0 else "#ff8787"
            label = key.replace("_", " ").title()
            x1 = left_x if row_y < 310 else right_x
            local_y = row_y if row_y < 310 else row_y - 188
            canvas.create_rectangle(x1, local_y, x1 + 400, local_y + 72, fill="#112132", outline="#31506a")
            canvas.create_text(x1 + 16, local_y + 18, anchor="w", text=label, fill="#eef7ff", font=("Helvetica", 12, "bold"))
            canvas.create_text(x1 + 16, local_y + 42, anchor="w", text=f"Price {self.money(self.market_prices[key])}", fill=fill, font=("Helvetica", 11, "bold"))
            canvas.create_text(x1 + 220, local_y + 42, anchor="w", text=f"Quarter trend {self.money(trend)}", fill="#b6d7ee", font=("Helvetica", 10))
            row_y += 94
        canvas.create_rectangle(42, HEIGHT - 156, WIDTH - 42, HEIGHT - 70, fill="#101b28", outline="#2c495e")
        canvas.create_text(58, HEIGHT - 142, anchor="nw", text="Recent activity", fill="#ffd166", font=("Helvetica", 11, "bold"))
        history_text = self.transaction_history[-5:] if self.transaction_history else ["No trades yet."]
        y = HEIGHT - 120
        for line in history_text:
            canvas.create_text(58, y, anchor="nw", text=line, fill="#d6e9f8", font=("Helvetica", 10), width=WIDTH - 120)
            y += 18

    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        self.draw_background(canvas)
        self.draw_top_bar(canvas)
        self.draw_footer(canvas)
        if self.ui_state == "game":
            self.draw_properties(canvas)
            self.draw_tasks(canvas)
            player.draw(canvas)
            self.draw_market_strip(canvas)
            self.draw_game_hud(canvas)
        elif self.ui_state == "detail":
            self.draw_properties(canvas)
            self.draw_tasks(canvas)
            player.draw(canvas)
            self.draw_game_hud(canvas)
            self.draw_detail_modal(canvas)
        elif self.ui_state == "portfolio":
            self.draw_portfolio(canvas)
        elif self.ui_state == "market":
            self.draw_market_screen(canvas)
        if self.finished:
            self.draw_result(canvas)
