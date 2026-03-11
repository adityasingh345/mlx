"""
Examples:
    learning_rate = 0.05
    depth         = 6
    iterations    = 500
    optimizer     = "adam"
    batch_size    = 32
"""

from sqlmodel import select
from mlx.storage.db import get_session, Param
from mlx.storage.filesystem import get_active_run, append_log


class ParamManager:
    """
    Handles all param operations.

    Key difference from MetricManager:
        Metrics  → always CREATE a new row (full history kept)
        Params   → CREATE or UPDATE (no duplicates, last value wins)

    Why? You never need the history of a param.
    If you log learning_rate=0.05 then log learning_rate=0.01,
    you just want the final value: 0.01.
    """

    @staticmethod
    def log(
        key: str,
        value,
        run_id: str = None,
    ) -> Param:
        """
        Args:
            key:    param name  → "learning_rate", "depth"
            value:  any value   → 0.05, 6, "adam", True
                                  always stored as string in DB
            run_id: which run   → defaults to active run
        """

        rid = run_id or get_active_run()
        if not rid:
            raise RuntimeError(
                "No active run.\n"
                "Start one with: mlx run start --name 'my-run'"
            )

        # Always convert to string for consistent storage
        # Handles int, float, bool, list, anything
        str_value = str(value)

        with get_session() as session:

            # Check if this param already exists for this run
            existing = session.exec(
                select(Param)
                .where(Param.run_id == rid)
                .where(Param.key == key)
            ).first()

            if existing:
                # UPDATE — change the value in place
                existing.value = str_value
                session.add(existing)
                session.commit()
                session.refresh(existing)
                param = existing
            else:
                # CREATE — brand new row
                param = Param(
                    run_id=rid,
                    key=key,
                    value=str_value,
                )
                session.add(param)
                session.commit()
                session.refresh(param)

        # Write to log file
        append_log(rid, f"param  | {key} = {str_value}")

        return param


    @staticmethod
    def log_many(params: dict, run_id: str = None):
        """
        Log multiple params at once from a dictionary.
        The most convenient way to log all your settings.

        Usage:
            ParamManager.log_many({
                "learning_rate": 0.05,
                "depth":         6,
                "iterations":    500,
                "loss_function": "Logloss",
                "eval_metric":   "AUC",
            })
        """
        for key, value in params.items():
            ParamManager.log(key, value, run_id=run_id)


    @staticmethod
    def get_for_run(run_id: str) -> list[Param]:
        """
        Get all params for a run, sorted alphabetically.

        Usage:
            params = ParamManager.get_for_run("catboost-v1_143201")
        """
        with get_session() as session:
            return session.exec(
                select(Param)
                .where(Param.run_id == run_id)
                .order_by(Param.key)
            ).all()


    @staticmethod
    def as_dict(run_id: str) -> dict:
        """
        Usage:
            params = ParamManager.as_dict("catboost-v1_143201")
            # → {"depth": "6", "learning_rate": "0.05", "iterations": "500"}

            # Access one value:
            lr = float(params["learning_rate"])   # cast back to float
        """
        params = ParamManager.get_for_run(run_id)
        return {p.key: p.value for p in params}


    @staticmethod
    def compare(run_ids: list[str]) -> dict:
        """
        Returns:
            {
                "catboost-v1_001": {"learning_rate": "0.05", "depth": "6"},
                "catboost-v2_002": {"learning_rate": "0.01", "depth": "8"},
            }

        Usage:
            data = ParamManager.compare(["catboost-v1_001", "catboost-v2_002"])
        """
        result = {}
        for rid in run_ids:
            result[rid] = ParamManager.as_dict(rid)
        return result