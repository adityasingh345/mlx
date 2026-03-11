#handles logging and reading metrices 

from sqlmodel import select 
from mlx.storage.db import Metric, get_session
from mlx.storage.filesystem import get_active_run, append_log

class MetricManager:
    @staticmethod
    def log(
        key:str,
        value: float,
        step: int = 0,
        run_id: str = None,
    ) -> Metric:
        #Every call creates a NEW row — metrics build up over time. This is different from params which UPDATE the existing row.
        # Args:
        #     key:    metric name  → "accuracy", "loss", "auc"
        #     value:  the number   → 0.94
        #     step:   which step   → 100
        #     run_id: which run    → defaults to active run
        
        #find the active run 
        rid = run_id or get_active_run()
        if not rid:
            raise RuntimeError(
                "No active run.\n"
                "Start one with: mlx run start --name 'my-run'"
            )
        
        try: 
            float(value)
        except(TypeError, ValueError):
            raise ValueError(
                 f"Metric value must be a number. Got: '{value}'"
            )
            
        #save to database
        with get_session() as session:
            metric = Metric(
                run_id = rid,
                key = key,
                value = float(value),
                step=step,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            
        append_log(rid, f"metric | {key} = {value} @ step {step}")
        
        return metric 
    
    @staticmethod
    def log_many( metrics: dict, step: int = 0, run_id: str = None):
        for key, value in metrics.items():
            MetricManager.log(key, value, step=step, run_id=run_id)
            
    @staticmethod
    def get_for_run(run_id: str) -> list[Metric]:
        """
        Get ALL metric rows for a run — full history included.

        Returns them ordered by step so you can read them
        like a timeline from start to finish.

        Usage:
            metrics = MetricManager.get_for_run("catboost-v1_143201")
        """
        with get_session() as session:
            return session.exec(
                select(Metric)
                .where(Metric.run_id == run_id)
                .order_by(Metric.step)
            ).all()
            
    @staticmethod
    def get_latest(run_id: str) -> list[Metric]:
        """
        Get only the FINAL value for each metric key.

        Why is this useful?
        A run might log 'accuracy' 10 times (steps 100 to 1000).
        When displaying a run summary you only want the final value.

        How it works:
            All metrics:
                accuracy @ 100 = 0.81
                accuracy @ 200 = 0.88
                accuracy @ 300 = 0.94   ← keep this one
                loss     @ 100 = 0.42
                loss     @ 200 = 0.31
                loss     @ 300 = 0.21   ← keep this one

            Result:
                accuracy = 0.94
                loss     = 0.21
        """
        all_metrics = MetricManager.get_for_run(run_id)

        # Dict to track the highest-step metric per key
        # key → metric object with the highest step seen so far
        latest = {}

        for m in all_metrics:
            if m.key not in latest:
                # First time seeing this key — store it
                latest[m.key] = m
            elif m.step > latest[m.key].step:
                # Higher step found — replace the stored one
                latest[m.key] = m

        # Return as a list sorted alphabetically by key name
        return sorted(latest.values(), key=lambda m: m.key)
    
    @staticmethod
    def get_history(run_id: str, key: str) -> list[Metric]:

        with get_session() as session:
            return session.exec(
                select(Metric)
                .where(Metric.run_id == run_id)
                .where(Metric.key == key)
                .order_by(Metric.step)
            ).all()

    @staticmethod
    def get_keys(run_id: str) -> list[str]:
        
        all_metrics = MetricManager.get_for_run(run_id)

        # Use a set to remove duplicates then sort alphabetically
        seen = set()
        keys = []
        for m in all_metrics:
            if m.key not in seen:
                seen.add(m.key)
                keys.append(m.key)

        return sorted(keys)
    
    @staticmethod
    def compare(run_ids: list[str]) -> dict:
        result = {}

        for rid in run_ids:
            latest = MetricManager.get_latest(rid)
            result[rid] = {m.key: m.value for m in latest}

        return result
