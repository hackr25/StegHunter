"""
StegHunter CLI — Advanced Steganography Detection Tool.

Usage examples
--------------
  python steg_hunter_cli.py info image.png
  python steg_hunter_cli.py analyze image.png
  python steg_hunter_cli.py analyze images/ --batch --recursive -o results.json
  python steg_hunter_cli.py analyze image.png --use-ml
  python steg_hunter_cli.py heatmap image.png --output heatmap.png
  python steg_hunter_cli.py train-model --clean-dir clean/ --stego-dir stego/
  python steg_hunter_cli.py predict image.png
"""
from __future__ import annotations

import json
from pathlib import Path

import click
from tqdm import tqdm

from src.common.utils import collect_image_files, convert_numpy_types, save_results_json, save_results_csv
from src.common.exceptions import InvalidImageError, ConfigError, AnalysisError
from src.core.analyzer import SteganographyAnalyzer


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """StegHunter — Advanced Steganography Detection Tool."""


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
def info(image_path: str):
    """Display basic metadata for IMAGE_PATH."""
    from src.common.image_utils import get_image_info
    try:
        data = get_image_info(image_path)
        click.echo(f"Image Analysis: {image_path}")
        click.echo("-" * 50)
        for key, value in data.items():
            click.echo(f"{key}: {value}")
    except InvalidImageError as e:
        click.echo(f"Error: Invalid image - {e}", err=True)
        raise SystemExit(1)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (JSON or CSV).")
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv"]), default="json", show_default=True,
    help="Output format.",
)
@click.option("--batch", "-b", is_flag=True, help="Batch-process a directory.")
@click.option("--recursive", "-r", is_flag=True, help="Recurse into sub-directories.")
@click.option("--verbose", "-v", is_flag=True, help="Print full JSON results.")
@click.option(
    "--threshold", "-t", type=float, default=50.0, show_default=True,
    help="Suspicion score threshold for HIGH/LOW classification.",
)
@click.option("--use-ml", is_flag=True, help="Use the trained ML model.")
@click.option(
    "--model", "-m",
    type=click.Path(), default="models/steg_model.pkl", show_default=True,
    help="Path to ML model.",
)
@click.option("--ela", is_flag=True, help="Run ELA and save heatmap alongside results.")
@click.option("--ghost", is_flag=True, help="Run JPEG Ghost analysis (JPEG files only).")
@click.option("--forensics", "run_forensics", is_flag=True,
              help="Run full forensic scan (format, structure, metadata).")

def analyze(target, output, format, batch, recursive, verbose, threshold, use_ml, model, ela, ghost, run_forensics):
    """Analyze TARGET (file or directory) for steganography."""
    try:
        analyzer = SteganographyAnalyzer()
    except ConfigError as e:
        click.echo(f"Error: Configuration failed - {e}", err=True)
        raise SystemExit(1)
    
    target_path = Path(target)

    if use_ml and not Path(model).exists():
        click.echo("Warning: ML model not found — falling back to heuristic analysis.")
        use_ml = False

    results_list: list[dict] = []

    if target_path.is_file():
        try:
            results_list.append(_analyze_single(target_path, analyzer, use_ml, model))
        except InvalidImageError as e:
            click.echo(f"Error: Invalid image - {e}", err=True)
            raise SystemExit(1)
        except AnalysisError as e:
            click.echo(f"Error: Analysis failed - {e}", err=True)
            raise SystemExit(1)
    else:
        if not batch:
            click.echo("Use --batch (-b) to process a directory.")
            return
        image_files = collect_image_files(target_path, recursive)
        if not image_files:
            click.echo("No supported image files found.")
            return
        for file_path in tqdm(image_files, desc="Analyzing"):
            try:
                results_list.append(_analyze_single(file_path, analyzer, use_ml, model))
            except InvalidImageError as e:
                if verbose:
                    click.echo(f"Skipped {file_path}: Invalid image - {e}")
            except AnalysisError as e:
                if verbose:
                    click.echo(f"Skipped {file_path}: {e}")
            except Exception as exc:
                if verbose:
                    click.echo(f"Error analyzing {file_path}: {exc}")

    _display_results(results_list, batch, verbose, threshold, use_ml, target_path)

    # ── Optional forensic analysis ──
    if (ela or ghost or run_forensics) and target_path.is_file():
        _run_forensic_extras(target_path, ela=ela, ghost=ghost,
                             run_forensics=run_forensics)

    if output:
        if format == "json":
            save_results_json(results_list, output)
            click.echo(f"Results saved to {output}")
        else:
            save_results_csv(results_list, output)
            click.echo(f"Results saved to {output}")


