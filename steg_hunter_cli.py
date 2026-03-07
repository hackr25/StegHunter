import click
from pathlib import Path
import json
import numpy as np
from tqdm import tqdm
from src.core.analyzer import SteganographyAnalyzer

def convert_numpy_types(obj):
    """Recursively convert NumPy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

@click.group()
def cli():
    """StegHunter - Advanced Steganography Detection Tool"""
    pass

@cli.command()
@click.argument('image_path')
def info(image_path):
    """Display basic image information"""
    from src.common.image_utils import get_image_info
    try:
        info = get_image_info(image_path)
        click.echo(f"Image Analysis: {image_path}")
        click.echo("-" * 50)
        for key, value in info.items():
            click.echo(f"{key}: {value}")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.argument('target', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file (JSON or CSV)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Output format')
@click.option('--batch', '-b', is_flag=True, help='Batch process directory')
@click.option('--recursive', '-r', is_flag=True, help='Recursive directory scan')
@click.option('--verbose', '-v', is_flag=True, help='Detailed output')
@click.option('--threshold', '-t', type=float, default=50.0, help='Suspicion threshold for highlighting')
@click.option('--use-ml', is_flag=True, help='Use ML model for detection')
@click.option('--model', '-m', type=click.Path(), default='models/steg_model.pkl', help='Path to ML model')
def analyze(target, output, format, batch, recursive, verbose, threshold, use_ml, model):
    """Analyze image(s) for steganography"""
    analyzer = SteganographyAnalyzer()
    target_path = Path(target)
    
    # Check if we should use ML model
    if use_ml and not Path(model).exists():
        click.echo("Warning: ML model not found. Using heuristic analysis instead.")
        use_ml = False
    
    if target_path.is_file():
        # Single file analysis
        if use_ml:
            from src.core.ml_classifier import MLSteganalysisClassifier
            try:
                classifier = MLSteganalysisClassifier(model)
                ml_result = classifier.predict(str(target_path))
                
                results = {
                    'filename': target_path.name,
                    'ml_prediction': ml_result['prediction'],
                    'ml_probability': ml_result['probability'],
                    'ml_confidence': ml_result['confidence'],
                    'method': 'ML-based'
                }
                results_list = [results]
            except Exception as e:
                click.echo(f"Error: {e}")
                return
        else:
            results = analyzer.analyze_image(target_path)
            results_list = [results]
    else:
        # Directory analysis
        if not batch:
            click.echo("Use --batch to process directories.")
            return
        
        image_files = collect_image_files(target_path, recursive)
        if not image_files:
            click.echo("No image files found.")
            return
        
        results_list = []
        for file_path in tqdm(image_files, desc="Analyzing images"):
            try:
                if use_ml:
                    from src.core.ml_classifier import MLSteganalysisClassifier
                    try:
                        classifier = MLSteganalysisClassifier(model)
                        ml_result = classifier.predict(str(file_path))
                        
                        results = {
                            'filename': file_path.name,
                            'ml_prediction': ml_result['prediction'],
                            'ml_probability': ml_result['probability'],
                            'ml_confidence': ml_result['confidence'],
                            'method': 'ML-based'
                        }
                    except Exception as e:
                        if verbose:
                            click.echo(f"Error in ML prediction for {file_path}: {e}")
                        continue
                else:
                    results = analyzer.analyze_image(file_path)
                
                results_list.append(results)
            except Exception as e:
                if verbose:
                    click.echo(f"Error analyzing {file_path}: {e}")
    
    # Display results
    if len(results_list) == 1 and not batch:
        # Single file output
        if verbose:
            click.echo(json.dumps(convert_numpy_types(results_list[0]), indent=2, default=str))
        else:
            result = results_list[0]
            if use_ml:
                score = result['ml_probability'] * 100
                status = "⚠️  HIGH SUSPICION" if result['ml_prediction'] == 1 else "✅ LOW SUSPICION"
                click.echo(f"Analyzing {target_path}...")
                click.echo(f"ML Prediction: {status}")
                click.echo(f"Final Suspicion Score: {score:.2f}/100")
                click.echo(f"Confidence: {result['ml_confidence']:.2f}")
            else:
                score = result['final_suspicion_score']
                status = "⚠️  HIGH SUSPICION" if score >= threshold else "✅ LOW SUSPICION"
                click.echo(f"Analyzing {target_path}...")
                click.echo(f"Final Suspicion Score: {score}/100 - {status}")
    else:
        # Batch output
        if verbose:
            for res in results_list:
                click.echo(json.dumps(convert_numpy_types(res), indent=2, default=str))
        else:
            # Summary table
            from tabulate import tabulate
            table_data = []
            high_suspicion_count = 0
            
            for res in results_list:
                if use_ml:
                    score = res['ml_probability'] * 100
                    status = "HIGH" if res['ml_prediction'] == 1 else "LOW"
                    if status == "HIGH":
                        high_suspicion_count += 1
                    table_data.append([
                        res['filename'],
                        f"{score:.2f}",
                        status,
                        f"{res['ml_confidence']:.2f}",
                        "ML"
                    ])
                else:
                    score = res['final_suspicion_score']
                    status = "HIGH" if score >= threshold else "LOW"
                    if status == "HIGH":
                        high_suspicion_count += 1
                    table_data.append([
                        res['filename'],
                        f"{score:.2f}",
                        status,
                        res['methods']['lsb']['lsb_suspicion_score'],
                        "Heuristic"
                    ])
            
            click.echo("\nAnalysis Summary:")
            click.echo(f"Total files: {len(results_list)}")
            click.echo(f"High suspicion (≥{threshold}): {high_suspicion_count}")
            click.echo(f"Low suspicion: {len(results_list) - high_suspicion_count}")
            
            click.echo("\nDetailed Results:")
            headers = ["Filename", "Final Score", "Status", "Confidence", "Method"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Save results if output specified
    if output:
        if format == 'json':
            save_results_json(results_list, output)
        else:
            save_results_csv(results_list, output)

@cli.command()
@click.argument('image_path')
@click.option('--output', '-o', type=click.Path(), help='Output heatmap path')
@click.option('--method', '-m', type=click.Choice(['lsb', 'comprehensive', 'ml']), default='lsb', help='Heatmap method')
def heatmap(image_path, output, method):
    """Generate heatmap showing suspicious regions"""
    from src.core.heatmap_generator import HeatmapGenerator
    from src.core.ml_classifier import MLSteganalysisClassifier
    
    generator = HeatmapGenerator()
    
    click.echo(f"Generating {method} heatmap for {image_path}...")
    
    try:
        if method == 'lsb':
            heatmap = generator.generate_lsb_heatmap(image_path, output)
        elif method == 'comprehensive':
            heatmaps = generator.generate_comprehensive_heatmap(image_path, output)
            click.echo(f"Generated {len(heatmaps)} different heatmaps")
        elif method == 'ml':
            # ML-based heatmap
            model_path = 'models/steg_model.pkl'
            if not Path(model_path).exists():
                click.echo("Error: No trained model found. Train a model first with 'train-model' command")
                return
            
            classifier = MLSteganalysisClassifier(model_path)
            heatmap = generator.generate_ml_heatmap(image_path, classifier, output)
        
        if output:
            click.echo(f"✅ Heatmap saved to {output}")
        else:
            click.echo("✅ Heatmap generation complete")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
@click.option('--clean-dir', type=click.Path(exists=True), help='Directory with clean images')
@click.option('--stego-dir', type=click.Path(exists=True), help='Directory with stego images')
@click.option('--output', '-o', type=click.Path(), default='models/steg_model.pkl', help='Output model path')
@click.option('--test-size', type=float, default=0.2, help='Test split ratio')
@click.option('--verbose', '-v', is_flag=True, help='Show training details')
def train_model(clean_dir, stego_dir, output, test_size, verbose):
    """Train ML model for steganography detection"""
    from src.core.ml_classifier import MLSteganalysisClassifier
    from pathlib import Path
    
    if not clean_dir or not stego_dir:
        click.echo("Error: Both --clean-dir and --stego-dir are required")
        return
    
    click.echo("Training ML model for steganography detection")
    click.echo(f"Clean images directory: {clean_dir}")
    click.echo(f"Stego images directory: {stego_dir}")
    click.echo(f"Output model: {output}")
    
    # Collect training images
    clean_images = list(Path(clean_dir).glob("*.*"))
    stego_images = list(Path(stego_dir).glob("*.*"))
    
    # Filter for image files
    supported = {'.jpg', '.jpeg', '.png', '.bmp'}
    clean_images = [str(p) for p in clean_images if p.suffix.lower() in supported]
    stego_images = [str(p) for p in stego_images if p.suffix.lower() in supported]
    
    click.echo(f"\nFound {len(clean_images)} clean images")
    click.echo(f"Found {len(stego_images)} stego images")
    
    if len(clean_images) == 0 or len(stego_images) == 0:
        click.echo("Error: Need at least one clean and one stego image")
        return
    
    try:
        # Train model
        classifier = MLSteganalysisClassifier()
        metrics = classifier.train_model(clean_images, stego_images, output, test_size)
        
        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Training Results")
        click.echo("=" * 60)
        click.echo(f"Accuracy:  {metrics['accuracy']:.4f}")
        click.echo(f"Precision: {metrics['precision']:.4f}")
        click.echo(f"Recall:    {metrics['recall']:.4f}")
        click.echo(f"F1-Score:  {metrics['f1_score']:.4f}")
        click.echo(f"CV Mean:   {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
        
        if verbose:
            click.echo("\nFeature Importance (Top 10):")
            sorted_features = sorted(metrics['feature_importance'].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in sorted_features:
                click.echo(f"  {feature:40s}: {importance:.4f}")
        
        click.echo(f"\n✅ Model saved to {output}")
        
    except Exception as e:
        click.echo(f"Error during training: {e}")
        import traceback
        traceback.print_exc()

@cli.command()
@click.argument('image_path')
@click.option('--model', '-m', type=click.Path(), default='models/steg_model.pkl', help='Path to trained model')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed prediction info')
def predict(image_path, model, verbose):
    """Predict if image contains steganography using ML model"""
    from src.core.ml_classifier import MLSteganalysisClassifier
    from pathlib import Path
    
    if not Path(model).exists():
        click.echo(f"Error: Model not found at {model}")
        click.echo("Train a model first with: python steg_hunter_cli.py train-model")
        return
    
    try:
        classifier = MLSteganalysisClassifier(model)
        result = classifier.predict(image_path)
        
        click.echo(f"ML Prediction for {image_path}")
        click.echo("-" * 50)
        
        prediction_text = "STEGANOGRAPHY DETECTED" if result['prediction'] == 1 else "CLEAN IMAGE"
        click.echo(f"Prediction: {prediction_text}")
        click.echo(f"Probability: {result['probability']:.4f}")
        click.echo(f"Confidence: {result['confidence']:.4f}")
        
        if verbose and result['error']:
            click.echo(f"Error: {result['error']}")
            
    except Exception as e:
        click.echo(f"Error during prediction: {e}")

@cli.command()
@click.argument('target', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Output format')
def export(target, output, format):
    """Export analysis results to file"""
    analyzer = SteganographyAnalyzer()
    target_path = Path(target)
    
    if target_path.is_file():
        results = [analyzer.analyze_image(target_path)]
    else:
        image_files = collect_image_files(target_path, recursive=False)
        if not image_files:
            click.echo("No image files found.")
            return
        results_list = []
        for file_path in tqdm(image_files, desc="Processing images"):
            try:
                results = analyzer.analyze_image(file_path)
                results_list.append(results)
            except Exception as e:
                click.echo(f"Error analyzing {file_path}: {e}")
        results = results_list
    
    # Save results
    if output:
        if format == 'json':
            save_results_json(results, output)
        else:
            save_results_csv(results, output)
        click.echo(f"✅ Results exported to {output}")
    else:
        click.echo("Error: --output is required")

def collect_image_files(directory, recursive=False):
    """Collect image files from directory"""
    supported = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    files = []
    if recursive:
        for item in directory.rglob('*'):
            if item.is_file() and item.suffix.lower() in supported:
                files.append(item)
    else:
        for item in directory.glob('*'):
            if item.is_file() and item.suffix.lower() in supported:
                files.append(item)
    return files

def save_results_json(results, output_path):
    """Save results to JSON file"""
    converted_results = [convert_numpy_types(res) for res in results]
    with open(output_path, 'w') as f:
        json.dump(converted_results, f, indent=2, default=str)
    click.echo(f"Results saved to {output_path}")

def save_results_csv(results, output_path):
    """Save results to CSV file"""
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            'Filename', 'File Size', 'Format', 'Dimensions', 'Mode',
            'Final Score', 'Status', 'LSB Score', 'Basic Score',
            'Chi-Square Score', 'Pixel Diff Score'
        ])
        # Write data rows
        for res in results:
            writer.writerow([
                res['filename'],
                res['file_size'],
                res['format'],
                f"{res['dimensions'][0]}x{res['dimensions'][1]}",
                res['mode'],
                res['final_suspicion_score'],
                "HIGH" if res['final_suspicion_score'] >= 50 else "LOW",
                res['methods']['lsb']['lsb_suspicion_score'],
                res['methods']['basic']['basic_suspicion_score'],
                res['methods']['chi_square']['suspicion_score'],
                res['methods']['pixel_differencing']['suspicion_score']
            ])
    click.echo(f"Results saved to {output_path}")

if __name__ == '__main__':
    cli()
