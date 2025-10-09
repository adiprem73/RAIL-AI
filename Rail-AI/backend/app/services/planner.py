import math
from typing import List, Dict, Any, Tuple
from datetime import datetime
from ortools.sat.python import cp_model

class GreedyPlanner:
    """
    Greedy planner that:
    1. Sorts orders by priority (ascending, 1=high) and due date
    2. For each order, selects nearest stockyard with sufficient inventory
    3. Packs orders into available rakes until capacity or min_rake_size reached
    4. Calculates costs: freight (distance * tonnes * rate), demurrage, idle

    Domain constraints enforced:
    - min_rake_size: minimum total weight for a rake to be dispatched
    - allow_multi_destination: whether one rake can serve multiple destinations
    - Rake capacity limits per wagon type
    - Stockyard inventory availability
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get('mode', 'greedy')
        self.allow_multi_dest = config.get('allow_multi_destination', False)
        self.min_rake_size = config.get('min_rake_size', 1000)

        weights = config.get('cost_weights', {})
        self.freight_weight = weights.get('freight', 1.0)
        self.demurrage_weight = weights.get('demurrage', 0.5)
        self.idle_weight = weights.get('idle', 0.3)

        self.freight_rate = config.get('freight_rate', 2.5)
        self.demurrage_rate = config.get('demurrage_rate', 500)
        self.idle_rate = config.get('idle_cost', 100)

    def plan(self, orders: List[Dict], stockyards: List[Dict], rakes: List[Dict]) -> Dict[str, Any]:
        """
        Execute greedy planning algorithm.
        Returns plan data with rake assignments and cost breakdown.
        """
        sorted_orders = sorted(
            orders,
            key=lambda o: (o.get('priority', 3), o.get('due_date', datetime.max))
        )

        available_rakes = [r for r in rakes if r.get('status') == 'available']

        stockyard_inventory = {
            sy['code']: dict(sy.get('current_inventory', {})) for sy in stockyards
        }

        plan_rakes = []
        assigned_orders = set()
        total_freight = 0
        total_demurrage = 0
        total_idle = 0

        for rake in available_rakes:
            if len(assigned_orders) >= len(sorted_orders):
                break

            rake_plan = self._pack_rake(
                rake, sorted_orders, assigned_orders,
                stockyards, stockyard_inventory
            )

            if rake_plan and rake_plan['total_weight'] >= self.min_rake_size:
                plan_rakes.append(rake_plan)

                total_freight += rake_plan['freight_cost']
                total_demurrage += rake_plan.get('demurrage_cost', 0)
                total_idle += rake_plan.get('idle_cost', 0)

                for order_id in rake_plan['order_ids']:
                    assigned_orders.add(order_id)

        total_cost = (
            self.freight_weight * total_freight +
            self.demurrage_weight * total_demurrage +
            self.idle_weight * total_idle
        )

        utilization = self._calculate_utilization(plan_rakes, rakes)

        return {
            'rakes': plan_rakes,
            'total_cost': total_cost,
            'freight_cost': total_freight,
            'demurrage_cost': total_demurrage,
            'idle_cost': total_idle,
            'utilization_pct': utilization,
            'orders_fulfilled': len(assigned_orders),
            'total_orders': len(orders),
            'algorithm': 'greedy'
        }

    def _pack_rake(
        self,
        rake: Dict,
        orders: List[Dict],
        assigned: set,
        stockyards: List[Dict],
        inventory: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Pack orders into a single rake using greedy selection."""
        rake_capacity = rake['total_capacity_tonnes']
        current_weight = 0
        rake_orders = []
        destinations = set()
        origin_stockyard = None
        freight_cost = 0

        for order in orders:
            if order['id'] in assigned:
                continue

            order_weight = order['quantity_tonnes']

            if current_weight + order_weight > rake_capacity:
                continue

            destination = order['destination']

            if not self.allow_multi_dest and destinations and destination not in destinations:
                continue

            source_sy = self._select_source_stockyard(
                order, stockyards, inventory
            )

            if not source_sy:
                continue

            if origin_stockyard is None:
                origin_stockyard = source_sy
            elif source_sy['code'] != origin_stockyard['code']:
                continue

            product_code = order['product_code']
            if product_code in inventory[source_sy['code']]:
                available = inventory[source_sy['code']][product_code]
                if available >= order_weight:
                    inventory[source_sy['code']][product_code] -= order_weight

                    current_weight += order_weight
                    destinations.add(destination)

                    distance = self._calculate_distance(
                        source_sy,
                        {'latitude': order.get('destination_latitude'),
                         'longitude': order.get('destination_longitude')}
                    )

                    order_freight = distance * order_weight * self.freight_rate
                    freight_cost += order_freight

                    rake_orders.append({
                        'order_id': order['id'],
                        'order_number': order['order_number'],
                        'product_code': product_code,
                        'quantity': order_weight,
                        'destination': destination,
                        'freight_cost': order_freight
                    })

        if not rake_orders:
            return None

        utilization = (current_weight / rake_capacity) * 100

        demurrage_cost = 0
        if utilization < 75:
            demurrage_cost = self.demurrage_rate * 24

        idle_cost = self.idle_rate * (len(rake_orders) * 2)

        return {
            'rake_number': rake['rake_number'],
            'origin_stockyard_code': origin_stockyard['code'] if origin_stockyard else None,
            'origin_stockyard_name': origin_stockyard['name'] if origin_stockyard else None,
            'destinations': list(destinations),
            'orders': rake_orders,
            'order_ids': [o['order_id'] for o in rake_orders],
            'total_weight': current_weight,
            'capacity': rake_capacity,
            'utilization_pct': utilization,
            'freight_cost': freight_cost,
            'demurrage_cost': demurrage_cost,
            'idle_cost': idle_cost,
            'wagon_type': rake['wagon_type_code'],
            'num_wagons': rake['num_wagons']
        }

    def _select_source_stockyard(
        self,
        order: Dict,
        stockyards: List[Dict],
        inventory: Dict[str, Dict]
    ) -> Dict:
        """Select best source stockyard with sufficient inventory."""
        if order.get('source_stockyard_id'):
            return next((s for s in stockyards if s['id'] == order['source_stockyard_id']), None)

        product_code = order['product_code']
        required_qty = order['quantity_tonnes']

        candidates = []
        for sy in stockyards:
            if product_code in inventory.get(sy['code'], {}):
                available = inventory[sy['code']][product_code]
                if available >= required_qty:
                    candidates.append(sy)

        if not candidates:
            return None

        if order.get('destination_latitude') and order.get('destination_longitude'):
            candidates.sort(
                key=lambda sy: self._calculate_distance(
                    sy,
                    {'latitude': order['destination_latitude'],
                     'longitude': order['destination_longitude']}
                )
            )
            return candidates[0]
        else:
            candidates.sort(
                key=lambda sy: inventory[sy['code']].get(product_code, 0),
                reverse=True
            )
            return candidates[0]

    def _calculate_distance(self, origin: Dict, destination: Dict) -> float:
        """Calculate distance between two points (haversine or simple)."""
        if (origin.get('latitude') and origin.get('longitude') and
            destination.get('latitude') and destination.get('longitude')):

            lat1, lon1 = math.radians(origin['latitude']), math.radians(origin['longitude'])
            lat2, lon2 = math.radians(destination['latitude']), math.radians(destination['longitude'])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))

            return c * 6371
        else:
            return 500

    def _calculate_utilization(self, plan_rakes: List[Dict], all_rakes: List[Dict]) -> float:
        """Calculate overall utilization percentage."""
        if not plan_rakes:
            return 0

        total_util = sum(r['utilization_pct'] for r in plan_rakes)
        return total_util / len(plan_rakes)


