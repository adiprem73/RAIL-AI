from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    density = Column(Float, default=1.5)
    handling_time = Column(Float, default=2.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WagonType(Base):
    __tablename__ = "wagon_types"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    capacity_tonnes = Column(Float, nullable=False)
    capacity_volume = Column(Float, default=50.0)
    tare_weight = Column(Float, default=20.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProductWagonCompatibility(Base):
    __tablename__ = "product_wagon_compatibility"

    product_id = Column(String, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    wagon_type_id = Column(String, ForeignKey('wagon_types.id', ondelete='CASCADE'), primary_key=True)
    loading_efficiency = Column(Float, default=1.0)

    __table_args__ = (
        CheckConstraint('loading_efficiency >= 0 AND loading_efficiency <= 1'),
    )

class Stockyard(Base):
    __tablename__ = "stockyards"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity_tonnes = Column(Float, default=100000)
    current_inventory = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LoadingPoint(Base):
    __tablename__ = "loading_points"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    stockyard_id = Column(String, ForeignKey('stockyards.id', ondelete='SET NULL'), nullable=True)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sidings = Column(Integer, default=2)
    max_rake_length = Column(Integer, default=58)
    products_handled = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_number = Column(String, unique=True, nullable=False, index=True)
    product_code = Column(String, nullable=False)
    quantity_tonnes = Column(Float, nullable=False)
    source_stockyard_id = Column(String, ForeignKey('stockyards.id', ondelete='SET NULL'), nullable=True)
    destination = Column(String, nullable=False)
    destination_latitude = Column(Float, nullable=True)
    destination_longitude = Column(Float, nullable=True)
    priority = Column(Integer, default=3)
    due_date = Column(DateTime, nullable=False)
    sla_hours = Column(Float, default=72)
    status = Column(String, default='pending', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('quantity_tonnes > 0'),
        CheckConstraint('priority >= 1 AND priority <= 5'),
        CheckConstraint("status IN ('pending', 'assigned', 'fulfilled', 'cancelled')"),
    )

class Rake(Base):
    __tablename__ = "rakes"

    id = Column(String, primary_key=True, default=generate_uuid)
    rake_number = Column(String, unique=True, nullable=False, index=True)
    wagon_type_code = Column(String, nullable=False)
    num_wagons = Column(Integer, nullable=False)
    total_capacity_tonnes = Column(Float, nullable=False)
    status = Column(String, default='available', index=True)
    current_location = Column(String, nullable=True)
    availability_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('num_wagons > 0'),
        CheckConstraint('total_capacity_tonnes > 0'),
        CheckConstraint("status IN ('available', 'assigned', 'in_transit', 'maintenance')"),
    )

class PlanningJob(Base):
    __tablename__ = "planning_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    scenario_name = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    status = Column(String, default='queued', index=True)
    progress = Column(Float, default=0)
    logs = Column(Text, default='')
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100'),
        CheckConstraint("status IN ('queued', 'running', 'completed', 'failed', 'cancelled')"),
    )

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey('planning_jobs.id', ondelete='CASCADE'))
    name = Column(String, nullable=False)
    plan_data = Column(JSON, default=dict)
    total_cost = Column(Float, default=0)
    freight_cost = Column(Float, default=0)
    demurrage_cost = Column(Float, default=0)
    idle_cost = Column(Float, default=0)
    utilization_pct = Column(Float, default=0)
    orders_fulfilled = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    committed = Column(Boolean, default=False, index=True)
    committed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlanRake(Base):
    __tablename__ = "plan_rakes"

    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(String, ForeignKey('plans.id', ondelete='CASCADE'), index=True)
    rake_number = Column(String, nullable=False)
    origin_stockyard_id = Column(String, ForeignKey('stockyards.id', ondelete='SET NULL'), nullable=True)
    destinations = Column(JSON, default=list)
    orders_assigned = Column(JSON, default=list)
    total_weight = Column(Float, default=0)
    utilization_pct = Column(Float, default=0)
    freight_cost = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(JSON, default=dict)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
