#!/usr/bin/env python3
"""
Credit Card Cycling Optimizer

Strategy: Use PayPal Business to cycle CC balances at optimal points
- Minimize interest
- Minimize fees
- Maximize credit score impact
- Time payments optimally
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

class CCOptimizer:
    """Optimize credit card cycling via PayPal Business"""
    
    # PayPal fees
    PAYPAL_SEND_FEE_PCT = 2.9  # PayPal goods/services fee
    PAYPAL_SEND_FEE_FIXED = 0.30  # Fixed fee per transaction
    
    def __init__(self, cards, paypal_balance=0, monthly_income=0):
        self.cards = cards
        self.paypal_balance = paypal_balance
        self.monthly_income = monthly_income
    
    def analyze(self):
        """Full analysis of current state"""
        total_limit = sum(c["limit"] for c in self.cards)
        total_balance = sum(c["balance"] for c in self.cards)
        total_available = total_limit - total_balance
        utilization = (total_balance / total_limit * 100) if total_limit > 0 else 0
        
        # Monthly interest cost
        monthly_interest = sum(
            c["balance"] * (c["apr"] / 100 / 12) 
            for c in self.cards
        )
        
        # Sort cards by priority
        by_apr = sorted(self.cards, key=lambda x: x["apr"], reverse=True)
        by_util = sorted(self.cards, key=lambda x: x["balance"]/x["limit"], reverse=True)
        
        return {
            "summary": {
                "total_limit": total_limit,
                "total_balance": total_balance,
                "total_available": total_available,
                "utilization_pct": round(utilization, 1),
                "monthly_interest": round(monthly_interest, 2),
                "annual_interest": round(monthly_interest * 12, 2)
            },
            "priority_by_apr": [c["name"] for c in by_apr],
            "priority_by_utilization": [c["name"] for c in by_util]
        }
    
    def paypal_cycle_cost(self, amount):
        """Calculate cost to cycle amount through PayPal Business"""
        fee = amount * (self.PAYPAL_SEND_FEE_PCT / 100) + self.PAYPAL_SEND_FEE_FIXED
        return round(fee, 2)
    
    def optimal_cycle_plan(self):
        """
        Generate optimal cycling plan
        
        Strategy:
        1. Identify cards with highest APR
        2. Identify cards with available balance
        3. Calculate if cycling saves money vs interest
        4. Generate action plan
        """
        plan = []
        
        # Cards sorted by APR (highest first = pay these off)
        high_apr = [c for c in self.cards if c["apr"] > 20 and c["balance"] > 0]
        
        # Cards with available credit (can receive balance)
        available = [c for c in self.cards if (c["limit"] - c["balance"]) > 500]
        
        for source in high_apr:
            monthly_interest = source["balance"] * (source["apr"] / 100 / 12)
            
            # Find best destination
            for dest in available:
                if dest["name"] == source["name"]:
                    continue
                    
                space = dest["limit"] - dest["balance"]
                transfer_amount = min(source["balance"], space, 2000)  # Cap at 2k per cycle
                
                if transfer_amount < 100:
                    continue
                
                # Cost analysis
                paypal_fee = self.paypal_cycle_cost(transfer_amount)
                interest_saved = transfer_amount * (source["apr"] / 100 / 12)
                net_benefit = interest_saved - paypal_fee
                
                if net_benefit > 0:
                    plan.append({
                        "action": "cycle",
                        "from": source["name"],
                        "to": dest["name"],
                        "amount": transfer_amount,
                        "paypal_fee": paypal_fee,
                        "monthly_interest_saved": round(interest_saved, 2),
                        "net_monthly_benefit": round(net_benefit, 2),
                        "method": "PayPal Business send to self, pay CC with PayPal balance"
                    })
        
        # Sort by net benefit
        plan.sort(key=lambda x: x["net_monthly_benefit"], reverse=True)
        
        return plan
    
    def payment_schedule(self):
        """
        Optimal payment timing for credit score
        
        Rules:
        - Pay before statement closes to reduce reported utilization
        - Pay minimum by due date to avoid late fees
        - Target <30% utilization on each card for best score impact
        """
        schedule = []
        
        for card in self.cards:
            util = card["balance"] / card["limit"] * 100
            target_balance = card["limit"] * 0.29  # Target 29% utilization
            
            if util > 30:
                payment_needed = card["balance"] - target_balance
                schedule.append({
                    "card": card["name"],
                    "current_util": f"{util:.0f}%",
                    "payment_needed_for_30pct": round(payment_needed, 2),
                    "timing": "Before statement close date",
                    "priority": "high" if util > 50 else "medium"
                })
        
        return schedule


def main():
    """Example usage with Yair's data"""
    
    # Example cards (Yair should update with real data)
    cards = [
        {"name": "Card1", "limit": 8000, "balance": 6000, "apr": 24.99, "due_date": 15},
        {"name": "Card2", "limit": 6000, "balance": 5000, "apr": 22.99, "due_date": 20},
        {"name": "Card3", "limit": 5000, "balance": 4000, "apr": 19.99, "due_date": 10},
        {"name": "Card4", "limit": 5000, "balance": 3000, "apr": 17.99, "due_date": 25},
    ]
    
    optimizer = CCOptimizer(cards, paypal_balance=1000)
    
    print("=" * 60)
    print("CREDIT CARD CYCLING OPTIMIZER")
    print("=" * 60)
    print()
    
    analysis = optimizer.analyze()
    print("CURRENT STATE:")
    print(f"  Total Limit:     ${analysis['summary']['total_limit']:,.0f}")
    print(f"  Total Balance:   ${analysis['summary']['total_balance']:,.0f}")
    print(f"  Available:       ${analysis['summary']['total_available']:,.0f}")
    print(f"  Utilization:     {analysis['summary']['utilization_pct']}%")
    print(f"  Monthly Interest:${analysis['summary']['monthly_interest']:,.2f}")
    print(f"  Annual Interest: ${analysis['summary']['annual_interest']:,.2f}")
    print()
    
    print("OPTIMAL CYCLING PLAN:")
    plan = optimizer.optimal_cycle_plan()
    for i, action in enumerate(plan, 1):
        print(f"  {i}. Move ${action['amount']:,.0f} from {action['from']} to {action['to']}")
        print(f"     PayPal fee: ${action['paypal_fee']:.2f}")
        print(f"     Interest saved: ${action['monthly_interest_saved']:.2f}/mo")
        print(f"     Net benefit: ${action['net_monthly_benefit']:.2f}/mo")
        print()
    
    print("PAYMENT SCHEDULE (for credit score):")
    schedule = optimizer.payment_schedule()
    for item in schedule:
        print(f"  {item['card']}: Pay ${item['payment_needed_for_30pct']:,.0f} to reach 30% util")
        print(f"     Current: {item['current_util']}, Priority: {item['priority']}")


if __name__ == "__main__":
    main()
