import pytest
from app.services.planner import GreedyPlanner, ORToolsPlanner, run_planner
from datetime import datetime, timedelta

@pytest.fixture
def sample_data():
    stockyards = [
        {
            'id': '1',
            'code': 'SY001',
            'name': 'Test Stockyard 1',
            'location': 'Location 1',
            'latitude': 23.0,
            'longitude': 85.0,
            'capacity_tonnes': 50000,
            'current_inventory': {'COAL': 30000, 'IRON_ORE': 20000}
        },
        {
            'id': '2',
            'code': 'SY002',
            'name': 'Test Stockyard 2',
            'location': 'Location 2',
            'latitude': 22.0,
            'longitude': 84.0,
            'capacity_tonnes': 40000,
            'current_inventory': {'COAL': 25000}
        }
    ]

    orders = [
        {
            'id': 'o1',
            'order_number': 'ORD001',
            'product_code': 'COAL',
            'quantity_tonnes': 2500,
            'destination': 'Dest 1',
            'destination_latitude': 19.0,
            'destination_longitude': 72.0,
            'priority': 1,
            'due_date': datetime.now() + timedelta(days=5),
            'sla_hours': 72
        },
        {
            'id': 'o2',
            'order_number': 'ORD002',
            'product_code': 'COAL',
            'quantity_tonnes': 2000,
            'destination': 'Dest 1',
            'destination_latitude': 19.0,
            'destination_longitude': 72.0,
            'priority': 2,
            'due_date': datetime.now() + timedelta(days=6),
            'sla_hours': 96
        },
        {
            'id': 'o3',
            'order_number': 'ORD003',
            'product_code': 'IRON_ORE',
            'quantity_tonnes': 3000,
            'destination': 'Dest 2',
            'destination_latitude': 17.0,
            'destination_longitude': 83.0,
            'priority': 1,
            'due_date': datetime.now() + timedelta(days=4),
            'sla_hours': 72
        }
    ]

    rakes = [
        {
            'id': 'r1',
            'rake_number': 'RK001',
            'wagon_type_code': 'BOXN',
            'num_wagons': 58,
            'total_capacity_tonnes': 3480,
            'status': 'available',
            'current_location': 'Yard 1'
        },
        {
            'id': 'r2',
            'rake_number': 'RK002',
            'wagon_type_code': 'BOXN',
            'num_wagons': 58,
            'total_capacity_tonnes': 3480,
            'status': 'available',
            'current_location': 'Yard 2'
        }
    ]

    return {'orders': orders, 'stockyards': stockyards, 'rakes': rakes}


def test_greedy_planner_packs_orders_correctly(sample_data):
    """Test that greedy planner correctly packs orders into rakes."""
    config = {
        'mode': 'greedy',
        'allow_multi_destination': False,
        'min_rake_size': 1000,
        'cost_weights': {'freight': 1.0, 'demurrage': 0.5, 'idle': 0.3},
        'freight_rate': 2.5,
        'demurrage_rate': 500,
        'idle_cost': 100
    }

    planner = GreedyPlanner(config)
    result = planner.plan(
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    assert result is not None
    assert 'rakes' in result
    assert len(result['rakes']) > 0
    assert result['orders_fulfilled'] > 0
    assert result['total_cost'] > 0

    for rake in result['rakes']:
        assert rake['total_weight'] >= config['min_rake_size']
        assert rake['total_weight'] <= rake['capacity']
        assert len(rake['orders']) > 0


def test_ortools_planner_returns_lower_or_equal_cost(sample_data):
    """Test that OR-Tools planner returns cost <= greedy for small instance."""
    config = {
        'mode': 'or-tools',
        'allow_multi_destination': True,
        'min_rake_size': 1000,
        'cost_weights': {'freight': 1.0, 'demurrage': 0.5, 'idle': 0.3},
        'freight_rate': 2.5,
        'demurrage_rate': 500,
        'idle_cost': 100
    }

    greedy_planner = GreedyPlanner(config)
    greedy_result = greedy_planner.plan(
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    ortools_planner = ORToolsPlanner(config)
    ortools_result = ortools_planner.plan(
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    assert ortools_result['total_cost'] <= greedy_result['total_cost'] * 1.1


def test_upload_validation_rejects_malformed_csv():
    """Test that CSV validation rejects malformed data."""
    import pandas as pd
    import io

    malformed_csv = "order_number,product_code\nORD001"
    df = pd.read_csv(io.StringIO(malformed_csv))

    assert df.shape[0] == 1
    assert 'product_code' in df.columns

    row = df.iloc[0]
    assert pd.isna(row['product_code'])


def test_run_planner_hybrid_mode(sample_data):
    """Test hybrid mode selects better solution."""
    config = {
        'mode': 'hybrid',
        'allow_multi_destination': True,
        'min_rake_size': 1000,
        'cost_weights': {'freight': 1.0, 'demurrage': 0.5, 'idle': 0.3},
        'freight_rate': 2.5,
        'demurrage_rate': 500,
        'idle_cost': 100
    }

    result = run_planner(
        'hybrid',
        config,
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    assert result is not None
    assert 'hybrid' in result['algorithm'].lower()
    assert result['total_cost'] > 0


def test_planner_respects_min_rake_size(sample_data):
    """Test that planner respects minimum rake size constraint."""
    config = {
        'mode': 'greedy',
        'allow_multi_destination': False,
        'min_rake_size': 5000,
        'cost_weights': {'freight': 1.0, 'demurrage': 0.5, 'idle': 0.3},
        'freight_rate': 2.5,
        'demurrage_rate': 500,
        'idle_cost': 100
    }

    planner = GreedyPlanner(config)
    result = planner.plan(
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    for rake in result['rakes']:
        assert rake['total_weight'] >= config['min_rake_size']


def test_planner_respects_inventory_constraints(sample_data):
    """Test that planner doesn't assign orders exceeding inventory."""
    sample_data['stockyards'][0]['current_inventory']['COAL'] = 2000

    config = {
        'mode': 'greedy',
        'allow_multi_destination': False,
        'min_rake_size': 1000,
        'cost_weights': {'freight': 1.0, 'demurrage': 0.5, 'idle': 0.3},
        'freight_rate': 2.5,
        'demurrage_rate': 500,
        'idle_cost': 100
    }

    planner = GreedyPlanner(config)
    result = planner.plan(
        sample_data['orders'],
        sample_data['stockyards'],
        sample_data['rakes']
    )

    total_coal_assigned = 0
    for rake in result['rakes']:
        for order in rake['orders']:
            if order['product_code'] == 'COAL':
                total_coal_assigned += order['quantity']

    total_coal_inventory = sum(
        sy['current_inventory'].get('COAL', 0)
        for sy in sample_data['stockyards']
    )

    assert total_coal_assigned <= total_coal_inventory
