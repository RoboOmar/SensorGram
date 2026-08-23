from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import random
from sqlalchemy import or_

from backend.database import get_db
from backend.models.robot import Robot
from backend.routers.auth import get_current_robot, _robot_out, get_optional_robot
from backend.schemas.robot import RobotOut

router = APIRouter(prefix="/api/robots", tags=["robots"])


@router.get("", response_model=list[RobotOut])
def list_robots(
    skip: int = 0,
    limit: int = 30,
    current: Robot | None = Depends(get_optional_robot),
    db: Session = Depends(get_db)
):
    robots = db.query(Robot).offset(skip).limit(limit).all()
    return [_robot_out(r, current) for r in robots]


@router.get("/search", response_model=list[RobotOut])
def search_robots(
    q: str,
    current: Robot | None = Depends(get_optional_robot),
    db: Session = Depends(get_db)
):
    if not q:
        return []
    robots = db.query(Robot).filter(
        or_(
            Robot.username.ilike(f"%{q}%"),
            Robot.display_name.ilike(f"%{q}%")
        )
    ).limit(10).all()
    return [_robot_out(r, current) for r in robots]


@router.get("/suggested", response_model=list[RobotOut])
def suggested_robots(
    current: Robot | None = Depends(get_optional_robot),
    db: Session = Depends(get_db)
):
    if current:
        followed_ids = [f.id for f in current.followed]
        followed_ids.append(current.id)
        candidates = db.query(Robot).filter(~Robot.id.in_(followed_ids)).all()
    else:
        candidates = db.query(Robot).all()
    
    selected = random.sample(candidates, min(5, len(candidates)))
    return [_robot_out(r, current) for r in selected]


@router.get("/{username}", response_model=RobotOut)
def get_robot(
    username: str,
    current: Robot | None = Depends(get_optional_robot),
    db: Session = Depends(get_db)
):
    robot = db.query(Robot).filter(Robot.username == username).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return _robot_out(robot, current)


@router.post("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow(
    username: str,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    target = db.query(Robot).filter(Robot.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="Robot not found")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    if target not in current.followed:
        try:
            current.followed.append(target)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error during follow.")


@router.delete("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(
    username: str,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    target = db.query(Robot).filter(Robot.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="Robot not found")
    if target in current.followed:
        try:
            current.followed.remove(target)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error during unfollow.")