# ---------------------------------------------------------------------------
# heatmap
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.option("--output", "-o", type=click.Path(), help="Output heatmap path.")
@click.option(
    "--method", "-m",
    type=click.Choice(["lsb", "comprehensive", "ml"]), default="lsb", show_default=True,
    help="Heatmap generation method.",
)
@click.option(
    "--model",
    type=click.Path(), default="models/steg_model.pkl", show_default=True,
    help="ML model path (only used with --method ml).",
)
def heatmap(image_path: str, output, method: str, model: str):
    """Generate a visual heatmap of suspicious regions in IMAGE_PATH."""
    from src.core.heatmap_generator import HeatmapGenerator

    generator = HeatmapGenerator()
    click.echo(f"Generating {method} heatmap for {image_path}…")

    try:
        if method == "lsb":
            generator.generate_lsb_heatmap(image_path, output)
        elif method == "comprehensive":
            heatmaps = generator.generate_comprehensive_heatmap(image_path, output)
            click.echo(f"Generated {len(heatmaps)} heatmap(s).")
        elif method == "ml":
            if not Path(model).exists():
                click.echo("Error: ML model not found. Train a model first with 'train-model'.")
                return
            from src.core.ml_classifier import MLSteganalysisClassifier
            classifier = MLSteganalysisClassifier(model)
            generator.generate_ml_heatmap(image_path, classifier, output)

        msg = f"✅ Heatmap saved to {output}" if output else "✅ Heatmap generation complete."
        click.echo(msg)
    except Exception as exc:
        click.echo(f"Error: {exc}")


# ---------------------------------------------------------------------------
# train-model
# ---------------------------------------------------------------------------

