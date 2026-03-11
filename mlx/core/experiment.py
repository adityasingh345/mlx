# this will manage the experiments- the top level grouping for runs
# an experiment is just a named projects: like fraud_detection, image_classification etc
# every run belongs to one experiment 

from sqlmodel import select
from mlx.storage.db import get_session, Experiment

class ExperimentManager:
    # handles all the experiment operations
    @staticmethod
    def create(name:str, description: str = "") -> Experiment:
        # creates a new experiment if it already exists , return the existing one 
        with get_session() as session:
            # first we will check 
            existing = session.exec(select(Experiment).where(Experiment.name == name )).first()
            
            if existing:
                return existing
            
            experiment = Experiment(name= name, description=description)
            
            session.add(experiment)
            session.commit()
            
            # refresh() reloads the object from db 
            session.refresh(experiment)
            return experiment
    
    @staticmethod
    def get(name: str ) -> Experiment | None :
        # find an experiment 
        with get_session() as session:
            return session.exec(select(Experiment).where(Experiment.name == name)).first()
    
    @staticmethod
    def get_all() -> list[Experiment]:
        with get_session() as session:
            return session.exec(select(Experiment).order_by(Experiment.id.desc())).all()
        
    @staticmethod
    def exists(name: str) -> bool:
        # wheather the experiment exists or not 
        return ExperimentManager.get(name) is not None    