# the most important file, manages the start -> running -> stop 
# every run has unique id, a status runnning, done or failed , params and metrics atteched to it , and a log file for everything 

from sqlmodel import select
import datetime
from mlx.storage.db import Run, get_session
from mlx.storage.filesystem import (save_active_run,clear_active_run, get_active_run, append_log)

class RunManager:
    
    @staticmethod
    def make_run_id(name: str) -> str:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        slug = name.lower().replace(" ", "-")[:30]
        
        return f"{slug}_{ts}"
    
    @staticmethod
    def start(name: str, experiment: str = "default", tags: str = "") -> Run:
        # it will start a new run command will be mlx run start
        # checks that no other run should be active , save the runs to database, saves run_id to config toml as active run
        
        active = get_active_run()
        if active:
            raise RuntimeError(
                f"Run '{active}' is already active. \n"
                f"stop it first with: mlx run stop"
            )
        
        run_id = RunManager.make_run_id(name)
        
        #save to database
        with get_session() as session:
            run = Run(
                run_id = run_id,
                name=name,
                experiment=experiment,
                status= "running",
                tags = tags
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            
        save_active_run(run_id)
        
        append_log(run_id, f"run started: {name}")
        if tags:
            append_log(run_id, f"tags: {tags}")
            
        return run
    
    @staticmethod
    def stop(status: str = "done", run_id: str = None) -> Run:
        #stop the active run by mlx run stop 
        rid = run_id or get_active_run()
        if not rid:
            raise RuntimeError(
                "No active run found.\n"
                "Start one with: mlx run start --name 'my-run'"
            )

        now = datetime.datetime.utcnow()

        with get_session() as session:

            # Fetch the run from database
            run = session.exec(
                select(Run).where(Run.run_id == rid)
            ).first()

            if not run:
                raise RuntimeError(f"Run '{rid}' not found in database.")

            # Calculate duration
            created = datetime.datetime.fromisoformat(run.created_at)
            duration = (now - created).total_seconds()

            # Update the run row
            run.status = status
            run.finished_at = now.isoformat()
            run.duration_sec = round(duration, 2)

            session.add(run)
            session.commit()
            session.refresh(run)

        # Remove from config.toml — no longer active
        clear_active_run()

        # Write final log entry
        append_log(rid, f"Run stopped. Status: {status}")

        return run 
    
    @staticmethod
    def get(run_id: str) -> Run | None:
        with get_session() as session:
            return session.exec(select(Run).where(Run.run_id == run_id)).first()
        
    @staticmethod
    def get_all(
        experiment: str = None,
        status: str = None,
        limit: int = 50,
    ) -> list[Run]:
        with get_session() as session:
            query = select(Run).order_by(Run.id.desc()).limit(limit)
            runs = session.exec(query).all()
            
        if experiment:
            runs = [r for r in runs if r.experiment == experiment]
        if status:
            runs = [r for r in runs if r.status == status]

        return runs   
         
    @staticmethod
    def get_active() -> Run | None:
        """
        Return the currently active run object.
        Returns None if no run is active.
        """
        rid = get_active_run()
        if not rid:
            return None
        return RunManager.get(rid)

    @staticmethod
    def delete(run_id: str):
        """
        Delete a run and all its metrics and params.

        Used by: `mlx run delete` (we'll build this later)
        """
        from mlx.storage.db import Metric, Param

        with get_session() as session:

            # Delete metrics
            metrics = session.exec(
                select(Metric).where(Metric.run_id == run_id)
            ).all()
            for m in metrics:
                session.delete(m)

            # Delete params
            params = session.exec(
                select(Param).where(Param.run_id == run_id)
            ).all()
            for p in params:
                session.delete(p)

            # Delete the run itself
            run = session.exec(
                select(Run).where(Run.run_id == run_id)
            ).first()
            if run:
                session.delete(run)

            session.commit()