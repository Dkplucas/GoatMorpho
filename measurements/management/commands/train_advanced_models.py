from django.core.management.base import BaseCommand
from django.conf import settings
import logging
import pandas as pd
from pathlib import Path
import os

from measurements.models import Goat, MorphometricMeasurement
from measurements.ml_trainer_advanced import AdvancedMLTrainer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train advanced AI/ML models for goat morphometry prediction'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-samples',
            type=int,
            default=50,
            help='Minimum number of samples required for training (default: 50)'
        )
        parser.add_argument(
            '--breed-specific',
            action='store_true',
            help='Train breed-specific models in addition to general models'
        )
        parser.add_argument(
            '--force-retrain',
            action='store_true',
            help='Force retraining even if models already exist'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save trained models (default: measurements/ml_models)'
        )
        parser.add_argument(
            '--test-split',
            type=float,
            default=0.2,
            help='Fraction of data to use for testing (default: 0.2)'
        )
        parser.add_argument(
            '--cv-folds',
            type=int,
            default=5,
            help='Number of cross-validation folds (default: 5)'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('Starting advanced AI/ML model training...')
            )
            
            # Configuration
            min_samples = options['min_samples']
            breed_specific = options['breed_specific']
            force_retrain = options['force_retrain']
            output_dir = options['output_dir']
            test_split = options['test_split']
            cv_folds = options['cv_folds']
            
            # Check data availability
            total_measurements = MorphometricMeasurement.objects.count()
            self.stdout.write(f"Total measurements in database: {total_measurements}")
            
            if total_measurements < min_samples:
                self.stdout.write(
                    self.style.ERROR(
                        f'Insufficient data for training. '
                        f'Found {total_measurements} measurements, need at least {min_samples}'
                    )
                )
                return
            
            # Initialize trainer
            trainer = AdvancedMLTrainer(model_dir=output_dir)
            
            # Check if models already exist
            if not force_retrain and self._models_exist(trainer.model_dir):
                self.stdout.write(
                    self.style.WARNING(
                        'Models already exist. Use --force-retrain to overwrite.'
                    )
                )
                return
            
            # Extract training data
            self.stdout.write('Extracting training data from database...')
            training_data = self._extract_training_data()
            
            if len(training_data) < min_samples:
                self.stdout.write(
                    self.style.ERROR(
                        f'Extracted only {len(training_data)} valid samples, '
                        f'need at least {min_samples}'
                    )
                )
                return
            
            self.stdout.write(f"Extracted {len(training_data)} training samples")
            
            # Prepare data
            df = pd.DataFrame(training_data)
            X, y = trainer.prepare_training_data(df)
            
            self.stdout.write(f"Prepared data: {X.shape[0]} samples, {X.shape[1]} features")
            self.stdout.write(f"Target measurements: {len(y.columns)}")
            
            # Train ensemble models
            self.stdout.write('Training ensemble models...')
            results = trainer.train_ensemble_models(X, y, test_size=test_split)
            
            # Display training results
            self._display_training_results(results)
            
            # Train breed-specific models if requested
            if breed_specific:
                self.stdout.write('Training breed-specific models...')
                breed_results = trainer.train_breed_specific_models(X, y)
                self._display_breed_results(breed_results)
            
            # Generate performance report
            self.stdout.write('Generating performance reports...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Model training completed successfully!'
                    f'\n📁 Models saved to: {trainer.model_dir}'
                    f'\n📊 Performance report: {trainer.model_dir}/model_performance_report.csv'
                    f'\n📈 Visualizations: {trainer.model_dir}/model_performance_plots.png'
                )
            )
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Training failed: {str(e)}')
            )
            raise

    def _extract_training_data(self):
        """Extract training data from database"""
        data = []
        
        for measurement in MorphometricMeasurement.objects.select_related('goat').all():
            goat = measurement.goat
            
            # Calculate age if birth date is available
            age_months = None
            if goat.birth_date:
                age_months = (measurement.measurement_date - goat.birth_date).days / 30.44
            
            row = {
                'goat_id': goat.id,
                'breed': goat.breed,
                'sex': goat.sex,
                'age_months': age_months,
                'confidence_score': measurement.confidence_score,
                'measurement_date': measurement.measurement_date,
                
                # Measurements
                'hauteur_au_garrot': measurement.hauteur_au_garrot,
                'hauteur_au_dos': measurement.hauteur_au_dos,
                'hauteur_au_sternum': measurement.hauteur_au_sternum,
                'hauteur_au_sacrum': measurement.hauteur_au_sacrum,
                'body_length': measurement.body_length,
                'tour_de_poitrine': measurement.tour_de_poitrine,
                'perimetre_thoracique': measurement.perimetre_thoracique,
                'largeur_poitrine': measurement.largeur_poitrine,
                'largeur_hanche': measurement.largeur_hanche,
                'largeur_tete': measurement.largeur_tete,
                'longueur_tete': measurement.longueur_tete,
                'longueur_oreille': measurement.longueur_oreille,
                'longueur_cou': measurement.longueur_cou,
                'tour_du_cou': measurement.tour_du_cou,
                'longueur_queue': measurement.longueur_queue,
            }
            
            # Only include rows with at least some measurements
            measurement_fields = [
                'hauteur_au_garrot', 'hauteur_au_dos', 'body_length', 
                'tour_de_poitrine', 'largeur_poitrine'
            ]
            
            if any(row[field] is not None for field in measurement_fields):
                data.append(row)
        
        return data

    def _models_exist(self, model_dir: Path) -> bool:
        """Check if trained models already exist"""
        if not model_dir.exists():
            return False
        
        # Check for key model files
        key_files = [
            'hauteur_au_garrot_random_forest_model.joblib',
            'body_length_random_forest_model.joblib',
            'tour_de_poitrine_random_forest_model.joblib'
        ]
        
        return any((model_dir / filename).exists() for filename in key_files)

    def _display_training_results(self, results):
        """Display training results in a formatted table"""
        self.stdout.write('\n' + '='*80)
        self.stdout.write('🎯 ENSEMBLE MODEL TRAINING RESULTS')
        self.stdout.write('='*80)
        
        # Headers
        headers = ['Measurement', 'Best Model', 'Test MAE', 'Test R²', 'CV Score']
        self.stdout.write(f"{'Measurement':<25} {'Best Model':<15} {'Test MAE':<10} {'Test R²':<10} {'CV Score':<10}")
        self.stdout.write('-' * 80)
        
        for measurement, models in results.items():
            if not models:
                continue
                
            # Find best model based on test MAE
            best_model_name = min(models.keys(), key=lambda k: models[k]['test_mae'])
            best_model = models[best_model_name]
            
            self.stdout.write(
                f"{measurement:<25} "
                f"{best_model_name:<15} "
                f"{best_model['test_mae']:<10.2f} "
                f"{best_model['test_r2']:<10.3f} "
                f"{best_model['cv_score_mean']:<10.2f}"
            )
        
        self.stdout.write('='*80)

    def _display_breed_results(self, breed_results):
        """Display breed-specific training results"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('🐐 BREED-SPECIFIC MODEL RESULTS')
        self.stdout.write('='*60)
        
        for breed, results in breed_results.items():
            self.stdout.write(f"\n📋 Breed: {breed.upper()}")
            self.stdout.write('-' * 40)
            
            total_models = sum(len(models) for models in results.values())
            successful_measurements = len([m for m, models in results.items() if models])
            
            self.stdout.write(f"  • Measurements modeled: {successful_measurements}")
            self.stdout.write(f"  • Total models trained: {total_models}")
            
            # Show best performing measurement for this breed
            if results:
                best_measurement = None
                best_r2 = -1
                
                for measurement, models in results.items():
                    if models:
                        for model_name, metrics in models.items():
                            if metrics['test_r2'] > best_r2:
                                best_r2 = metrics['test_r2']
                                best_measurement = measurement
                
                if best_measurement:
                    self.stdout.write(f"  • Best performing: {best_measurement} (R² = {best_r2:.3f})")
        
        self.stdout.write('='*60)

    def _display_summary_stats(self, training_data):
        """Display summary statistics about the training data"""
        df = pd.DataFrame(training_data)
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 TRAINING DATA SUMMARY')
        self.stdout.write('='*60)
        
        # Basic stats
        self.stdout.write(f"Total samples: {len(df)}")
        self.stdout.write(f"Unique goats: {df['goat_id'].nunique()}")
        
        # Breed distribution
        if 'breed' in df.columns:
            breed_counts = df['breed'].value_counts()
            self.stdout.write(f"\nBreed distribution:")
            for breed, count in breed_counts.head(5).items():
                percentage = (count / len(df)) * 100
                self.stdout.write(f"  • {breed}: {count} ({percentage:.1f}%)")
        
        # Measurement completeness
        measurement_cols = [
            'hauteur_au_garrot', 'hauteur_au_dos', 'body_length',
            'tour_de_poitrine', 'largeur_poitrine'
        ]
        
        self.stdout.write(f"\nMeasurement completeness:")
        for col in measurement_cols:
            if col in df.columns:
                completeness = (1 - df[col].isna().mean()) * 100
                self.stdout.write(f"  • {col}: {completeness:.1f}%")
        
        self.stdout.write('='*60)
