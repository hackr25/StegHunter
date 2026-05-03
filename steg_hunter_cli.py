"""
StegHunter CLI — Advanced Steganography Detection Tool.

Enhanced CLI interface with rich formatting and better UX.

Usage:
  After installation: steg-hunter info image.png
  Or: python steg_hunter_cli_improved.py info image.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from tqdm import tqdm

from src.common.utils import collect_image_files, convert_numpy_types, save_results_json, save_results_csv
from src.common.exceptions import InvalidImageError, ConfigError, AnalysisError
from src.core.analyzer import SteganographyAnalyzer

console = Console()

# ASCII Banner with enhanced graphics (Windows-compatible)
BANNER = r"""
    _____ _            _    _             _            
   / ____| |          | |  | |           | |           
  | (___ | |_ ___  __ | |__| |_   _ _ __ | |_ ___ _ __ 
   \___ \| __/ _ \/ _\|  __  | | | | '_ \| __/ _ \ '__|
   ____) | ||  __/ (_| | |  | | |_| | | | | ||  __/ |   
  |_____/ \__\___|\__,_|_|  |_|\__,_|_| |_|\__\___|_|   

  ====================================================================
      STEGHUNTER - Advanced Steganography & Forensics Detection
  ====================================================================
             Multi-Model ML | Video Analysis | Heatmaps
  
  DETECTION PIPELINE:
  [Phase 1] File Forensics & Metadata Analysis
  [Phase 2] Image Artifact Detection (LSB, ELA, JPEG Ghost)
  [Phase 3] Clone Detection & Forgery Analysis
  [Phase 4] Video Frame Analysis & Temporal Detection
  [Phase 5] 4 ML Models (Random Forest, XGBoost, SVM, Ensemble)

  ML MODELS:
  - Random Forest    [92% accuracy]  Fast baseline
  - XGBoost          [96% accuracy]  Highest performance
  - SVM              [94% accuracy]  Non-linear patterns
  - Ensemble         [97% accuracy]  Best consensus

  ====================================================================
  Type 'steg-hunter --help' for available commands
  ====================================================================
"""

# ---------------------------------------------------------------------------
# CLI Context
# ---------------------------------------------------------------------------

class Config:
    """CLI configuration object."""
    def __init__(self):
        self.verbose = False
        self.quiet = False


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.version_option(version='2.0.0', prog_name='StegHunter')
@click.pass_context
def cli(ctx, verbose, quiet):
    """StegHunter — Advanced Steganography Detection Tool."""
    ctx.ensure_object(Config)
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def print_success(message: str):
    """Print success message."""
    console.print(f"✓ {message}", style="bold green")


def print_error(message: str):
    """Print error message."""
    console.print(f"✗ {message}", style="bold red")


def print_info(message: str):
    """Print info message."""
    console.print(f"ℹ {message}", style="bold blue")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"⚠ {message}", style="bold yellow")


# ---------------------------------------------------------------------------
# info command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.pass_context
def info(ctx, image_path: str):
    """Display basic metadata for IMAGE_PATH."""
    from src.common.image_utils import get_image_info
    
    try:
        print_info(f"Analyzing metadata for: {image_path}")
        data = get_image_info(image_path)
        
        # Create rich table
        table = Table(title="Image Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(key, str(value))
        
        console.print(table)
        print_success(f"Metadata analysis complete")
        
    except InvalidImageError as e:
        print_error(f"Invalid image: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.option("--use-ml", is_flag=True, help="Use ML-based detection")
@click.option("--batch", is_flag=True, help="Batch mode for directories")
@click.option("--recursive", is_flag=True, help="Recursive directory scan")
@click.option("-o", "--output", type=str, help="Output file (JSON/CSV)")
@click.option("--method", type=str, default="all", help="Analysis method (all/lsb/ela/noise/etc)")
@click.pass_context
def analyze(ctx, image_path: str, use_ml: bool, batch: bool, recursive: bool, output: Optional[str], method: str):
    """Analyze IMAGE_PATH for steganography."""
    try:
        analyzer = SteganographyAnalyzer()
        path = Path(image_path)
        
        if batch or path.is_dir():
            # Batch processing
            image_files = collect_image_files(image_path, recursive=recursive)
            
            if not image_files:
                print_error("No image files found in directory")
                sys.exit(1)
            
            print_info(f"Found {len(image_files)} image(s) for batch analysis")
            
            results = []
            
            with Progress(
                SpinnerColumn(),
                BarColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Analyzing images...", total=len(image_files))
                
                for img_file in image_files:
                    try:
                        result = analyzer.analyze_image(str(img_file)) if use_ml else analyzer.basic_analysis(str(img_file))
                        results.append(convert_numpy_types(result))
                    except Exception as e:
                        print_warning(f"Failed to analyze {img_file}: {e}")
                    
                    progress.update(task, advance=1)
            
            # Save results
            if output:
                if output.endswith('.csv'):
                    save_results_csv(results, output)
                else:
                    save_results_json(results, output)
                print_success(f"Results saved to {output}")
            else:
                # Display results table
                table = Table(title="Batch Analysis Results", show_header=True, header_style="bold magenta")
                table.add_column("File", style="cyan")
                table.add_column("Suspicion Score", style="yellow")
                table.add_column("Status", style="green")
                
                for result in results:
                    filename = result.get("filename", "Unknown")
                    score = result.get("final_suspicion_score", 0)
                    status = "⚠ Suspicious" if score > 50 else "✓ Clean"
                    table.add_row(filename, f"{score:.1f}%", status)
                
                console.print(table)
        
        else:
            # Single image analysis
            print_info(f"Analyzing: {image_path}")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("[cyan]Processing image...", total=None)
                result = analyzer.analyze_image(image_path) if use_ml else analyzer.basic_analysis(image_path)
            
            result = convert_numpy_types(result)
            
            # Display result
            score = result.get("final_suspicion_score", 0)
            status = "🚨 SUSPICIOUS" if score > 50 else "✅ CLEAN"
            
            console.print(Panel(
                f"Suspicion Score: [bold yellow]{score:.1f}%[/bold yellow]\n"
                f"Status: [bold]{status}[/bold]\n"
                f"Analysis: {result.get('explanation', 'N/A')}",
                title="Analysis Result",
                border_style="cyan"
            ))
            
            # Show detailed methods if available
            if "methods" in result:
                table = Table(title="Detection Methods", show_header=True, header_style="bold magenta")
                table.add_column("Method", style="cyan")
                table.add_column("Score", style="yellow")
                table.add_column("Status", style="green")
                
                for method_name, method_result in result["methods"].items():
                    method_score = method_result.get("suspicion_score", 0)
                    method_status = "⚠" if method_score > 50 else "✓"
                    table.add_row(method_name, f"{method_score:.1f}%", method_status)
                
                console.print(table)
            
            # Save if output specified
            if output:
                if output.endswith('.csv'):
                    save_results_csv([result], output)
                else:
                    save_results_json([result], output)
                print_success(f"Results saved to {output}")
            else:
                print_success("Analysis complete")
    
    except InvalidImageError as e:
        print_error(f"Invalid image: {e}")
        sys.exit(1)
    except AnalysisError as e:
        print_error(f"Analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# heatmap command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.option("--output", "-o", type=str, required=True, help="Output heatmap file")
@click.option("--method", type=str, default="lsb", help="Analysis method for heatmap")
@click.pass_context
def heatmap(ctx, image_path: str, output: str, method: str):
    """Generate heatmap visualization for IMAGE_PATH."""
    try:
        from src.core.heatmap_generator import HeatmapGenerator
        
        print_info(f"Generating {method} heatmap for: {image_path}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Creating heatmap...", total=None)
            
            heatmap_gen = HeatmapGenerator()
            heatmap_gen.generate(image_path, output, analysis_type=method)
        
        print_success(f"Heatmap saved to {output}")
    
    except Exception as e:
        print_error(f"Error generating heatmap: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# generate-video-training-data command
# ---------------------------------------------------------------------------

@cli.command(name='generate-video-training-data')
@click.option("--clean-video-dir", type=str, required=True, help="Directory with clean videos")
@click.option("--output-dir", type=str, required=True, help="Directory to save extracted frames")
@click.option("--stego-video-dir", type=str, default=None, help="Directory with stego videos (optional)")
@click.option("--frames-per-video", type=int, default=15, help="Frames to extract per video")
@click.option("--embedding-rate", type=float, default=1.0, help="LSB embedding rate (0.0-1.0)")
@click.pass_context
def generate_video_training_data(ctx, clean_video_dir: str, output_dir: str, 
                                stego_video_dir: str, frames_per_video: int, embedding_rate: float):
    """Generate training data from videos (extract frames + create stego videos)."""
    try:
        from src.core.video_training_generator import VideoTrainingDataGenerator
        
        print_info(f"Generating video training data...")
        print_info(f"Clean videos: {clean_video_dir}")
        if stego_video_dir:
            print_info(f"Stego videos: {stego_video_dir}")
        print_info(f"Output directory: {output_dir}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Processing videos...", total=None)
            
            generator = VideoTrainingDataGenerator()
            stats = generator.generate_mixed_dataset(
                clean_image_dir=clean_video_dir,
                stego_image_dir=stego_video_dir or clean_video_dir,
                clean_video_dir=clean_video_dir,
                stego_video_dir=stego_video_dir,
                output_image_dir=output_dir,
                num_video_samples=100,
                frames_per_video=frames_per_video,
                embedding_rate=embedding_rate
            )
        
        # Display summary
        table = Table(title="Video Training Data Generated", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="yellow")
        
        for key, val in stats.items():
            table.add_row(key.replace('_', ' ').title(), str(val))
        
        console.print(table)
        print_success(f"Training data saved to {output_dir}")
    
    except Exception as e:
        print_error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ---------------------------------------------------------------------------
# train-model command
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--clean-dir", type=str, required=True, help="Directory with clean images")
@click.option("--stego-dir", type=str, required=True, help="Directory with stego images")
@click.option("--output", "-o", type=str, default="models/steg_model.pkl", help="Output model file")
@click.pass_context
def train_model(ctx, clean_dir: str, stego_dir: str, output: str):
    """Train ML model on labeled datasets."""
    try:
        from src.core.ml_classifier import MLClassifier
        
        print_info(f"Training ML model...")
        print_info(f"Clean images: {clean_dir}")
        print_info(f"Stego images: {stego_dir}")
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Training model...", total=None)
            
            classifier = MLClassifier()
            classifier.train(clean_dir, stego_dir)
            classifier.save_model(output)
        
        print_success(f"Model trained and saved to {output}")
    
    except Exception as e:
        print_error(f"Training failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# train-all-models command
# ---------------------------------------------------------------------------

@cli.command(name='train-all-models')
@click.option("--clean-dir", type=str, required=True, help="Directory with clean images")
@click.option("--stego-dir", type=str, required=True, help="Directory with stego images")
@click.option("--clean-videos", type=str, default=None, help="Directory with clean videos (optional)")
@click.option("--stego-videos", type=str, default=None, help="Directory with stego videos (optional)")
@click.pass_context
def train_all_models(ctx, clean_dir: str, stego_dir: str, clean_videos: str, stego_videos: str):
    """Train all 4 ML models (Random Forest, XGBoost, SVM, Ensemble) on images + videos."""
    try:
        from src.core.ml_multi_model_manager import MultiModelMLManager
        
        print_info(f"Training all 4 ML models...")
        print_info(f"Clean images: {clean_dir}")
        print_info(f"Stego images: {stego_dir}")
        if clean_videos:
            print_info(f"Clean videos: {clean_videos}")
        if stego_videos:
            print_info(f"Stego videos: {stego_videos}")
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if clean_videos or stego_videos:
                progress.add_task("[cyan]Training with images + videos...", total=None)
                manager = MultiModelMLManager()
                metrics = manager.train_all_models_with_video(
                    clean_dir, stego_dir, clean_videos, stego_videos
                )
            else:
                progress.add_task("[cyan]Training with images only...", total=None)
                manager = MultiModelMLManager()
                metrics = manager.train_all_models(clean_dir, stego_dir)
        
        # Display metrics table
        table = Table(title="Model Training Metrics", show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan")
        table.add_column("Accuracy", style="yellow")
        table.add_column("Precision", style="green")
        table.add_column("Recall", style="green")
        table.add_column("F1-Score", style="green")
        
        for model_name, model_metrics in metrics.items():
            table.add_row(
                model_name,
                f"{model_metrics.get('accuracy', 0):.3f}",
                f"{model_metrics.get('precision', 0):.3f}",
                f"{model_metrics.get('recall', 0):.3f}",
                f"{model_metrics.get('f1_score', 0):.3f}",
            )
        
        console.print(table)
        
        # Show training data summary
        training_mode = "Images + Videos" if (clean_videos or stego_videos) else "Images Only"
        console.print(Panel(
            f"Training Mode: [bold cyan]{training_mode}[/bold cyan]\n"
            f"Status: [bold green]✓ All models trained and saved successfully![/bold green]",
            title="Training Complete",
            border_style="green"
        ))
    
    except Exception as e:
        print_error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ---------------------------------------------------------------------------
# analyze-all-models command
# ---------------------------------------------------------------------------

@cli.command(name='analyze-all-models')
@click.argument("image_path")
@click.pass_context
def analyze_all_models(ctx, image_path: str):
    """Analyze image with all 4 ML models."""
    try:
        from src.core.ml_multi_model_manager import MultiModelMLManager
        
        print_info(f"Analyzing with all 4 ML models: {image_path}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Running predictions...", total=None)
            
            manager = MultiModelMLManager()
            results = manager.predict_all_models(image_path)
        
        # Display results table
        table = Table(title="Multi-Model Analysis Results", show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan")
        table.add_column("Suspicion Score", style="yellow")
        table.add_column("Confidence", style="green")
        table.add_column("Status", style="green")
        
        scores = []
        for model_name, prediction in results.items():
            score = prediction.get('suspicion_score', 0)
            confidence = prediction.get('confidence', 0)
            status = "⚠ Suspicious" if score > 50 else "✓ Clean"
            scores.append(score)
            table.add_row(model_name, f"{score:.1f}%", f"{confidence:.1f}%", status)
        
        console.print(table)
        
        # Show consensus
        consensus_score = sum(scores) / len(scores) if scores else 0
        consensus_status = "🚨 SUSPICIOUS" if consensus_score > 50 else "✅ CLEAN"
        
        console.print(Panel(
            f"Consensus Score: [bold yellow]{consensus_score:.1f}%[/bold yellow]\n"
            f"Status: [bold]{consensus_status}[/bold]",
            title="Consensus Result",
            border_style="cyan"
        ))
        
        print_success("Analysis complete")
    
    except Exception as e:
        print_error(f"Analysis failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# compare-models command
# ---------------------------------------------------------------------------

@cli.command(name='compare-models')
@click.argument("image_dir")
@click.option("--output", "-o", type=str, help="Output JSON file")
@click.pass_context
def compare_models(ctx, image_dir: str, output: Optional[str]):
    """Compare model performance on batch of images."""
    try:
        from src.core.ml_multi_model_manager import MultiModelMLManager
        
        image_files = collect_image_files(image_dir, recursive=True)
        
        if not image_files:
            print_error("No image files found in directory")
            sys.exit(1)
        
        print_info(f"Comparing models on {len(image_files)} images...")
        
        comparison_results = []
        manager = MultiModelMLManager()
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Comparing models...", total=len(image_files))
            
            for img_file in image_files:
                try:
                    results = manager.predict_all_models(str(img_file))
                    results['filename'] = str(img_file)
                    comparison_results.append(convert_numpy_types(results))
                except Exception as e:
                    print_warning(f"Failed to analyze {img_file}: {e}")
                
                progress.update(task, advance=1)
        
        # Save or display results
        if output:
            save_results_json(comparison_results, output)
            print_success(f"Comparison results saved to {output}")
        else:
            # Display results table
            table = Table(title="Model Comparison Results", show_header=True, header_style="bold magenta")
            table.add_column("File", style="cyan")
            table.add_column("RF Score", style="yellow")
            table.add_column("XGB Score", style="yellow")
            table.add_column("SVM Score", style="yellow")
            table.add_column("Ensemble", style="green")
            
            for result in comparison_results[:10]:  # Show first 10
                filename = Path(result.get("filename", "Unknown")).name
                rf_score = result.get("Random Forest", {}).get("suspicion_score", 0)
                xgb_score = result.get("XGBoost", {}).get("suspicion_score", 0)
                svm_score = result.get("SVM", {}).get("suspicion_score", 0)
                ensemble_score = result.get("Ensemble", {}).get("suspicion_score", 0)
                table.add_row(
                    filename,
                    f"{rf_score:.1f}%",
                    f"{xgb_score:.1f}%",
                    f"{svm_score:.1f}%",
                    f"{ensemble_score:.1f}%"
                )
            
            console.print(table)
        
        print_success("Model comparison complete")
    
    except Exception as e:
        print_error(f"Comparison failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# video-analyze command
# ---------------------------------------------------------------------------

@cli.command(name='video-analyze')
@click.argument("video_path")
@click.option("--heatmap", type=str, help="Output heatmap file")
@click.option("--output", "-o", type=str, help="Output JSON file")
@click.option("--verbose", is_flag=True, help="Verbose output with frame details")
@click.pass_context
def video_analyze(ctx, video_path: str, heatmap: Optional[str], output: Optional[str], verbose: bool):
    """Analyze video for steganography."""
    try:
        from src.core.video_analyzer import VideoAnalyzer
        
        print_info(f"Analyzing video: {video_path}")
        
        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Analyzing video frames...", total=None)
            
            analyzer = VideoAnalyzer()
            result = analyzer.analyze_video(video_path)
        
        if result.get('error'):
            print_error(f"Video analysis error: {result['error']}")
            sys.exit(1)
        
        if output:
            save_results_json([convert_numpy_types(result)], output)
            print_success(f"Results saved to {output}")
        
        score = result.get('final_suspicion_score', 0)
        status = "🚨 SUSPICIOUS" if score > 50 else "✅ CLEAN"
        
        # Display comprehensive results
        frame_count = result.get('analyzed_frames', 0)
        anomalies = sum(len(v) for v in result.get('temporal_anomalies', {}).values())
        
        console.print(Panel(
            f"Suspicion Score: [bold yellow]{score:.2f}%[/bold yellow]\n"
            f"Status: [bold]{status}[/bold]\n"
            f"Frames Analyzed: [cyan]{frame_count}[/cyan]\n"
            f"Temporal Anomalies: [red]{anomalies}[/red]\n"
            f"Analysis Time: [green]{result.get('analysis_time', 0):.2f}s[/green]",
            title="📹 Video Forensics Analysis Result",
            border_style="cyan"
        ))
        
        # Display technique breakdown if verbose
        if verbose:
            if result.get('frame_results'):
                console.print("[bold cyan]Per-Technique Summary:[/bold cyan]")
                for frame in result['frame_results'][:1]:  # Show first frame as example
                    for technique, data in frame.get('techniques', {}).items():
                        score = data.get('suspicion_score', 0)
                        console.print(f"  • {technique.upper()}: {score:.1f}")
        
        print_success("Video analysis complete")
    
    except Exception as e:
        print_error(f"Video analysis failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# predict command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("image_path")
@click.option("--model", type=str, default="models/steg_model.pkl", help="Model file path")
@click.pass_context
def predict(ctx, image_path: str, model: str):
    """Run ML prediction on IMAGE_PATH."""
    try:
        from src.core.ml_classifier import MLClassifier
        
        print_info(f"Making prediction for: {image_path}")
        print_info(f"Using model: {model}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("[cyan]Running prediction...", total=None)
            
            classifier = MLClassifier()
            classifier.load_model(model)
            result = classifier.predict(image_path)
        
        score = result.get('suspicion_score', 0)
        confidence = result.get('confidence', 0)
        status = "🚨 SUSPICIOUS" if score > 50 else "✅ CLEAN"
        
        console.print(Panel(
            f"Suspicion Score: [bold yellow]{score:.1f}%[/bold yellow]\n"
            f"Confidence: [bold green]{confidence:.1f}%[/bold green]\n"
            f"Status: [bold]{status}[/bold]",
            title="ML Prediction Result",
            border_style="cyan"
        ))
        
        print_success("Prediction complete")
    
    except Exception as e:
        print_error(f"Prediction failed: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point with banner display."""
    # Always show banner on startup (except for help/version)
    if '--help' not in sys.argv and '-h' not in sys.argv and '--version' not in sys.argv:
        try:
            sys.stdout.write(BANNER)
            sys.stdout.write("\n>>> StegHunter v2.0.0 ready | 4 ML Models | 5-Phase Pipeline\n\n")
            sys.stdout.flush()
        except Exception:
            pass
    
    cli(obj=Config())


if __name__ == "__main__":
    main()