@cli.command("train-model")
@click.option("--clean-dir", type=click.Path(exists=True), required=True, help="Directory of clean images.")
@click.option("--stego-dir", type=click.Path(exists=True), required=True, help="Directory of stego images.")
@click.option(
    "--output", "-o",
    type=click.Path(), default="models/steg_model.pkl", show_default=True,
    help="Output model path.",
)
@click.option("--test-size", type=float, default=0.2, show_default=True, help="Validation split ratio.")
@click.option("--verbose", "-v", is_flag=True, help="Show top-10 feature importances.")
def train_model(clean_dir, stego_dir, output, test_size, verbose):
    """Train the Random Forest ML model."""
    from src.core.ml_classifier import MLSteganalysisClassifier

    _SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    clean_images = [str(p) for p in Path(clean_dir).glob("*.*") if p.suffix.lower() in _SUPPORTED]
    stego_images = [str(p) for p in Path(stego_dir).glob("*.*") if p.suffix.lower() in _SUPPORTED]

    click.echo(f"Clean images : {len(clean_images)}")
    click.echo(f"Stego images : {len(stego_images)}")

    if not clean_images or not stego_images:
        click.echo("Error: need at least one image in each directory.")
        return

    try:
        classifier = MLSteganalysisClassifier()
        metrics = classifier.train_model(clean_images, stego_images, output, test_size)

        click.echo("\n" + "=" * 50)
        click.echo("Training Results")
        click.echo("=" * 50)
        click.echo(f"Accuracy  : {metrics['accuracy']:.4f}")
        click.echo(f"Precision : {metrics['precision']:.4f}")
        click.echo(f"Recall    : {metrics['recall']:.4f}")
        click.echo(f"F1-Score  : {metrics['f1_score']:.4f}")
        click.echo(f"CV Mean   : {metrics['cv_mean']:.4f} (±{metrics['cv_std']:.4f})")

        if verbose and "feature_importance" in metrics:
            click.echo("\nTop-10 Feature Importances:")
            top = sorted(metrics["feature_importance"].items(), key=lambda x: x[1], reverse=True)[:10]
            for feat, imp in top:
                click.echo(f"  {feat:<40s}: {imp:.4f}")

        click.echo(f"\n✅ Model saved to {output}")
    except Exception as exc:
        click.echo(f"Error during training: {exc}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------------
# predict
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.option(
    "--model", "-m",
    type=click.Path(), default="models/steg_model.pkl", show_default=True,
    help="Path to trained model.",
)
@click.option("--verbose", "-v", is_flag=True, help="Show extra prediction details.")
def predict(image_path: str, model: str, verbose: bool):
    """Run ML prediction on IMAGE_PATH."""
    from src.core.ml_classifier import MLSteganalysisClassifier

    if not Path(model).exists():
        click.echo(f"Error: model not found at {model}. Train one with 'train-model'.")
        return

    try:
        classifier = MLSteganalysisClassifier(model)
        result = classifier.predict(image_path)

        label = "STEGANOGRAPHY DETECTED" if result["prediction"] == 1 else "CLEAN IMAGE"
        click.echo(f"\nML Prediction — {image_path}")
        click.echo("-" * 50)
        click.echo(f"Prediction  : {label}")
        click.echo(f"Probability : {result['probability']:.4f}")
        click.echo(f"Confidence  : {result['confidence']:.4f}")

        if verbose and result.get("error"):
            click.echo(f"Note: {result['error']}")
    except Exception as exc:
        click.echo(f"Error: {exc}")


# ---------------------------------------------------------------------------
# forensics  (new top-level command)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--ela",   is_flag=True, help="Include ELA analysis.")
@click.option("--ghost", is_flag=True, help="Include JPEG Ghost analysis.")
@click.option("--save-pdf", type=click.Path(), default=None,
              help="Save a PDF report to this path.")
def forensics(image_path: str, ela: bool, ghost: bool, save_pdf: str):
    """Run full forensic analysis on IMAGE_PATH."""
    path = Path(image_path)
    click.echo(f"Forensic scan: {path.name}")
    click.echo("=" * 55)

    # Standard analysis first
    from src.core.analyzer import SteganographyAnalyzer
    analyzer = SteganographyAnalyzer()
    results = analyzer.analyze_image(path)
    score = results.get('final_suspicion_score', 0)
    status = "⚠️  HIGH SUSPICION" if score >= 50 else "✅ CLEAN"
    click.echo(f"  Steg Score    : {score:.1f}/100 — {status}")

    # All forensic extras
    _run_forensic_extras(path, ela=ela, ghost=ghost, run_forensics=True)

    if save_pdf:
        try:
            from src.core.pdf_reporter import PDFReporter
            reporter = PDFReporter()
            pdf = reporter.create_single_image_report(image_path, results,
                                                       output_path=save_pdf)
            click.echo(f"\n  PDF saved: {pdf}")
        except Exception as exc:
            click.echo(f"  PDF generation failed: {exc}")


# ---------------------------------------------------------------------------
# video-analyze  (Phase 4 — NEW)
# ---------------------------------------------------------------------------

@cli.command("video-analyze")
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output results file (JSON).")
@click.option("--heatmap", type=click.Path(), help="Output heatmap path (PNG).")
@click.option("--verbose", "-v", is_flag=True, help="Print detailed frame analysis.")
def video_analyze(video_path: str, output: str, heatmap: str, verbose: bool):
    """Analyze VIDEO_PATH for steganography using Phase 4 forensics.
    
    Performs:
    - Frame-by-frame LSB entropy analysis
    - Temporal anomaly detection (Z-score based)
    - Container format inspection (MP4/MKV)
    - Optional heatmap generation
    """
    try:
        analyzer = SteganographyAnalyzer()
    except Exception as e:
        click.echo(f"Error: Configuration failed - {e}", err=True)
        raise SystemExit(1)
    
    try:
        click.echo(f"🎬 Analyzing video: {Path(video_path).name}")
        click.echo("-" * 60)
        
        results = analyzer.analyze_video(video_path)
        
        # Display results
        click.echo(f"Frames analyzed    : {results['frame_count']}")
        click.echo(f"Overall score      : {results['overall_score']:.1f}/100")
        click.echo(f"Suspicious         : {'⚠️  YES' if results['is_suspicious'] else '✅ NO'}")
        click.echo(f"Analysis time      : {results['analysis_time']:.2f}s")
        
        if verbose:
            if "video_frame_analysis" in results["methods"]:
                frame_result = results["methods"]["video_frame_analysis"]
                if "anomalies" in frame_result:
                    click.echo(f"\nFrame anomalies found: {len(frame_result['anomalies'])}")
                    for idx, anom in frame_result['anomalies'][:5]:  # Show first 5
                        click.echo(f"  Frame {idx}: score {anom:.2f}")
        
        # Generate heatmap if requested
        if heatmap:
            try:
                from src.core.video_heatmap_generator import VideoHeatmapGenerator
                if "video_frame_analysis" in results["methods"]:
                    entropy_timeline = results["methods"]["video_frame_analysis"].get("entropy_timeline", [])
                    anomalies = results["methods"]["video_frame_analysis"].get("anomalies", [])
                    
                    gen = VideoHeatmapGenerator()
                    gen.generate(entropy_timeline, anomalies, heatmap)
                    click.echo(f"✅ Heatmap saved to {heatmap}")
            except Exception as e:
                click.echo(f"Warning: Heatmap generation failed - {e}")
        
        # Save results if requested
        if output:
            save_results_json([results], output)
            click.echo(f"✅ Results saved to {output}")
        
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file.")
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv"]), default="json", show_default=True,
)
@click.option("--recursive", "-r", is_flag=True)
def export(target, output, format, recursive):
    """Export analysis results for TARGET to a file."""
    analyzer = SteganographyAnalyzer()
    target_path = Path(target)

    if target_path.is_file():
        results = [analyzer.analyze_image(target_path)]
    else:
        image_files = collect_image_files(target_path, recursive)
        if not image_files:
            click.echo("No image files found.")
            return
        results = []
        for fp in tqdm(image_files, desc="Processing"):
            try:
                results.append(analyzer.analyze_image(fp))
            except Exception as exc:
                click.echo(f"Error: {fp}: {exc}")

    if format == "json":
        save_results_json(results, output)
    else:
        save_results_csv(results, output)
    click.echo(f"✅ Results exported to {output}")


