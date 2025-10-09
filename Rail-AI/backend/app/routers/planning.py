from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import asyncio
import traceback
from ..database import get_db
from ..models import *
from ..services import run_planner

router = APIRouter(prefix="/api", tags=["planning"])

def execute_planning_job(job_id: str, config: Dict[str, Any]):
    """
    Background task to execute planning job.
    Updates job status and creates plan in database.
    """
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        job = db.query(PlanningJob).filter(PlanningJob.id == job_id).first()
        if not job:
            return

        job.status = 'running'
        job.started_at = datetime.utcnow()
        job.logs += f"[{datetime.utcnow()}] Starting planning job\n"
        db.commit()

        orders = db.query(Order).filter(Order.status == 'pending').all()
        stockyards = db.query(Stockyard).all()
        rakes = db.query(Rake).filter(Rake.status == 'available').all()

        job.logs += f"[{datetime.utcnow()}] Loaded {len(orders)} orders, {len(stockyards)} stockyards, {len(rakes)} rakes\n"
        job.progress = 20
        db.commit()

        orders_data = [
            {
                'id': o.id,
                'order_number': o.order_number,
                'product_code': o.product_code,
                'quantity_tonnes': o.quantity_tonnes,
                'source_stockyard_id': o.source_stockyard_id,
                'destination': o.destination,
                'destination_latitude': o.destination_latitude,
                'destination_longitude': o.destination_longitude,
                'priority': o.priority,
                'due_date': o.due_date,
                'sla_hours': o.sla_hours
            }
            for o in orders
        ]

        stockyards_data = [
            {
                'id': s.id,
                'code': s.code,
                'name': s.name,
                'location': s.location,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'capacity_tonnes': s.capacity_tonnes,
                'current_inventory': s.current_inventory or {}
            }
            for s in stockyards
        ]

        rakes_data = [
            {
                'id': r.id,
                'rake_number': r.rake_number,
                'wagon_type_code': r.wagon_type_code,
                'num_wagons': r.num_wagons,
                'total_capacity_tonnes': r.total_capacity_tonnes,
                'status': r.status,
                'current_location': r.current_location
            }
            for r in rakes
        ]

        job.logs += f"[{datetime.utcnow()}] Running {config.get('mode', 'greedy')} planner\n"
        job.progress = 40
        db.commit()

        plan_result = run_planner(
            mode=config.get('mode', 'greedy'),
            config=config,
            orders=orders_data,
            stockyards=stockyards_data,
            rakes=rakes_data
        )

        job.logs += f"[{datetime.utcnow()}] Planning completed. Generated {len(plan_result['rakes'])} rake assignments\n"
        job.progress = 80
        db.commit()

        plan = Plan(
            job_id=job_id,
            name=job.scenario_name,
            plan_data=plan_result,
            total_cost=plan_result['total_cost'],
            freight_cost=plan_result['freight_cost'],
            demurrage_cost=plan_result['demurrage_cost'],
            idle_cost=plan_result['idle_cost'],
            utilization_pct=plan_result['utilization_pct'],
            orders_fulfilled=plan_result['orders_fulfilled'],
            total_orders=plan_result['total_orders']
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        for rake_plan in plan_result['rakes']:
            origin_sy = None
            if rake_plan.get('origin_stockyard_code'):
                origin_sy = db.query(Stockyard).filter(
                    Stockyard.code == rake_plan['origin_stockyard_code']
                ).first()

            plan_rake = PlanRake(
                plan_id=plan.id,
                rake_number=rake_plan['rake_number'],
                origin_stockyard_id=origin_sy.id if origin_sy else None,
                destinations=rake_plan['destinations'],
                orders_assigned=rake_plan['orders'],
                total_weight=rake_plan['total_weight'],
                utilization_pct=rake_plan['utilization_pct'],
                freight_cost=rake_plan['freight_cost']
            )
            db.add(plan_rake)

        db.commit()

        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.progress = 100
        job.logs += f"[{datetime.utcnow()}] Job completed successfully. Plan ID: {plan.id}\n"
        db.commit()

    except Exception as e:
        job = db.query(PlanningJob).filter(PlanningJob.id == job_id).first()
        if job:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.logs += f"[{datetime.utcnow()}] ERROR: {str(e)}\n{traceback.format_exc()}\n"
            db.commit()

    finally:
        db.close()

@router.post("/plan/generate")
async def generate_plan(
    scenario_name: str,
    config: Dict[str, Any],
    notes: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Create a new planning job and run planner in background.
    Returns job ID for status tracking.
    """
    job = PlanningJob(
        scenario_name=scenario_name,
        notes=notes,
        config=config,
        status='queued'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(execute_planning_job, job.id, config)

    return {
        "job_id": job.id,
        "status": "queued",
        "message": "Planning job queued successfully"
    }

@router.get("/job/{job_id}/status")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get current status and logs for a planning job."""
    job = db.query(PlanningJob).filter(PlanningJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    plan = None
    if job.status == 'completed':
        plan = db.query(Plan).filter(Plan.job_id == job_id).first()

    return {
        "job_id": job.id,
        "scenario_name": job.scenario_name,
        "status": job.status,
        "progress": job.progress,
        "logs": job.logs,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "plan_id": plan.id if plan else None
    }

@router.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running or queued job."""
    job = db.query(PlanningJob).filter(PlanningJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ['completed', 'failed', 'cancelled']:
        raise HTTPException(status_code=400, detail="Cannot cancel job in current state")

    job.status = 'cancelled'
    job.completed_at = datetime.utcnow()
    job.logs += f"[{datetime.utcnow()}] Job cancelled by user\n"
    db.commit()

    return {"message": "Job cancelled successfully"}

@router.get("/plan/{plan_id}")
async def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get complete plan details including rake assignments."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_rakes = db.query(PlanRake).filter(PlanRake.plan_id == plan_id).all()

    rakes_data = []
    for pr in plan_rakes:
        rake_data = {
            'id': pr.id,
            'rake_number': pr.rake_number,
            'origin_stockyard_id': pr.origin_stockyard_id,
            'destinations': pr.destinations,
            'orders_assigned': pr.orders_assigned,
            'total_weight': pr.total_weight,
            'utilization_pct': pr.utilization_pct,
            'freight_cost': pr.freight_cost
        }

        if pr.origin_stockyard_id:
            origin = db.query(Stockyard).filter(Stockyard.id == pr.origin_stockyard_id).first()
            if origin:
                rake_data['origin_stockyard_name'] = origin.name
                rake_data['origin_stockyard_code'] = origin.code

        rakes_data.append(rake_data)

    return {
        "id": plan.id,
        "job_id": plan.job_id,
        "name": plan.name,
        "total_cost": plan.total_cost,
        "freight_cost": plan.freight_cost,
        "demurrage_cost": plan.demurrage_cost,
        "idle_cost": plan.idle_cost,
        "utilization_pct": plan.utilization_pct,
        "orders_fulfilled": plan.orders_fulfilled,
        "total_orders": plan.total_orders,
        "committed": plan.committed,
        "committed_at": plan.committed_at.isoformat() if plan.committed_at else None,
        "created_at": plan.created_at.isoformat(),
        "rakes": rakes_data,
        "algorithm": plan.plan_data.get('algorithm', 'unknown')
    }

@router.post("/plan/{plan_id}/explain")
async def explain_plan(plan_id: str, db: Session = Depends(get_db)):
    """
    Generate natural language explanation for a plan.
    This is a stub that provides structured explanation.
    TODO: Replace with actual LLM API call (OpenAI, HuggingFace, etc.)
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_rakes = db.query(PlanRake).filter(PlanRake.plan_id == plan_id).all()

    explanation = f"""## Plan Summary: {plan.name}

This plan was generated using the {plan.plan_data.get('algorithm', 'unknown')} algorithm and successfully allocated {plan.orders_fulfilled} out of {plan.total_orders} orders across {len(plan_rakes)} rakes.

### Cost Breakdown
- **Total Cost**: ₹{plan.total_cost:,.2f}
- **Freight Cost**: ₹{plan.freight_cost:,.2f} ({plan.freight_cost/plan.total_cost*100:.1f}% of total)
- **Demurrage Cost**: ₹{plan.demurrage_cost:,.2f}
- **Idle Freight Cost**: ₹{plan.idle_cost:,.2f}

### Utilization
Average rake utilization is {plan.utilization_pct:.1f}%. {'This meets the target utilization threshold.' if plan.utilization_pct >= 75 else 'Consider consolidating orders to improve utilization.'}

### Rake Assignments
"""

    for idx, rake in enumerate(plan_rakes, 1):
        explanation += f"\n**Rake {idx}: {rake.rake_number}**\n"
        explanation += f"- Origin: {rake.orders_assigned[0].get('order_number', 'N/A') if rake.orders_assigned else 'N/A'}\n"
        explanation += f"- Destinations: {', '.join(rake.destinations)}\n"
        explanation += f"- Total Weight: {rake.total_weight:.0f} tonnes ({rake.utilization_pct:.1f}% utilization)\n"
        explanation += f"- Orders: {len(rake.orders_assigned)}\n"

    explanation += "\n### Recommendations\n"

    if plan.utilization_pct < 75:
        explanation += "- Consider consolidating orders or using smaller rakes to improve cost efficiency.\n"

    if plan.orders_fulfilled < plan.total_orders:
        unfulfilled = plan.total_orders - plan.orders_fulfilled
        explanation += f"- {unfulfilled} orders remain unfulfilled. Review inventory levels and rake availability.\n"

    explanation += "- Review demurrage costs and optimize loading schedules if high.\n"

    return {
        "plan_id": plan_id,
        "explanation": explanation,
        "llm_model": "stub (replace with actual LLM)",
        "generated_at": datetime.utcnow().isoformat()
    }

@router.post("/plan/{plan_id}/commit")
async def commit_plan(plan_id: str, db: Session = Depends(get_db)):
    """Mark a plan as committed for execution."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.committed:
        raise HTTPException(status_code=400, detail="Plan already committed")

    plan.committed = True
    plan.committed_at = datetime.utcnow()

    plan_rakes = db.query(PlanRake).filter(PlanRake.plan_id == plan_id).all()

    for plan_rake in plan_rakes:
        rake = db.query(Rake).filter(Rake.rake_number == plan_rake.rake_number).first()
        if rake:
            rake.status = 'assigned'

        for order_data in plan_rake.orders_assigned:
            order = db.query(Order).filter(Order.id == order_data['order_id']).first()
            if order:
                order.status = 'assigned'

    db.commit()

    return {
        "message": "Plan committed successfully",
        "plan_id": plan_id,
        "committed_at": plan.committed_at.isoformat()
    }