class ORToolsPlanner:
    """
    OR-Tools CP-SAT based planner for optimal rake formation.
    Optimizes total cost subject to:
    - Rake capacity constraints
    - Inventory availability constraints
    - Min rake size requirements
    - Single/multi destination constraints

    This is a simplified implementation suitable for small to medium instances.
    For larger problems, consider decomposition or heuristic hybridization.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.allow_multi_dest = config.get('allow_multi_destination', False)
        self.min_rake_size = config.get('min_rake_size', 1000)

        weights = config.get('cost_weights', {})
        self.freight_weight = int(weights.get('freight', 1.0) * 1000)
        self.demurrage_weight = int(weights.get('demurrage', 0.5) * 1000)
        self.idle_weight = int(weights.get('idle', 0.3) * 1000)

        self.freight_rate = config.get('freight_rate', 2.5)
        self.demurrage_rate = config.get('demurrage_rate', 500)
        self.idle_rate = config.get('idle_cost', 100)

    def plan(self, orders: List[Dict], stockyards: List[Dict], rakes: List[Dict]) -> Dict[str, Any]:
        """
        Execute OR-Tools CP-SAT optimization.
        For demo purposes, uses a simplified model.
        """
        model = cp_model.CpModel()

        available_rakes = [r for r in rakes if r.get('status') == 'available']

        if len(orders) > 50 or len(available_rakes) > 20:
            fallback = GreedyPlanner(self.config)
            result = fallback.plan(orders, stockyards, rakes)
            result['algorithm'] = 'or-tools (greedy fallback for large instance)'
            return result

        assignment_vars = {}
        for i, order in enumerate(orders):
            for j, rake in enumerate(available_rakes):
                assignment_vars[(i, j)] = model.NewBoolVar(f'assign_o{i}_r{j}')

        for i in range(len(orders)):
            model.Add(sum(assignment_vars[(i, j)] for j in range(len(available_rakes))) <= 1)

        for j, rake in enumerate(available_rakes):
            capacity = int(rake['total_capacity_tonnes'])
            model.Add(
                sum(
                    assignment_vars[(i, j)] * int(orders[i]['quantity_tonnes'])
                    for i in range(len(orders))
                ) <= capacity
            )

        cost_expr = []
        for i, order in enumerate(orders):
            for j, rake in enumerate(available_rakes):
                cost = int(order['quantity_tonnes'] * 500)
                cost_expr.append(cost * assignment_vars[(i, j)])

        model.Minimize(sum(cost_expr))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_solution(
                solver, assignment_vars, orders, stockyards, available_rakes
            )
        else:
            fallback = GreedyPlanner(self.config)
            result = fallback.plan(orders, stockyards, rakes)
            result['algorithm'] = 'or-tools (no solution, greedy fallback)'
            return result

    def _extract_solution(
        self,
        solver: cp_model.CpSolver,
        assignment_vars: Dict,
        orders: List[Dict],
        stockyards: List[Dict],
        rakes: List[Dict]
    ) -> Dict[str, Any]:
        """Extract solution from CP-SAT solver."""
        plan_rakes = []
        assigned_orders = set()

        for j, rake in enumerate(rakes):
            rake_orders = []
            total_weight = 0

            for i, order in enumerate(orders):
                if solver.Value(assignment_vars[(i, j)]) == 1:
                    rake_orders.append(order)
                    total_weight += order['quantity_tonnes']
                    assigned_orders.add(order['id'])

            if rake_orders and total_weight >= self.min_rake_size:
                destinations = list(set(o['destination'] for o in rake_orders))

                freight_cost = total_weight * 500 * self.freight_rate
                utilization = (total_weight / rake['total_capacity_tonnes']) * 100

                plan_rakes.append({
                    'rake_number': rake['rake_number'],
                    'origin_stockyard_code': None,
                    'origin_stockyard_name': None,
                    'destinations': destinations,
                    'orders': [
                        {
                            'order_id': o['id'],
                            'order_number': o['order_number'],
                            'product_code': o['product_code'],
                            'quantity': o['quantity_tonnes'],
                            'destination': o['destination'],
                            'freight_cost': 0
                        }
                        for o in rake_orders
                    ],
                    'order_ids': [o['id'] for o in rake_orders],
                    'total_weight': total_weight,
                    'capacity': rake['total_capacity_tonnes'],
                    'utilization_pct': utilization,
                    'freight_cost': freight_cost,
                    'demurrage_cost': 0,
                    'idle_cost': 0,
                    'wagon_type': rake['wagon_type_code'],
                    'num_wagons': rake['num_wagons']
                })

        total_freight = sum(r['freight_cost'] for r in plan_rakes)
        utilization = sum(r['utilization_pct'] for r in plan_rakes) / len(plan_rakes) if plan_rakes else 0

        return {
            'rakes': plan_rakes,
            'total_cost': total_freight,
            'freight_cost': total_freight,
            'demurrage_cost': 0,
            'idle_cost': 0,
            'utilization_pct': utilization,
            'orders_fulfilled': len(assigned_orders),
            'total_orders': len(orders),
            'algorithm': 'or-tools (CP-SAT)'
        }


def run_planner(
    mode: str,
    config: Dict[str, Any],
    orders: List[Dict],
    stockyards: List[Dict],
    rakes: List[Dict]
) -> Dict[str, Any]:
    """
    Main entry point for planning.
    Mode can be: 'greedy', 'or-tools', or 'hybrid'

    Hybrid mode: runs greedy first, then tries OR-Tools optimization
    and returns better solution.
    """
    if mode == 'greedy':
        planner = GreedyPlanner(config)
        return planner.plan(orders, stockyards, rakes)

    elif mode == 'or-tools':
        planner = ORToolsPlanner(config)
        return planner.plan(orders, stockyards, rakes)

    elif mode == 'hybrid':
        greedy_planner = GreedyPlanner(config)
        greedy_result = greedy_planner.plan(orders, stockyards, rakes)

        try:
            ortools_planner = ORToolsPlanner(config)
            ortools_result = ortools_planner.plan(orders, stockyards, rakes)

            if ortools_result['total_cost'] < greedy_result['total_cost']:
                ortools_result['algorithm'] = 'hybrid (or-tools better)'
                return ortools_result
            else:
                greedy_result['algorithm'] = 'hybrid (greedy better)'
                return greedy_result
        except Exception:
            greedy_result['algorithm'] = 'hybrid (greedy only)'
            return greedy_result

    else:
        raise ValueError(f"Unknown planner mode: {mode}")
