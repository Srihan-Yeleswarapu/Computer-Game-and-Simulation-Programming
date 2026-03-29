import random
import math
import tkinter as tk
from src.utils import WIDTH, HEIGHT, TEXT, clamp, Particle
from src.player import Player
from src.worlds.base import BaseWorld
from typing import Any

class TycoonWorld(BaseWorld):
    def __init__(self) -> None:
        super().__init__(
            name="Tycoon Empire",
            summary="Build a diverse investment portfolio and dominate the market",
            duration=180.0,
        )
        self.briefing = [
            "WELCOME TO TYCOON EMPIRE - Your $50,000 Challenge!",
            "Strategically invest in real estate, stocks, and businesses across the board.",
            "Market prices FLUCTUATE - watch for crashes and rallies to maximize profit.",
            "Build a diversified portfolio and reach $500,000 net worth to become a legend.",
            "Advanced Features: Short selling, dividend tracking, hostile takeovers, and more!"
        ]
        self.hints = [
            "Tip: SPACE near assets opens details. ENTER to buy/sell. BACKSPACE to cancel.",
            "Tip: Press P to open Portfolio - manage all your holdings and view profits!",
            "Tip: Press M for Market Analysis - track price trends and make smart trades.",
            "Tip: Diversify! Stocks are risky but high-reward. Real estate is steady income.",
            "Tip: Watch for Market Events! Crashes can bankrupt you or create opportunities.",
            "Tip: Use the board edges wisely - there are hidden zones with rare investments!"
        ]
        
        # Financial state
        self.cash = 50000.0
        self.net_worth = 50000.0
        self.total_invested = 0.0
        self.portfolio: list[dict[str, Any]] = []
        self.transaction_history: list[dict[str, Any]] = []
        self.ui_state = "game"  # "game", "portfolio", "market_analysis", "property_detail", "confirm_buy"
        self.selected_detail_idx = -1
        self.space_pressed_last_frame = False
        self.enter_pressed_last_frame = False
        self.backspace_pressed_last_frame = False
        
        # Advanced market mechanics
        self.market_prices: dict[str, float] = {
            "residential": 15000.0,
            "commercial": 25000.0,
            "luxury": 50000.0,
            "stocks_tech": 100.0,
            "stocks_finance": 85.0,
            "stocks_real_estate": 120.0,
            "stocks_energy": 65.0,
            "crypto": 10000.0,
            "bonds": 1000.0,
        }
        self.price_trends: dict[str, float] = {key: random.uniform(-0.01, 0.01) for key in self.market_prices}
        self.price_history: dict[str, list[float]] = {key: [v] for key, v in self.market_prices.items()}
        self.market_timer = 0.0
        self.market_event_timer = 0.0
        self.current_market_event = None
        self.market_event_message = ""
        self.event_message_timer = 0.0
        self.market_volatility = 1.0
        
        # Properties on the board
        self.properties: list[dict[str, Any]] = []
        self.spawn_timer = 0.0
        self.board_zones = self._generate_board_zones()
        
        # UI state
        self.confirm_dialog_action = None
        self.confirm_dialog_data = None
        self.selected_detail_idx = -1
        self.highlighted_property = -1
        self.scroll_offset = 0
        
        # Tutorial and progression
        self.tutorial_timer = 5.0
        self.first_purchase_made = False
        self.achievements: list[str] = []
        
        # Statistics
        self.total_profit = 0.0
        self.buy_count = 0
        self.sell_count = 0
        self.peak_net_worth = 50000.0
        
    def _generate_board_zones(self) -> list[dict[str, Any]]:
        """Generate special zones on the board with unique properties"""
        return [
            {
                "name": "Tech Valley",
                "x": 150,
                "y": 150,
                "radius": 80,
                "asset_type": "tech",
                "color": "#9b59b6"
            },
            {
                "name": "Financial District",
                "x": WIDTH - 150,
                "y": 150,
                "radius": 80,
                "asset_type": "finance",
                "color": "#e74c3c"
            },
            {
                "name": "Real Estate Hub",
                "x": 150,
                "y": HEIGHT - 150,
                "radius": 80,
                "asset_type": "real_estate",
                "color": "#3498db"
            },
            {
                "name": "Luxury District",
                "x": WIDTH - 150,
                "y": HEIGHT - 150,
                "radius": 80,
                "asset_type": "luxury",
                "color": "#f39c12"
            }
        ]
    
    def reset(self, player: Player) -> None:
        player.reset(WIDTH / 2, HEIGHT / 2)
        self.timer = self.duration
        self.finished = False
        self.success = False
        self.message = ""
        self.cash = 50000.0
        self.net_worth = 50000.0
        self.total_invested = 0.0
        self.portfolio = []
        self.transaction_history = []
        self.ui_state = "game"
        self.selected_detail_idx = -1
        self.space_pressed_last_frame = False
        self.enter_pressed_last_frame = False
        self.backspace_pressed_last_frame = False
        
        self.market_prices = {
            "residential": 15000.0,
            "commercial": 25000.0,
            "luxury": 50000.0,
            "stocks_tech": 100.0,
            "stocks_finance": 85.0,
            "stocks_real_estate": 120.0,
            "stocks_energy": 65.0,
            "crypto": 10000.0,
            "bonds": 1000.0,
        }
        self.price_trends = {key: random.uniform(-0.01, 0.01) for key in self.market_prices}
        self.price_history = {key: [v] for key, v in self.market_prices.items()}
        self.market_timer = 0.0
        self.market_event_timer = 0.0
        self.current_market_event = None
        self.market_event_message = ""
        self.event_message_timer = 0.0
        self.market_volatility = 1.0
        
        self.properties = []
        self.spawn_timer = 0.0
        self.confirm_dialog_action = None
        self.confirm_dialog_data = None
        self.scroll_offset = 0
        self.shake = 0.0
        self.particles = []
        self.tutorial_timer = 5.0
        self.first_purchase_made = False
        self.achievements = []
        self.total_profit = 0.0
        self.buy_count = 0
        self.sell_count = 0
        self.peak_net_worth = 50000.0
        
    def spawn_property(self) -> dict[str, Any]:
        """Spawn a property with zone awareness"""
        # Determine zone
        zone = random.choice(self.board_zones)
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, zone["radius"])
        x = zone["x"] + math.cos(angle) * dist
        y = zone["y"] + math.sin(angle) * dist
        x = clamp(x, 60, WIDTH - 60)
        y = clamp(y, 100, HEIGHT - 150)
        
        prop_type = random.choices(
            ["residential", "commercial", "luxury", "stocks_tech", "stocks_finance", "stocks_real_estate", 
             "stocks_energy", "crypto", "bonds", "liability", "dividend_stock"],
            weights=[0.15, 0.12, 0.08, 0.12, 0.12, 0.1, 0.1, 0.08, 0.07, 0.05, 0.01]
        )[0]
        
        if prop_type == "residential":
            price = self.market_prices["residential"] + random.uniform(-3000, 3000)
            return {
                "id": len(self.properties),
                "type": "residential",
                "name": f"House #{random.randint(100, 999)}",
                "price": price,
                "monthly_income": price * 0.008,
                "color": "#3498db",
                "icon": "🏠",
                "x": x,
                "y": y,
                "owned": False,
                "purchase_price": price,
                "months_owned": 0,
                "quality": random.choice(["Good", "Excellent", "Fair"]),
                "zone": zone["name"],
                "condition": random.uniform(0.7, 1.0)
            }
        elif prop_type == "commercial":
            price = self.market_prices["commercial"] + random.uniform(-4000, 4000)
            return {
                "id": len(self.properties),
                "type": "commercial",
                "name": f"Office #{random.randint(100, 999)}",
                "price": price,
                "monthly_income": price * 0.012,
                "color": "#2ecc71",
                "icon": "🏢",
                "x": x,
                "y": y,
                "owned": False,
                "purchase_price": price,
                "quality": random.choice(["Good", "Excellent", "Fair"]),
                "zone": zone["name"],
                "tenants": random.randint(1, 5)
            }
        elif prop_type == "luxury":
            price = self.market_prices["luxury"] + random.uniform(-8000, 8000)
            return {
                "id": len(self.properties),
                "type": "luxury",
                "name": f"Penthouse #{random.randint(1000, 9999)}",
                "price": price,
                "monthly_income": price * 0.015,
                "color": "#f39c12",
                "icon": "👑",
                "x": x,
                "y": y,
                "owned": False,
                "purchase_price": price,
                "prestige": random.randint(80, 100),
                "zone": zone["name"],
                "amenities": random.randint(5, 15)
            }
        elif prop_type.startswith("stocks"):
            stock_key = prop_type
            base_price = self.market_prices[stock_key]
            return {
                "id": len(self.properties),
                "type": "stock",
                "stock_type": stock_key,
                "name": f"{stock_key.replace('stocks_', '').upper()} Stock",
                "price": base_price,
                "shares_available": random.randint(20, 150),
                "color": "#e67e22",
                "icon": "📈",
                "x": x,
                "y": y,
                "owned": False,
                "shares_owned": 0,
                "purchase_price": base_price,
                "volatility": random.uniform(0.3, 3.0),
                "pe_ratio": random.uniform(5, 25),
                "sector": stock_key.replace("stocks_", "")
            }
        elif prop_type == "crypto":
            price = self.market_prices["crypto"]
            return {
                "id": len(self.properties),
                "type": "crypto",
                "name": f"Coin #{random.choice(['Bitcoin', 'Ethereum', 'Dogecoin'])}",
                "price": price,
                "color": "#f1c40f",
                "icon": "💰",
                "x": x,
                "y": y,
                "owned": False,
                "coins_available": random.randint(1, 10),
                "purchase_price": price,
                "volatility": 5.0,
                "risk": "EXTREME"
            }
        elif prop_type == "bonds":
            price = self.market_prices["bonds"]
            return {
                "id": len(self.properties),
                "type": "bond",
                "name": f"Bond #{random.randint(100, 999)}",
                "price": price,
                "monthly_income": price * 0.004,
                "color": "#16a085",
                "icon": "📜",
                "x": x,
                "y": y,
                "owned": False,
                "purchase_price": price,
                "maturity": random.randint(5, 30),
                "interest_rate": random.uniform(0.02, 0.08)
            }
        elif prop_type == "dividend_stock":
            price = self.market_prices["stocks_finance"]
            return {
                "id": len(self.properties),
                "type": "dividend_stock",
                "name": f"Dividend Stock #{random.randint(100, 999)}",
                "price": price,
                "monthly_income": price * 0.02,  # High dividend
                "color": "#27ae60",
                "icon": "💵",
                "x": x,
                "y": y,
                "owned": False,
                "shares_available": random.randint(10, 50),
                "dividend_yield": 0.04,
                "stability": "HIGH"
            }
        else:  # liability
            return {
                "id": len(self.properties),
                "type": "liability",
                "name": f"Debt #{random.randint(1000, 9999)}",
                "price": random.uniform(5000, 15000),
                "monthly_drain": random.uniform(200, 800),
                "color": "#e74c3c",
                "icon": "💸",
                "x": x,
                "y": y,
                "owned": False,
                "interest_rate": random.uniform(0.05, 0.25),
                "deadline": random.randint(30, 180)
            }
    
    def trigger_market_event(self):
        """Generate random market events"""
        events = [
            {
                "name": "Tech Boom!",
                "description": "Tech stocks surge 15%",
                "effect": {"stocks_tech": 1.15},
                "severity": "positive"
            },
            {
                "name": "Market Crash!",
                "description": "All stocks plummet 20%",
                "effect": {"stocks_tech": 0.80, "stocks_finance": 0.80, "stocks_real_estate": 0.85},
                "severity": "negative"
            },
            {
                "name": "Real Estate Rally",
                "description": "Property prices surge 12%",
                "effect": {"residential": 1.12, "commercial": 1.12, "luxury": 1.12},
                "severity": "positive"
            },
            {
                "name": "Interest Rate Hike",
                "description": "Bonds become attractive (+8%)",
                "effect": {"bonds": 1.08},
                "severity": "mixed"
            },
            {
                "name": "Crypto Volatility",
                "description": "Crypto doubles then halves!",
                "effect": {"crypto": random.choice([2.0, 0.5])},
                "severity": "extreme"
            },
            {
                "name": "Inflation Surge",
                "description": "All asset prices inflate",
                "effect": {k: 1.08 for k in self.market_prices.keys()},
                "severity": "negative"
            }
        ]
        
        event = random.choice(events)
        self.current_market_event = event
        self.market_event_message = f"{event['name']}: {event['description']}"
        self.event_message_timer = 3.0
        
        # Apply effects
        for asset, multiplier in event["effect"].items():
            if asset in self.market_prices:
                self.market_prices[asset] *= multiplier
        
        self.market_volatility = 1.5 if event["severity"] == "extreme" else 1.2
    
    def update(self, dt: float, canvas: tk.Canvas, player: Player, keys: set[str], mouse_pos: tuple[int, int]) -> None:
        if self.finished:
            self.draw(canvas, player)
            return
        
        if self.tutorial_timer > 0:
            self.tutorial_timer -= dt
            self.draw(canvas, player)
            return
        
        self.tick_timer(dt)
        
        # Event message timer
        if self.event_message_timer > 0:
            self.event_message_timer -= dt
        
        # Update market (every 2-3 seconds)
        self.market_timer += dt
        if self.market_timer >= 2.5:
            self.market_timer = 0.0
            
            for key in self.market_prices:
                trend = self.price_trends[key]
                # Random walk with volatility
                volatility_multiplier = self.market_volatility
                trend += random.uniform(-0.015, 0.015) * volatility_multiplier
                trend = clamp(trend, -0.08, 0.08)
                self.price_trends[key] = trend
                
                # Update price
                old_price = self.market_prices[key]
                self.market_prices[key] *= (1.0 + trend)
                self.market_prices[key] = max(1.0, self.market_prices[key])
                
                # Track history
                if len(self.price_history[key]) < 50:
                    self.price_history[key].append(self.market_prices[key])
            
            # Volatility decays
            self.market_volatility = max(1.0, self.market_volatility - 0.1)
            
            # Random market events
            if random.random() < 0.15:
                self.trigger_market_event()
        
        # Handle key presses (with debouncing)
        space_pressed = "space" in keys and not self.space_pressed_last_frame
        enter_pressed = "return" in keys and not self.enter_pressed_last_frame
        backspace_pressed = "backspace" in keys and not self.backspace_pressed_last_frame
        
        self.space_pressed_last_frame = "space" in keys
        self.enter_pressed_last_frame = "return" in keys
        self.backspace_pressed_last_frame = "backspace" in keys
        
        if self.ui_state == "game":
            player.update(dt, keys, (70, 100, WIDTH - 70, HEIGHT - 150))
            
            # Spawn properties
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = random.uniform(3.0, 6.0)
                if len(self.properties) < 30:
                    self.properties.append(self.spawn_property())
            
            # Clean up old properties
            self.properties = [p for p in self.properties if p.get("owned") or random.random() > 0.0005 * dt]
            
            # Check collisions
            closest_idx = -1
            closest_dist = 50
            for i, prop in enumerate(self.properties):
                dist = math.hypot(player.x - prop["x"], player.y - prop["y"])
                if dist < closest_dist:
                    closest_dist = dist
                    closest_idx = i
            
            self.highlighted_property = closest_idx
            
            if space_pressed and closest_idx >= 0:
                self.selected_detail_idx = closest_idx
                self.ui_state = "property_detail"
            
            if "p" in keys:
                self.ui_state = "portfolio"
            
            if "m" in keys:
                self.ui_state = "market_analysis"
        
        elif self.ui_state == "property_detail":
            if backspace_pressed:
                self.ui_state = "game"
            elif enter_pressed and self.selected_detail_idx >= 0:
                prop = self.properties[self.selected_detail_idx]
                if prop["type"] == "stock":
                    cost = prop["price"]
                    if self.cash >= cost and prop.get("shares_available", 0) > 0:
                        self.cash -= cost
                        self.total_invested += cost
                        prop["owned"] = True
                        prop["shares_owned"] = prop.get("shares_owned", 0) + 1
                        self.portfolio.append({
                            "type": "stock",
                            "stock_type": prop["stock_type"],
                            "shares": 1,
                            "purchase_price": prop["price"],
                            "current_price": prop["price"],
                            "profit": 0.0
                        })
                        self.transaction_history.append({"action": "BUY", "asset": prop["name"], "price": cost, "time": self.timer})
                        self.buy_count += 1
                        self.shake = 3.0
                        if not self.first_purchase_made:
                            self.first_purchase_made = True
                            self.achievements.append("First Investment")
                elif prop["type"] == "crypto":
                    cost = prop["price"]
                    if self.cash >= cost:
                        self.cash -= cost
                        self.total_invested += cost
                        prop["owned"] = True
                        self.portfolio.append({
                            "type": "crypto",
                            "name": prop["name"],
                            "coins": 1,
                            "purchase_price": prop["price"],
                            "current_price": prop["price"],
                            "profit": 0.0
                        })
                        self.transaction_history.append({"action": "BUY CRYPTO", "asset": prop["name"], "price": cost, "time": self.timer})
                        self.buy_count += 1
                        self.shake = 3.0
                else:
                    cost = prop["price"]
                    if self.cash >= cost:
                        self.cash -= cost
                        self.total_invested += cost
                        prop["owned"] = True
                        self.portfolio.append({
                            "type": prop["type"],
                            "property_id": prop["id"],
                            "name": prop["name"],
                            "purchase_price": cost,
                            "current_value": cost,
                            "monthly_income": prop.get("monthly_income", 0),
                            "monthly_drain": prop.get("monthly_drain", 0),
                            "profit": 0.0
                        })
                        self.transaction_history.append({"action": "BUY", "asset": prop["name"], "price": cost, "time": self.timer})
                        self.buy_count += 1
                        self.shake = 3.0
                        if not self.first_purchase_made:
                            self.first_purchase_made = True
                            self.achievements.append("First Investment")
                self.ui_state = "game"
        
        elif self.ui_state == "portfolio":
            if "p" in keys or backspace_pressed:
                self.ui_state = "game"
        
        elif self.ui_state == "market_analysis":
            if "m" in keys or backspace_pressed:
                self.ui_state = "game"
        
        # Update portfolio values and income
        monthly_income = 0.0
        monthly_drain = 0.0
        total_property_value = 0.0
        
        for item in self.portfolio:
            if item["type"] == "stock":
                stock_key = item["stock_type"]
                if stock_key in self.market_prices:
                    item["current_price"] = self.market_prices[stock_key]
                    value = item["current_price"] * item["shares"]
                    item["profit"] = value - (item["purchase_price"] * item["shares"])
                    total_property_value += value
            elif item["type"] == "crypto":
                item["current_price"] = self.market_prices["crypto"]
                value = item["current_price"] * item.get("coins", 1)
                item["profit"] = value - item["purchase_price"]
                total_property_value += value
            elif item["type"] == "dividend_stock":
                stock_key = "stocks_finance"
                if stock_key in self.market_prices:
                    item["current_price"] = self.market_prices[stock_key]
                    value = item["current_price"] * item.get("shares", 1)
                    income = item.get("monthly_income", 0) * item.get("shares", 1)
                    item["profit"] = value - item["purchase_price"] + income * dt * 10
                    monthly_income += income
                    total_property_value += value
            elif item["type"] == "bond":
                item["current_value"] = item["purchase_price"]
                item["profit"] = item.get("monthly_income", 0) * dt * 10
                monthly_income += item.get("monthly_income", 0)
                total_property_value += item["purchase_price"]
            else:
                # Real estate
                income = item.get("monthly_income", 0)
                drain = item.get("monthly_drain", 0)
                monthly_income += income * dt * 0.15
                monthly_drain += drain * dt * 0.15
                
                # Appreciation
                item["current_value"] = item.get("current_value", item["purchase_price"])
                item["current_value"] *= (1.0 + income * 0.00008 * dt)
                item["profit"] = item["current_value"] - item["purchase_price"]
                total_property_value += item["current_value"]
        
        self.cash += monthly_income - monthly_drain
        self.net_worth = self.cash + total_property_value
        self.total_profit = self.net_worth - 50000.0
        
        if self.net_worth > self.peak_net_worth:
            self.peak_net_worth = self.net_worth
            if self.peak_net_worth >= 100000:
                self.achievements.append("$100K Club")
            if self.peak_net_worth >= 250000:
                self.achievements.append("Quarter Millionaire")
            if self.peak_net_worth >= 500000:
                self.achievements.append("LEGEND")
        
        # Win/lose conditions
        if self.cash < -50000:
            self.finished = True
            self.success = False
            self.message = f"Bankrupt! Final Net Worth: ${int(self.net_worth):,}"
            self.grade = "F"
        
        if self.timer <= 0:
            self.finished = True
            if self.net_worth >= 500000:
                self.success = True
                self.message = f"🏆 TYCOON LEGEND! Net Worth: ${int(self.net_worth):,}"
                self.grade = "S"
            elif self.net_worth >= 300000:
                self.success = True
                self.message = f"🥇 Elite Investor! Net Worth: ${int(self.net_worth):,}"
                self.grade = "A"
            elif self.net_worth >= 150000:
                self.success = True
                self.message = f"🥈 Successful Trader! Net Worth: ${int(self.net_worth):,}"
                self.grade = "B"
            elif self.net_worth >= 75000:
                self.success = True
                self.message = f"Investor. Net Worth: ${int(self.net_worth):,}"
                self.grade = "C"
            else:
                self.success = False
                self.message = f"Try Again. Net Worth: ${int(self.net_worth):,}"
                self.grade = "F"
        
        self.update_particles(dt)
        self.draw(canvas, player)
    
    def draw_property_detail(self, canvas: tk.Canvas) -> None:
        """Draw property detail modal"""
        if self.selected_detail_idx < 0 or self.selected_detail_idx >= len(self.properties):
            return
        
        prop = self.properties[self.selected_detail_idx]
        
        # Modal background
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50")
        
        # Panel
        panel_w, panel_h = 450, 420
        x0 = WIDTH / 2 - panel_w / 2
        y0 = HEIGHT / 2 - panel_h / 2
        canvas.create_rectangle(x0, y0, x0 + panel_w, y0 + panel_h, fill="#2c3e50", outline="#ecf0f1", width=3)
        
        y = y0 + 20
        
        # Title with icon
        canvas.create_text(x0 + panel_w / 2, y, text=f"{prop['icon']} {prop['name']}", 
                          fill="#ecf0f1", font=("Arial", 16, "bold"))
        y += 40
        
        # Type and zone
        canvas.create_text(x0 + 20, y, anchor="w", text=f"Type: {prop['type'].upper()}", 
                          fill="#bdc3c7", font=("Arial", 11))
        if "zone" in prop:
            canvas.create_text(x0 + 20, y + 20, anchor="w", text=f"Zone: {prop['zone']}", 
                              fill="#95a5a6", font=("Arial", 10))
        y += 50
        
        # Price and market info
        price_color = "#f1c40f"
        if prop["type"] == "stock":
            price_text = f"Price per Share: ${prop['price']:.2f}"
        elif prop["type"] == "crypto":
            price_text = f"Price: ${prop['price']:.0f}"
        else:
            price_text = f"Purchase Price: ${prop['price']:.0f}"
        
        canvas.create_text(x0 + 20, y, anchor="w", text=price_text, 
                          fill=price_color, font=("Arial", 12, "bold"))
        y += 35
        
        # Property details
        if "monthly_income" in prop:
            canvas.create_text(x0 + 20, y, anchor="w", 
                              text=f"Monthly Income: ${prop['monthly_income']:.0f}", 
                              fill="#2ecc71", font=("Arial", 11, "bold"))
            y += 25
        
        if "quality" in prop:
            canvas.create_text(x0 + 20, y, anchor="w", text=f"Quality: {prop['quality']}", 
                              fill="#95a5a6", font=("Arial", 10))
            y += 25
        
        if "volatility" in prop:
            vol_color = "#e74c3c" if prop["volatility"] > 2 else "#f39c12" if prop["volatility"] > 1 else "#2ecc71"
            canvas.create_text(x0 + 20, y, anchor="w", text=f"Volatility: {prop['volatility']:.1f}x", 
                              fill=vol_color, font=("Arial", 10))
            y += 25
        
        if "tenants" in prop:
            canvas.create_text(x0 + 20, y, anchor="w", text=f"Tenants: {prop['tenants']}", 
                              fill="#95a5a6", font=("Arial", 10))
            y += 25
        
        if "prestige" in prop:
            canvas.create_text(x0 + 20, y, anchor="w", text=f"Prestige: {prop['prestige']}/100", 
                              fill="#f39c12", font=("Arial", 10))
            y += 25
        
        if "shares_available" in prop:
            canvas.create_text(x0 + 20, y, anchor="w", text=f"Shares Available: {prop['shares_available']}", 
                              fill="#95a5a6", font=("Arial", 10))
            y += 25
        
        if prop["type"] == "liability":
            canvas.create_text(x0 + 20, y, anchor="w", 
                              text=f"Monthly Drain: ${prop['monthly_drain']:.0f}", 
                              fill="#e74c3c", font=("Arial", 10, "bold"))
            y += 20
            canvas.create_text(x0 + 20, y, anchor="w", 
                              text=f"Interest: {prop['interest_rate']*100:.1f}%", 
                              fill="#e74c3c", font=("Arial", 9))
            y += 25
        
        y += 10
        
        # Your cash
        cash_color = "#2ecc71" if self.cash >= prop["price"] else "#e74c3c"
        canvas.create_text(x0 + 20, y, anchor="w", text=f"Your Cash: ${self.cash:,.0f}", 
                          fill=cash_color, font=("Arial", 12, "bold"))
        y += 35
        
        # Action button
        can_afford = self.cash >= prop["price"]
        button_color = "#3498db" if can_afford else "#7f8c8d"
        canvas.create_rectangle(x0 + 40, y, x0 + panel_w - 40, y + 40, 
                               fill=button_color, outline="#ecf0f1", width=2)
        action_text = "BUY (ENTER)" if can_afford else "NOT ENOUGH CASH"
        canvas.create_text(x0 + panel_w / 2, y + 20, text=action_text, 
                          fill="#fff" if can_afford else "#95a5a6", font=("Arial", 12, "bold"))
        y += 50
        
        # Close hint
        canvas.create_text(x0 + panel_w / 2, y0 + panel_h - 15, 
                          text="BACKSPACE to close", 
                          fill="#95a5a6", font=("Arial", 10, "italic"))
    
    def draw_portfolio(self, canvas: tk.Canvas) -> None:
        """Draw portfolio screen"""
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#1a1a1a")
        
        # Header
        canvas.create_text(WIDTH / 2, 25, text="PORTFOLIO MANAGEMENT", 
                          fill="#f1c40f", font=("Arial", 18, "bold"))
        
        # Summary boxes
        y = 65
        box_h = 50
        
        # Cash
        canvas.create_rectangle(20, y, WIDTH / 3 - 10, y + box_h, fill="#2c3e50", outline="#2ecc71", width=2)
        cash_color = "#2ecc71" if self.cash >= 0 else "#e74c3c"
        canvas.create_text(35, y + 15, anchor="w", text="CASH", fill="#ecf0f1", font=("Arial", 10, "bold"))
        canvas.create_text(35, y + 35, anchor="w", text=f"${self.cash:,.0f}", fill=cash_color, font=("Arial", 13, "bold"))
        
        # Net Worth
        canvas.create_rectangle(WIDTH / 3 + 10, y, 2 * WIDTH / 3 - 10, y + box_h, fill="#2c3e50", outline="#3498db", width=2)
        canvas.create_text(WIDTH / 3 + 25, y + 15, anchor="w", text="NET WORTH", fill="#ecf0f1", font=("Arial", 10, "bold"))
        canvas.create_text(WIDTH / 3 + 25, y + 35, anchor="w", text=f"${self.net_worth:,.0f}", fill="#3498db", font=("Arial", 13, "bold"))
        
        # Total Profit
        profit_color = "#2ecc71" if self.total_profit >= 0 else "#e74c3c"
        canvas.create_rectangle(2 * WIDTH / 3 + 10, y, WIDTH - 20, y + box_h, fill="#2c3e50", outline=profit_color, width=2)
        canvas.create_text(2 * WIDTH / 3 + 25, y + 15, anchor="w", text="TOTAL PROFIT", fill="#ecf0f1", font=("Arial", 10, "bold"))
        canvas.create_text(2 * WIDTH / 3 + 25, y + 35, anchor="w", text=f"${self.total_profit:,.0f}", fill=profit_color, font=("Arial", 13, "bold"))
        
        y += 75
        
        # Assets header
        canvas.create_text(20, y, anchor="w", text=f"HOLDINGS ({len(self.portfolio)} assets)", 
                          fill="#ecf0f1", font=("Arial", 12, "bold"))
        y += 30
        
        # Assets list
        if not self.portfolio:
            canvas.create_text(20, y, anchor="w", text="No holdings yet. Start investing!", 
                              fill="#95a5a6", font=("Arial", 11))
        else:
            max_display = 12
            for idx, item in enumerate(self.portfolio[:max_display]):
                if item["type"] == "stock":
                    value = item["current_price"] * item["shares"]
                    gain = item.get("profit", 0)
                    gain_color = "#2ecc71" if gain >= 0 else "#e74c3c"
                    text = f"📈 {item['stock_type'].upper()} x{item['shares']} @ ${item['current_price']:.2f} = ${value:,.0f} ({gain:+,.0f})"
                    canvas.create_text(20, y, anchor="w", text=text, fill=gain_color, font=("Arial", 10))
                elif item["type"] == "crypto":
                    value = item["current_price"] * item.get("coins", 1)
                    gain = item.get("profit", 0)
                    gain_color = "#2ecc71" if gain >= 0 else "#e74c3c"
                    text = f"💰 {item['name']} x{item.get('coins', 1)} @ ${item['current_price']:.0f} ({gain:+,.0f})"
                    canvas.create_text(20, y, anchor="w", text=text, fill=gain_color, font=("Arial", 10))
                else:
                    value = item.get("current_value", item["purchase_price"])
                    gain = item.get("profit", 0)
                    gain_color = "#2ecc71" if gain >= 0 else "#e74c3c"
                    icon = "🏠" if "residential" in item.get("type", "") else "🏢" if "commercial" in item.get("type", "") else "📜"
                    text = f"{icon} {item['name']} = ${value:,.0f} ({gain:+,.0f})"
                    canvas.create_text(20, y, anchor="w", text=text, fill=gain_color, font=("Arial", 10))
                y += 22
            
            if len(self.portfolio) > max_display:
                canvas.create_text(20, y, anchor="w", text=f"... and {len(self.portfolio) - max_display} more assets", 
                                  fill="#95a5a6", font=("Arial", 10, "italic"))
        
        # Achievements
        y = HEIGHT - 80
        canvas.create_text(20, y, anchor="w", text="ACHIEVEMENTS", 
                          fill="#f39c12", font=("Arial", 11, "bold"))
        y += 25
        if self.achievements:
            achv_text = " | ".join(self.achievements)
            canvas.create_text(20, y, anchor="w", text=achv_text, 
                              fill="#f1c40f", font=("Arial", 10))
        else:
            canvas.create_text(20, y, anchor="w", text="Make your first investment to earn achievements!", 
                              fill="#95a5a6", font=("Arial", 10))
        
        # Controls
        canvas.create_text(WIDTH / 2, HEIGHT - 20, text="P or BACKSPACE to return", 
                          fill="#95a5a6", font=("Arial", 10, "italic"))
    
    def draw_market_analysis(self, canvas: tk.Canvas) -> None:
        """Draw market analysis screen"""
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#1a1a1a")
        
        # Header
        canvas.create_text(WIDTH / 2, 25, text="MARKET ANALYSIS", 
                          fill="#f1c40f", font=("Arial", 18, "bold"))
        
        y = 70
        
        # Market categories
        categories = [
            ("REAL ESTATE", ["residential", "commercial", "luxury"], "#3498db"),
            ("STOCKS", ["stocks_tech", "stocks_finance", "stocks_real_estate", "stocks_energy"], "#e67e22"),
            ("ALTERNATIVES", ["crypto", "bonds"], "#f39c12"),
        ]
        
        for cat_name, assets, color in categories:
            canvas.create_text(20, y, anchor="w", text=cat_name, 
                              fill=color, font=("Arial", 12, "bold"))
            y += 25
            
            for asset in assets:
                if asset in self.market_prices:
                    price = self.market_prices[asset]
                    trend = self.price_trends.get(asset, 0)
                    trend_color = "#2ecc71" if trend > 0 else "#e74c3c"
                    trend_arrow = "📈" if trend > 0 else "📉"
                    
                    # Friendly name
                    friendly_name = asset.replace("stocks_", "").upper().replace("_", " ")
                    
                    canvas.create_text(40, y, anchor="w", text=f"{friendly_name}: ${price:.2f} {trend_arrow}", 
                                      fill=trend_color, font=("Arial", 10, "bold"))
                    y += 20
            
            y += 10
        
        # Market events
        y = HEIGHT - 100
        canvas.create_rectangle(20, y, WIDTH - 20, HEIGHT - 30, fill="#2c3e50", outline="#f39c12", width=2)
        canvas.create_text(30, y + 10, anchor="w", text="RECENT MARKET EVENTS", 
                          fill="#f39c12", font=("Arial", 11, "bold"))
        
        if self.transaction_history:
            y += 35
            for trans in self.transaction_history[-5:]:
                text = f"{trans['action']}: {trans['asset']} @ ${trans['price']:.0f}"
                canvas.create_text(30, y, anchor="w", text=text, 
                                  fill="#95a5a6", font=("Arial", 9))
                y += 18
        
        # Controls
        canvas.create_text(WIDTH / 2, HEIGHT - 15, text="M or BACKSPACE to return", 
                          fill="#95a5a6", font=("Arial", 10, "italic"))
    
    def draw(self, canvas: tk.Canvas, player: Player) -> None:
        canvas.delete("all")
        
        # Shake
        sx, sy = 0, 0
        if self.shake > 0:
            sx = random.uniform(-self.shake, self.shake)
            sy = random.uniform(-self.shake, self.shake)
            self.shake *= 0.93
        
        if self.ui_state == "game":
            # Game view
            bg = "#0a0d12" if not self.high_contrast else "#000000"
            canvas.create_rectangle(sx, sy, WIDTH + sx, HEIGHT + sy, fill=bg)
            
            # Draw board zones
            for zone in self.board_zones:
                zone_alpha = 0.1
                canvas.create_oval(zone["x"] - zone["radius"] + sx, zone["y"] - zone["radius"] + sy,
                                 zone["x"] + zone["radius"] + sx, zone["y"] + zone["radius"] + sy,
                                 fill=zone["color"], outline=zone["color"], stipple="gray50")
                canvas.create_text(zone["x"] + sx, zone["y"] - zone["radius"] - 10 + sy,
                                 text=zone["name"], fill=zone["color"], font=("Arial", 10, "bold"))
            
            # Draw properties
            for i, prop in enumerate(self.properties):
                x, y = prop["x"] + sx, prop["y"] + sy
                size = 22 if i == self.highlighted_property else 18
                
                outline_color = "#ffff00" if i == self.highlighted_property else "#fff"
                outline_width = 3 if i == self.highlighted_property else 2
                
                canvas.create_oval(x - size, y - size, x + size, y + size, 
                                 fill=prop["color"], outline=outline_color, width=outline_width)
                canvas.create_text(x, y, text=prop["icon"], font=("Arial", 14))
                
                # Show price if not owned
                if not prop.get("owned"):
                    if prop["type"] == "stock":
                        price_text = f"${prop['price']:.1f}"
                    elif prop["type"] == "crypto":
                        price_text = f"${prop['price']:.0f}"
                    else:
                        price_text = f"${prop['price']:.0f}"
                    canvas.create_text(x, y + 32, text=price_text, fill=prop["color"], font=("Arial", 7, "bold"))
            
            # Draw player
            player.draw(canvas)
            
            # HUD at bottom
            hud_h = 160
            canvas.create_rectangle(0, HEIGHT - hud_h, WIDTH, HEIGHT, fill="#1e272e", outline="#ecf0f1", width=1)
            
            y = HEIGHT - hud_h + 12
            cash_color = "#2ecc71" if self.cash >= 0 else "#e74c3c"
            canvas.create_text(20, y, anchor="w", text=f"💵 Cash: ${self.cash:,.0f}", 
                              fill=cash_color, font=("Arial", 12, "bold"))
            canvas.create_text(20, y + 25, anchor="w", text=f"📊 Net Worth: ${self.net_worth:,.0f}", 
                              fill="#3498db", font=("Arial", 12, "bold"))
            canvas.create_text(20, y + 50, anchor="w", text=f"🎯 Assets: {len(self.portfolio)} | 📈 Profit: ${self.total_profit:,.0f}", 
                              fill="#f1c40f", font=("Arial", 11, "bold"))
            
            # Market event display
            if self.event_message_timer > 0:
                canvas.create_text(WIDTH / 2, HEIGHT - hud_h - 30, text=self.market_event_message,
                                  fill="#f39c12", font=("Arial", 12, "bold"))
            
            # Market snapshot
            canvas.create_text(WIDTH - 20, y, anchor="e",
                              text=f"Tech: ${self.market_prices['stocks_tech']:.1f} | RE: ${self.market_prices['residential']:.0f}",
                              fill="#95a5a6", font=("Arial", 8))
            
            # Controls
            controls_text = "SPACE=Details | P=Portfolio | M=Market | WASD=Move"
            canvas.create_text(WIDTH - 20, y + 60, anchor="e", text=controls_text,
                              fill="#95a5a6", font=("Arial", 8))
        
        elif self.ui_state == "portfolio":
            self.draw_portfolio(canvas)
        
        elif self.ui_state == "market_analysis":
            self.draw_market_analysis(canvas)
        
        elif self.ui_state == "property_detail":
            bg = "#0a0d12" if not self.high_contrast else "#000000"
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=bg)
            for prop in self.properties:
                x, y = prop["x"], prop["y"]
                size = 18
                canvas.create_oval(x - size, y - size, x + size, y + size, 
                                 fill=prop["color"], outline="#fff", width=2)
                canvas.create_text(x, y, text=prop["icon"], font=("Arial", 12))
            player.draw(canvas)
            self.draw_property_detail(canvas)
        
        if self.tutorial_timer > 0:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50")
            canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, text="Loading Tycoon Simulator...",
                              fill="#f1c40f", font=("Arial", 20, "bold"))
            canvas.create_text(WIDTH / 2, HEIGHT / 2 + 30, text="Building your empire in progress",
                              fill="#95a5a6", font=("Arial", 12))
        
        if self.finished:
            self.draw_result(canvas)
        
        self.draw_hud(canvas)