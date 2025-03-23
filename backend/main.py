
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
import uuid

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data.json"

class CargoItem(BaseModel):
    name: str
    weight: float
    length: float
    width: float
    height: float
    position: float
    cargoType: str
    isHazmat: bool

class Personnel(BaseModel):
    name: str
    weight: float
    position: float

class LoadPlan(BaseModel):
    user: str
    aircraft: str
    cargo: List[CargoItem]
    personnel: List[Personnel]
    id: str = ""

def read_data():
    if not os.path.exists(DATA_FILE):
        return {"plans": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.get("/aircraft")
def get_aircraft():
    return [
        {"name": "C-130J", "max_weight": 46700, "cg_limits": [15, 35]},
        {"name": "C-17", "max_weight": 170900, "cg_limits": [25, 45]},
        {"name": "C-5", "max_weight": 281001, "cg_limits": [30, 60]}
    ]

@app.post("/save")
def save_plan(plan: LoadPlan):
    data = read_data()
    plan.id = str(uuid.uuid4())
    data["plans"].append(plan.dict())
    write_data(data)
    return {"status": "saved", "id": plan.id}

@app.get("/plans/{user}")
def get_user_plans(user: str):
    data = read_data()
    return [p for p in data["plans"] if p["user"] == user]

@app.get("/plan/{plan_id}")
def get_plan_by_id(plan_id: str):
    data = read_data()
    for p in data["plans"]:
        if p["id"] == plan_id:
            return p
    raise HTTPException(404, "Plan not found")

@app.post("/check-cg")
def check_cg(plan: LoadPlan):
    aircrafts = {a["name"]: a for a in get_aircraft()}
    aircraft = aircrafts.get(plan.aircraft)
    if not aircraft:
        raise HTTPException(400, "Aircraft not found")
    
    total_weight = sum([c.weight for c in plan.cargo]) + sum([p.weight for p in plan.personnel])
    moment = sum([c.weight * c.position for c in plan.cargo]) + sum([p.weight * p.position for p in plan.personnel])
    cg = moment / total_weight if total_weight > 0 else 0
    limits = aircraft["cg_limits"]
    within_limits = limits[0] <= cg <= limits[1]

    return {
        "cg": cg,
        "within_limits": within_limits,
        "limits": limits,
        "moment": moment,
        "total_weight": total_weight,
        "points": [{"x": c.position, "y": c.weight} for c in plan.cargo + plan.personnel]
    }
