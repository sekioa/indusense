"""Pipeline ML bout en bout : baseline -> [Optuna borné + CodeCarbon] -> évaluation -> SHAP -> arbitrage.

Orchestre les briques de ``indusense.fault`` en une seule commande ; aucune logique métier ne vit ici.

    uv run python scripts/run_fault_pipeline.py --horizon 24 --tune --n-trials 40
"""

import argparse
import json
import logging
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
for _logger_name in ("mlflow", "mlflow.sklearn", "mlflow.utils.environment", "mlflow.utils.uv_utils"):
    logging.getLogger(_logger_name).setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=r"Hint: Inferred schema contains integer column.*",
                        category=UserWarning, module=r"mlflow\.types\.utils")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import shap

from indusense.fault import carbon, data, evaluate, explain, model, train, tune

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "fault"
MLFLOW_STORE = ROOT / ".mlflow"
MLFLOW_EXPERIMENT = "indusense-fault-pipeline"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--horizon", type=int, choices=(6, 12, 24, 48), default=24,
                        help="Horizon de prédiction en heures (def. 24).")
    parser.add_argument("--tune", action="store_true", help="Lancer une étude Optuna après la baseline.")
    parser.add_argument("--n-trials", type=int, default=40, help="Budget d'essais Optuna (def. 40).")
    parser.add_argument("--timeout", type=float, default=1800.0,
                        help="Budget de temps en secondes pour l'étude Optuna (def. 1800).")
    parser.add_argument("--n-folds", type=int, default=3, help="Nombre de folds de CV temporelle (def. 3).")
    parser.add_argument("--seed", type=int, default=42, help="Graine de reproductibilité (def. 42).")
    parser.add_argument("--no-mlflow", action="store_true", help="Désactiver la journalisation MLflow.")
    parser.add_argument("--data-path", type=Path, default=data.DEFAULT_DATA_PATH,
                        help="Chemin du Gold dataset CSV.")
    return parser.parse_args(argv)


def setup_mlflow(run_name: str):
    """Configure le tracking SQLite et retourne un run parent, ou ``None`` si désactivé."""
    import mlflow

    MLFLOW_STORE.mkdir(exist_ok=True)
    artifacts_dir = MLFLOW_STORE / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + (MLFLOW_STORE / "mlflow.db").as_posix())
    if mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT) is None:
        mlflow.create_experiment(MLFLOW_EXPERIMENT, artifact_location=artifacts_dir.as_uri())
    mlflow.set_experiment(MLFLOW_EXPERIMENT)
    return mlflow.start_run(run_name=run_name)


