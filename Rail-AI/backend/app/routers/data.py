from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd
import io
import json
from datetime import datetime
from ..database import get_db
from ..models import *

router = APIRouter(prefix="/api", tags=["data"])

DATASET_MODELS = {
    'stockyards': Stockyard,
    'orders': Order,
    'rakes': Rake,
    'loading_points': LoadingPoint,
    'products': Product,
    'wagon_types': WagonType
}

TEMPLATES = {
    'stockyards': {
        'headers': ['code', 'name', 'location', 'latitude', 'longitude', 'capacity_tonnes', 'current_inventory_json'],
        'example': ['SY001', 'Bokaro Stockyard', 'Bokaro, Jharkhand', 23.6693, 85.9630, 50000, '{"COAL": 25000, "IRON_ORE": 15000}']
    },
    'orders': {
        'headers': ['order_number', 'product_code', 'quantity_tonnes', 'source_stockyard_code', 'destination', 'destination_latitude', 'destination_longitude', 'priority', 'due_date', 'sla_hours'],
        'example': ['ORD001', 'COAL', 2500, 'SY001', 'Mumbai Port', 19.0760, 72.8777, 1, '2025-10-15', 72]
    },
    'rakes': {
        'headers': ['rake_number', 'wagon_type_code', 'num_wagons', 'total_capacity_tonnes', 'status', 'current_location', 'availability_date'],
        'example': ['RK001', 'BOXN', 58, 3480, 'available', 'Bokaro', '2025-10-09']
    },
    'loading_points': {
        'headers': ['code', 'name', 'stockyard_code', 'location', 'latitude', 'longitude', 'sidings', 'max_rake_length', 'products_handled_json'],
        'example': ['LP001', 'Bokaro Loading Point 1', 'SY001', 'Bokaro', 23.6693, 85.9630, 3, 58, '["COAL", "IRON_ORE"]']
    },
    'products': {
        'headers': ['code', 'name', 'density', 'handling_time'],
        'example': ['COAL', 'Coal', 1.4, 2.5]
    },
    'wagon_types': {
        'headers': ['code', 'name', 'capacity_tonnes', 'capacity_volume', 'tare_weight'],
        'example': ['BOXN', 'BOXN Wagon', 60, 50, 22]
    }
}

@router.get("/template/{dataset}")
async def get_template(dataset: str):
    """Return CSV template for a dataset."""
    if dataset not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template for {dataset} not found")

    template = TEMPLATES[dataset]
    df = pd.DataFrame([template['example']], columns=template['headers'])

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset}_template.csv"}
    )

@router.post("/upload/{dataset}")
async def upload_dataset(dataset: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse CSV data for a dataset."""
    if dataset not in DATASET_MODELS:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        df = df.where(pd.notnull(df), None)

        model = DATASET_MODELS[dataset]

        records_created = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                record_data = row.to_dict()

                if dataset == 'stockyards' and 'current_inventory_json' in record_data:
                    inv_str = record_data.pop('current_inventory_json', '{}')
                    if inv_str and inv_str != 'None':
                        record_data['current_inventory'] = json.loads(inv_str) if isinstance(inv_str, str) else inv_str

                if dataset == 'loading_points' and 'products_handled_json' in record_data:
                    ph_str = record_data.pop('products_handled_json', '[]')
                    if ph_str and ph_str != 'None':
                        record_data['products_handled'] = json.loads(ph_str) if isinstance(ph_str, str) else ph_str

                if dataset == 'orders' and 'source_stockyard_code' in record_data:
                    code = record_data.pop('source_stockyard_code', None)
                    if code:
                        sy = db.query(Stockyard).filter(Stockyard.code == code).first()
                        record_data['source_stockyard_id'] = sy.id if sy else None

                if dataset == 'loading_points' and 'stockyard_code' in record_data:
                    code = record_data.pop('stockyard_code', None)
                    if code:
                        sy = db.query(Stockyard).filter(Stockyard.code == code).first()
                        record_data['stockyard_id'] = sy.id if sy else None

                clean_data = {k: v for k, v in record_data.items() if v is not None and str(v) != 'nan'}

                existing = None
                if hasattr(model, 'code'):
                    existing = db.query(model).filter(model.code == clean_data.get('code')).first()
                elif hasattr(model, 'order_number'):
                    existing = db.query(model).filter(model.order_number == clean_data.get('order_number')).first()
                elif hasattr(model, 'rake_number'):
                    existing = db.query(model).filter(model.rake_number == clean_data.get('rake_number')).first()

                if existing:
                    for key, value in clean_data.items():
                        setattr(existing, key, value)
                else:
                    record = model(**clean_data)
                    db.add(record)

                records_created += 1

            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")

        db.commit()

        return {
            "message": f"Successfully processed {records_created} records for {dataset}",
            "records_created": records_created,
            "errors": errors[:10] if errors else []
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@router.get("/{dataset}")
async def get_dataset(dataset: str, skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """Fetch dataset rows with pagination."""
    if dataset not in DATASET_MODELS:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")

    model = DATASET_MODELS[dataset]
    records = db.query(model).offset(skip).limit(limit).all()

    result = []
    for record in records:
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}

        for key, value in record_dict.items():
            if isinstance(value, datetime):
                record_dict[key] = value.isoformat()

        result.append(record_dict)

    return {"data": result, "count": len(result)}

@router.put("/{dataset}/{id}")
async def update_record(dataset: str, id: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    """Update a single record."""
    if dataset not in DATASET_MODELS:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")

    model = DATASET_MODELS[dataset]
    record = db.query(model).filter(model.id == id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for key, value in data.items():
        if hasattr(record, key):
            setattr(record, key, value)

    db.commit()
    db.refresh(record)

    return {"message": "Record updated successfully"}

@router.delete("/{dataset}/{id}")
async def delete_record(dataset: str, id: str, db: Session = Depends(get_db)):
    """Delete a single record."""
    if dataset not in DATASET_MODELS:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")

    model = DATASET_MODELS[dataset]
    record = db.query(model).filter(model.id == id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully"}