# ---------------------------------------------------------------------------
# train-all-models (NEW - Multi-Model Training)
# ---------------------------------------------------------------------------

@cli.command("train-all-models")
@click.option("--clean-dir", type=click.Path(exists=True), required=True, help="Directory of clean images.")
@click.option("--stego-dir", type=click.Path(exists=True), required=True, help="Directory of stego images.")
@click.option("--test-size", type=float, default=0.2, show_default=True, help="Validation split ratio.")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed training metrics.")
def train_all_models(clean_dir, stego_dir, test_size, verbose):
    """Train XGBoost, SVM, and Ensemble ML models simultaneously."""
    from src.core.ml_multi_model_manager import MultiModelMLManager
    from src.core.ml_features import MLFeatureExtractor
    from sklearn.model_selection import train_test_split
    import numpy as np
    
    _SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    clean_images = [str(p) for p in Path(clean_dir).glob("*.*") if p.suffix.lower() in _SUPPORTED]
    stego_images = [str(p) for p in Path(stego_dir).glob("*.*") if p.suffix.lower() in _SUPPORTED]
    
    click.echo(f"Clean images : {len(clean_images)}")
    click.echo(f"Stego images : {len(stego_images)}")
    
    if not clean_images or not stego_images:
        click.echo("Error: need at least one image in each directory.")
        return
    
    try:
        click.echo("\n" + "="*60)
        click.echo("FEATURE EXTRACTION")
        click.echo("="*60 + "\n")
        
        # Extract features
        extractor = MLFeatureExtractor()
        X_clean = []
        X_stego = []
        
        for img_path in tqdm(clean_images, desc="Extracting clean features"):
            try:
                features = extractor.extract_features(img_path)
                X_clean.append(features)
            except Exception as e:
                if verbose:
                    click.echo(f"  Skipped {img_path}: {e}")
        
        for img_path in tqdm(stego_images, desc="Extracting stego features"):
            try:
                features = extractor.extract_features(img_path)
                X_stego.append(features)
            except Exception as e:
                if verbose:
                    click.echo(f"  Skipped {img_path}: {e}")
        
        if len(X_clean) < 2 or len(X_stego) < 2:
            click.echo("Error: Not enough valid images to train models.")
            return
        
        X = np.vstack([X_clean, X_stego])
        y = np.hstack([np.zeros(len(X_clean)), np.ones(len(X_stego))])
        
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=42)
        
        click.echo(f"\nTraining set: {len(X_train)} samples")
        click.echo(f"Validation set: {len(X_val)} samples")
        
        # Train all models
        manager = MultiModelMLManager(model_type='ensemble')
        results = manager.train_all_models(X_train, y_train, X_val, y_val)
        
        # Display results
        click.echo("\n" + "="*60)
        click.echo("TRAINING COMPLETE")
        click.echo("="*60 + "\n")
        
        for model_name, metrics in results.items():
            click.echo(f"📊 {model_name.upper()}")
            click.echo(f"   Accuracy   : {metrics.get('accuracy', 'N/A'):.4f}")
            click.echo(f"   Precision  : {metrics.get('precision', 'N/A'):.4f}")
            click.echo(f"   Recall     : {metrics.get('recall', 'N/A'):.4f}")
            click.echo(f"   F1-Score   : {metrics.get('f1', 'N/A'):.4f}")
            if 'val_f1' in metrics:
                click.echo(f"   Val F1     : {metrics['val_f1']:.4f}")
            click.echo()
        
        click.echo("✅ All models trained and saved!")
        click.echo("   • models/steg_model.pkl (Random Forest)")
        click.echo("   • models/steg_model_xgboost.pkl (XGBoost)")
        click.echo("   • models/steg_model_svm.pkl (SVM)")
        click.echo("   • models/steg_model_ensemble.pkl (Ensemble)")
        
    except Exception as exc:
        click.echo(f"Error during training: {exc}")
        if verbose:
            import traceback
            traceback.print_exc()