def nested_run(mlflow_enabled: bool, *, run_name: str, parent_run_id: str | None):
    if not mlflow_enabled:
        return None
    import mlflow

    return mlflow.start_run(run_name=run_name, parent_run_id=parent_run_id, nested=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mlflow_enabled = not args.no_mlflow
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"fault-pipeline-h{args.horizon}-{timestamp}"
    run_dir = OUTPUT_DIR / run_name
    figures_dir = run_dir / "figures"

    print(f"[1/6] Chargement du Gold dataset et split temporel (horizon={args.horizon}h)...")
    gold = data.load_gold(args.data_path)
    split = data.temporal_split(gold, horizon=args.horizon)
    folds = data.build_cv_folds(split, n_folds=args.n_folds)
    print(f"      {len(split.features)} features, {len(split.X['train'])} lignes de train, "
          f"{len(folds.folds)} folds.")

    parent_run = setup_mlflow(run_name) if mlflow_enabled else None
    parent_run_id = None
    if parent_run is not None:
        parent_run.__enter__()
        parent_run_id = parent_run.info.run_id
        import mlflow

        mlflow.log_params({
            "horizon": args.horizon, "n_folds": args.n_folds, "seed": args.seed,
            "tune": args.tune, "n_trials": args.n_trials if args.tune else 0,
        })
        mlflow.log_dict({"features": split.features, "fold_metadata": folds.metadata}, "protocole.json")

    try:
        print("[2/6] Entraînement de la baseline (+ CodeCarbon)...")
        summary_csv = OUTPUT_DIR / "emissions_summary.csv"

        def fit_baseline():
            return train.fit_and_log(
                model.BASELINE_PARAMS, split.X["train"], split.y["train"], folds,
                role="reference", seed=args.seed,
                mlflow_run=nested_run(mlflow_enabled, run_name=f"{run_name}-baseline", parent_run_id=parent_run_id),
            )

        baseline_result, baseline_carbon = carbon.track_step(
            fit_baseline, step="baseline", output_dir=run_dir, project_name="indusense-fault",
        )
        carbon.append_summary_row(summary_csv, baseline_carbon, run_name=run_name, metric_name="cv_ap",
                                   metric_value=baseline_result.cv_result.cv_ap)
        print(f"      Baseline cv_ap={baseline_result.cv_result.cv_ap:.4f} "
              f"({baseline_carbon.emissions_kg * 1000:.3f} gCO2eq, {baseline_carbon.duration_seconds:.1f}s).")

        best_result = baseline_result
        best_label = "baseline"
        study = None
        if args.tune:
            print(f"[3/6] Étude Optuna bornée (n_trials={args.n_trials}, timeout={args.timeout}s, pruning)...")

            def on_trial_complete(trial, sampled, decoded_params, val_scores, train_scores):
                cv_result = evaluate.CrossValidationResult(
                    fold_scores=val_scores, fold_train_scores=train_scores,
                    cv_ap=sum(val_scores) / len(val_scores),
                    cv_std=float(pd.Series(val_scores).std(ddof=0)),
                    train_ap=sum(train_scores) / len(train_scores),
                    gap_ap=sum(train_scores) / len(train_scores) - sum(val_scores) / len(val_scores),
                )
                train.log_cv_result(
                    cv_result, sampled, role="optuna_trial",
                    mlflow_run=nested_run(mlflow_enabled, run_name=f"{run_name}-trial-{trial.number:03d}",
                                           parent_run_id=parent_run_id),
                    tags={"trial_number": str(trial.number)},
                )

            objective = tune.make_objective(
                split.X["train"], split.y["train"], folds, seed=args.seed,
                on_trial_complete=on_trial_complete if mlflow_enabled else None,
            )

            def run_optuna_study():
                return tune.run_study(
                    objective,
                    budget=tune.StudyBudget(n_trials=args.n_trials, timeout=args.timeout),
                    seed=args.seed, study_name=run_name,
                )

            study, study_carbon = carbon.track_step(
                run_optuna_study, step="optuna_study", output_dir=run_dir, project_name="indusense-fault",
            )
            completed = [t for t in study.trials if t.state.name == "COMPLETE"]
            pruned = [t for t in study.trials if t.state.name == "PRUNED"]
            print(f"      {len(completed)} essais complets, {len(pruned)} élagués (pruning), "
                  f"meilleur AP CV={study.best_value:.4f} "
                  f"({study_carbon.emissions_kg * 1000:.3f} gCO2eq, {study_carbon.duration_seconds:.1f}s).")
            carbon.append_summary_row(summary_csv, study_carbon, run_name=run_name, metric_name="cv_ap",
                                       metric_value=study.best_value)

            if study.best_value > baseline_result.cv_result.cv_ap:
                decoded_best = model.decode_params(study.best_params)
                tuned_result = train.fit_and_log(
                    decoded_best, split.X["train"], split.y["train"], folds,
                    role="tuned", seed=args.seed,
                    logged_params=study.best_params,
                    mlflow_run=nested_run(mlflow_enabled, run_name=f"{run_name}-tuned", parent_run_id=parent_run_id),
                )
                best_result, best_label = tuned_result, "tuned"
                print(f"      Optuna améliore la baseline : cv_ap "
                      f"{baseline_result.cv_result.cv_ap:.4f} -> {tuned_result.cv_result.cv_ap:.4f}.")
            else:
                print("      Aucun essai Optuna ne bat la baseline : la baseline reste retenue.")
        else:
            print("[3/6] Étude Optuna ignorée (--tune non passé).")

        print("[4/6] Évaluation sur validation/test (seuil F2)...")
        val_scores = best_result.model.predict_proba(split.X["validation"])[:, 1]
        threshold = evaluate.choose_threshold(split.y["validation"], val_scores)
        validation_metrics = evaluate.evaluate_at_threshold(split.y["validation"], val_scores, threshold)
        test_scores = best_result.model.predict_proba(split.X["test"])[:, 1]
        test_metrics = evaluate.evaluate_at_threshold(split.y["test"], test_scores, threshold)
        print(f"      [{best_label}] validation F2={validation_metrics.F2:.4f} ; "
              f"test AP={test_metrics.AP:.4f} F2={test_metrics.F2:.4f}.")

        print("[5/6] Explicabilité SHAP (summary, waterfall, dependence)...")
        figures_dir.mkdir(parents=True, exist_ok=True)
        X_val_sample = split.X["validation"].sample(
            n=min(500, len(split.X["validation"])), random_state=args.seed,
        )
        explanation = explain.build_explanation(best_result.model, X_val_sample)
        top = explain.top_features(explanation, n=10)
        top.to_csv(run_dir / "shap_top_features.csv", index=False)

        shap.plots.beeswarm(explanation, show=False)
        plt.gcf().savefig(figures_dir / "shap_summary.png", bbox_inches="tight", dpi=150)
        plt.close("all")

        sample_scores = best_result.model.predict_proba(X_val_sample)[:, 1]
        flagged = explain.pick_flagged_instance(sample_scores, X_val_sample, threshold=threshold)
        shap.plots.waterfall(explanation[flagged.position], show=False)
        plt.gcf().savefig(figures_dir / "shap_waterfall.png", bbox_inches="tight", dpi=150)
        plt.close("all")

        for feature in explain.dependence_pairs(top, n=3):
            shap.plots.scatter(explanation[:, feature], show=False)
            plt.gcf().savefig(figures_dir / f"shap_dependence_{feature}.png", bbox_inches="tight", dpi=150)
            plt.close("all")
        print(f"      Figures SHAP enregistrées dans {figures_dir}.")

        print("[6/6] Tableau d'arbitrage et sauvegarde des artefacts...")
        arbitration = evaluate.arbitration_table([{
            "modele": best_label,
            "pr_auc": test_metrics.AP,
            "gco2eq": (baseline_carbon.emissions_kg + (study_carbon.emissions_kg if args.tune else 0.0)) * 1000,
            "interpretabilite": f"SHAP top-1 = {top.iloc[0]['feature']} ({top.iloc[0]['impact']:.4f})",
            "decision": "retenu" if best_label == "tuned" else "baseline conservée (Optuna sans gain net)",
        }])
        arbitration.to_csv(run_dir / "arbitration_table.csv", index=False)

        summary = {
            "run_name": run_name, "horizon": args.horizon, "best_label": best_label,
            "baseline_cv_ap": baseline_result.cv_result.cv_ap,
            "best_cv_ap": best_result.cv_result.cv_ap,
            "validation_metrics": validation_metrics.as_dict(),
            "test_metrics": test_metrics.as_dict(),
            "threshold": threshold,
            "top_features": top.to_dict("records"),
        }
        (run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
        )
        print(f"      Artefacts écrits dans {run_dir}.")
        return 0
    finally:
        if parent_run is not None:
            parent_run.__exit__(None, None, None)


if __name__ == "__main__":
    raise SystemExit(main())
