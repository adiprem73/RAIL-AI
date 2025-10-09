export interface Stockyard {
    id: string;
    code: string;
    name: string;
    location: string;
    latitude?: number;
    longitude?: number;
    capacity_tonnes: number;
    current_inventory: Record<string, number>;
    created_at?: string;
    updated_at?: string;
  }
  
  export interface Order {
    id: string;
    order_number: string;
    product_code: string;
    quantity_tonnes: number;
    source_stockyard_id?: string;
    destination: string;
    destination_latitude?: number;
    destination_longitude?: number;
    priority: number;
    due_date: string;
    sla_hours: number;
    status: 'pending' | 'assigned' | 'fulfilled' | 'cancelled';
    created_at?: string;
    updated_at?: string;
  }
  
  export interface Rake {
    id: string;
    rake_number: string;
    wagon_type_code: string;
    num_wagons: number;
    total_capacity_tonnes: number;
    status: 'available' | 'assigned' | 'in_transit' | 'maintenance';
    current_location?: string;
    availability_date: string;
    created_at?: string;
    updated_at?: string;
  }
  
  export interface Product {
    id: string;
    code: string;
    name: string;
    density: number;
    handling_time: number;
    created_at?: string;
    updated_at?: string;
  }
  
  export interface WagonType {
    id: string;
    code: string;
    name: string;
    capacity_tonnes: number;
    capacity_volume: number;
    tare_weight: number;
    created_at?: string;
    updated_at?: string;
  }
  
  export interface LoadingPoint {
    id: string;
    code: string;
    name: string;
    stockyard_id?: string;
    location: string;
    latitude?: number;
    longitude?: number;
    sidings: number;
    max_rake_length: number;
    products_handled: string[];
    created_at?: string;
    updated_at?: string;
  }
  
  export interface PlanningJob {
    id: string;
    scenario_name: string;
    notes?: string;
    config: Record<string, any>;
    status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    logs: string;
    started_at?: string;
    completed_at?: string;
    plan_id?: string;
  }
  
  export interface Plan {
    id: string;
    job_id: string;
    name: string;
    total_cost: number;
    freight_cost: number;
    demurrage_cost: number;
    idle_cost: number;
    utilization_pct: number;
    orders_fulfilled: number;
    total_orders: number;
    committed: boolean;
    committed_at?: string;
    created_at: string;
    rakes: PlanRake[];
    algorithm?: string;
  }
  
  export interface PlanRake {
    id: string;
    rake_number: string;
    origin_stockyard_id?: string;
    origin_stockyard_name?: string;
    origin_stockyard_code?: string;
    destinations: string[];
    orders_assigned: OrderAssignment[];
    total_weight: number;
    utilization_pct: number;
    freight_cost: number;
  }
  
  export interface OrderAssignment {
    order_id: string;
    order_number: string;
    product_code: string;
    quantity: number;
    destination: string;
    freight_cost: number;
  }
  
  export type DatasetType = 'stockyards' | 'orders' | 'rakes' | 'loading_points' | 'products' | 'wagon_types';
  