# ---------------------------------------------------------------------------
# analyze-all-models (NEW - Multi-Model Analysis)
# ---------------------------------------------------------------------------

@cli.command("analyze-all-models")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed predictions.")
def analyze_all_models(image_path: str, verbose: bool):
    """Analyze IMAGE_PATH with all ML models (RF, XGB, SVM, Ensemble)."""
    from src.core.ml_multi_model_manager import MultiModelMLManager
    from src.core.ml_features import MLFeatureExtractor
    import numpy as np
    
    try:
        click.echo(f"\n📊 Multi-Model Analysis: {Path(image_path).name}")
        click.echo("=" * 70)
        
        # Extract features
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(image_path)
        X = np.array([features])
        
        # Get predictions from all models
        manager = MultiModelMLManager(model_type='ensemble')
        results = manager.predict_all_models(X)
        
        # Display results
        click.echo()
        table_data = []
        
        for model_name in ['rf', 'xgb', 'svm', 'ensemble']:
            if model_name in results:
                if 'error' in results[model_name]:
                    table_data.append([
                        model_name.upper(),
                        "ERROR",
                        "N/A",
                        results[model_name]['error']
                    ])
                else:
                    pred = results[model_name]['predictions'][0]
                    conf = results[model_name]['confidences'][0]
                    status = "STEGO" if pred == 1 else "CLEAN"
                    table_data.append([
                        model_name.upper(),
                        status,
                        f"{conf:.4f}",
                        ""
                    ])
        
        from tabulate import tabulate
        click.echo(tabulate(table_data, 
                           headers=["Model", "Prediction", "Confidence", "Notes"],
                           tablefmt="grid"))
        
        # Consensus prediction
        stego_votes = sum(1 for m in ['rf', 'xgb', 'svm', 'ensemble'] 
                         if m in results and 'error' not in results[m] 
                         and results[m]['predictions'][0] == 1)
        
        click.echo()
        click.echo(f"Consensus: {stego_votes}/4 models detected steganography")
        
        if stego_votes >= 3:
            click.echo("🚨 HIGH CONFIDENCE: Image is likely steganographic")
        elif stego_votes >= 2:
            click.echo("⚠️  MEDIUM CONFIDENCE: Image may contain hidden data")
        else:
            click.echo("✅ LOW CONFIDENCE: Image appears clean")
        
        click.echo("=" * 70 + "\n")
        
    except Exception as exc:
        click.echo(f"Error: {exc}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------------
# compare-models (NEW - Model Comparison)
# ---------------------------------------------------------------------------

@cli.command("compare-models")
@click.argument("target", type=click.Path(exists=True))
@click.option("--batch", "-b", is_flag=True, help="Batch-process a directory.")
@click.option("--recursive", "-r", is_flag=True, help="Recurse into sub-directories.")
@click.option("--output", "-o", type=click.Path(), help="Output comparison results (JSON).")
def compare_models(target: str, batch: bool, recursive: bool, output: str):
    """Compare model performance on TARGET image(s)."""
    from src.core.ml_multi_model_manager import MultiModelMLManager
    from src.core.ml_features import MLFeatureExtractor
    import numpy as np
    
    target_path = Path(target)
    
    click.echo("\n🔍 Model Comparison Analysis")
    click.echo("=" * 70)
    
    try:
        manager = MultiModelMLManager(model_type='ensemble')
        extractor = MLFeatureExtractor()
        
        if target_path.is_file():
            # Single image
            features = extractor.extract_features(str(target_path))
            X = np.array([features])
            
            results = manager.predict_all_models(X)
            
            click.echo(f"\nImage: {target_path.name}")
            click.echo("-" * 70)
            
            for model_name in ['rf', 'xgb', 'svm', 'ensemble']:
                if model_name in results and 'error' not in results[model_name]:
                    conf = results[model_name]['confidences'][0]
                    pred = "STEGO" if results[model_name]['predictions'][0] == 1 else "CLEAN"
                    click.echo(f"  {model_name.upper():10s} : {pred:5s} (confidence: {conf:.4f})")
        
        elif batch:
            # Batch processing
            image_files = collect_image_files(target_path, recursive)
            if not image_files:
                click.echo("No image files found.")
                return
            
            all_results = []
            
            for img_path in tqdm(image_files, desc="Comparing models"):
                try:
                    features = extractor.extract_features(str(img_path))
                    X = np.array([features])
                    predictions = manager.predict_all_models(X)
                    
                    result_entry = {
                        'filename': Path(img_path).name,
                        'models': {}
                    }
                    
                    for model_name in ['rf', 'xgb', 'svm', 'ensemble']:
                        if model_name in predictions and 'error' not in predictions[model_name]:
                            result_entry['models'][model_name] = {
                                'prediction': int(predictions[model_name]['predictions'][0]),
                                'confidence': float(predictions[model_name]['confidences'][0])
                            }
                    
                    all_results.append(result_entry)
                except Exception as e:
                    if len(image_files) < 20:
                        click.echo(f"  Skipped {img_path}: {e}")
            
            click.echo(f"\n✅ Compared {len(all_results)} images")
            
            # Summary statistics
            stego_by_model = {'rf': 0, 'xgb': 0, 'svm': 0, 'ensemble': 0}
            for result in all_results:
                for model_name in stego_by_model:
                    if model_name in result['models'] and result['models'][model_name]['prediction'] == 1:
                        stego_by_model[model_name] += 1
            
            click.echo("\nDetection Summary:")
            for model_name, count in stego_by_model.items():
                pct = (count / len(all_results) * 100) if len(all_results) > 0 else 0
                click.echo(f"  {model_name.upper():10s} : {count:3d}/{len(all_results)} ({pct:.1f}%)")
            
            # Save results if requested
            if output:
                import json
                with open(output, 'w') as f:
                    json.dump(all_results, f, indent=2)
                click.echo(f"\n✅ Results saved to {output}")
        
        else:
            click.echo("Use --batch (-b) to process a directory.")
        
        click.echo("=" * 70 + "\n")
        
    except Exception as exc:
        click.echo(f"Error: {exc}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _analyze_single(file_path: Path, analyzer: SteganographyAnalyzer, use_ml: bool, model: str) -> dict:
    """Run analysis on a single file and return the result dict."""
    if use_ml:
        from src.core.ml_classifier import MLSteganalysisClassifier
        clf = MLSteganalysisClassifier(model)
        r = clf.predict(str(file_path))
        return {
            "filename": file_path.name,
            "full_path": str(file_path),
            "method": "ML-based",
            "ml_prediction": r["prediction"],
            "ml_probability": r["probability"],
            "ml_confidence": r["confidence"],
        }
    return analyzer.analyze_image(file_path)


def _display_results(results: list[dict], batch: bool, verbose: bool, threshold: float, use_ml: bool, target_path: Path):
    """Pretty-print results to stdout."""
    if not results:
        return

    if len(results) == 1 and not batch:
        result = results[0]
        if verbose:
            click.echo(json.dumps(convert_numpy_types(result), indent=2, default=str))
            return
        if use_ml:
            score = result["ml_probability"] * 100
            status = "⚠️  HIGH SUSPICION" if result["ml_prediction"] == 1 else "✅ CLEAN"
            click.echo(f"Analyzing {target_path}…")
            click.echo(f"ML Prediction      : {status}")
            click.echo(f"Suspicion Score    : {score:.2f}/100")
            click.echo(f"Confidence         : {result['ml_confidence']:.2f}")
        else:
            score = result.get("final_suspicion_score", 0)
            status = "⚠️  HIGH SUSPICION" if score >= threshold else "✅ CLEAN"
            click.echo(f"Analyzing {target_path}…")
            click.echo(f"Final Score        : {score}/100 — {status}")
        return

    # Batch summary
    if verbose:
        for r in results:
            click.echo(json.dumps(convert_numpy_types(r), indent=2, default=str))
        return

    from tabulate import tabulate
    table_data = []
    high_count = 0

    for r in results:
        if use_ml:
            score = r["ml_probability"] * 100
            status = "HIGH" if r["ml_prediction"] == 1 else "LOW"
            conf = f"{r['ml_confidence']:.2f}"
            method = "ML"
        else:
            score = r.get("final_suspicion_score", 0)
            status = "HIGH" if score >= threshold else "LOW"
            conf = str(r.get("methods", {}).get("lsb", {}).get("lsb_suspicion_score", "N/A"))
            method = "Heuristic"

        if status == "HIGH":
            high_count += 1
        table_data.append([r["filename"], f"{score:.2f}", status, conf, method])

    click.echo(f"\nTotal files   : {len(results)}")
    click.echo(f"High suspicion: {high_count}  (threshold ≥ {threshold})")
    click.echo(f"Low suspicion : {len(results) - high_count}")
    click.echo()
    click.echo(tabulate(table_data, headers=["Filename", "Score", "Status", "Confidence", "Method"], tablefmt="grid"))

def _run_forensic_extras(file_path: Path, ela: bool = False,
                          ghost: bool = False, run_forensics: bool = False) -> None:
    """Run optional ELA, Ghost and forensic checks and print results."""
    click.echo("\n" + "─" * 55)
    click.echo("  FORENSIC ANALYSIS")
    click.echo("─" * 55)

    if run_forensics:
        # Format validation
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
            magic_map = {
                b'\xff\xd8\xff': 'JPEG',
                b'\x89PNG': 'PNG',
                b'BM': 'BMP',
                b'GIF8': 'GIF',
            }
            detected = next(
                (fmt for sig, fmt in magic_map.items() if header[:len(sig)] == sig),
                'Unknown'
            )
            ext = file_path.suffix.upper().lstrip('.')
            match = "✅ OK" if detected.upper().startswith(ext[:3]) else "⚠️  MISMATCH"
            click.echo(f"  Format  : {detected} ({match})")
        except Exception as exc:
            click.echo(f"  Format check failed: {exc}")

        # JPEG structure
        if file_path.suffix.lower() in ('.jpg', '.jpeg'):
            try:
                import struct
                with open(file_path, 'rb') as f:
                    data = f.read()
                eoi_offset = None
                i = 0
                marker_count = 0
                while i < len(data) - 1:
                    if data[i] == 0xFF and data[i+1] not in (0x00, 0xFF):
                        code = (data[i] << 8) | data[i+1]
                        marker_count += 1
                        if code == 0xFFD9:
                            eoi_offset = i
                        size = 0
                        if code not in (0xFFD8, 0xFFD9):
                            try:
                                size = struct.unpack('>H', data[i+2:i+4])[0]
                            except Exception:
                                pass
                        i += max(2, size + 2) if size else 2
                    else:
                        i += 1
                click.echo(f"  JPEG markers found: {marker_count}")
                if eoi_offset is not None:
                    appended = len(data) - (eoi_offset + 2)
                    if appended > 0:
                        click.echo(f"  ⚠️  Appended bytes after EOI: {appended} — SUSPICIOUS")
                    else:
                        click.echo("  ✅ No data after EOI marker")
            except Exception as exc:
                click.echo(f"  JPEG structure check failed: {exc}")

        # Stego tool signatures
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            sigs = {b'OpenStego': 'OpenStego', b'SilentEye': 'SilentEye',
                    b'Steghide': 'Steghide', b'outguess': 'OutGuess', b'F5Stego': 'F5'}
            hits = [name for sig, name in sigs.items() if sig in data]
            if hits:
                click.echo(f"  ⚠️  Stego tool signatures: {', '.join(hits)}")
            else:
                click.echo("  ✅ No stego tool signatures found")
        except Exception as exc:
            click.echo(f"  Signature scan failed: {exc}")

    if ela:
        try:
            from src.core.heatmap_generator import HeatmapGenerator
            gen = HeatmapGenerator()
            scores = gen.ela_score(str(file_path))
            ela_path = str(file_path.with_stem(file_path.stem + '_ela').with_suffix('.png'))
            gen.generate_ela_heatmap(str(file_path), output_path=ela_path)
            click.echo(f"\n  ELA Score     : {scores['suspicion_score']:.1f}/100")
            click.echo(f"  ELA Mean      : {scores['ela_mean']:.3f}")
            click.echo(f"  ELA Std       : {scores['ela_std']:.3f}")
            click.echo(f"  ELA Heatmap   : {ela_path}")
        except Exception as exc:
            click.echo(f"  ELA failed: {exc}")

    if ghost and file_path.suffix.lower() in ('.jpg', '.jpeg'):
        try:
            from src.core.heatmap_generator import HeatmapGenerator
            gen = HeatmapGenerator()
            ghost_path = str(file_path.with_stem(file_path.stem + '_ghost').with_suffix('.png'))
            result = gen.generate_ghost_heatmap(str(file_path), output_path=ghost_path)
            click.echo(f"\n  Ghost Quality : Q{result['ghost_quality']}")
            click.echo(f"  Ghost Variance: {result['ghost_variance']:.4f}")
            click.echo(f"  Ghost Score   : {result['suspicion_score']:.1f}/100")
            click.echo(f"  Ghost Map     : {ghost_path}")
        except Exception as exc:
            click.echo(f"  Ghost analysis failed: {exc}")
    elif ghost:
        click.echo("  Ghost analysis skipped — only valid for JPEG files")

    click.echo("─" * 55)

if __name__ == "__main__":
    cli()
