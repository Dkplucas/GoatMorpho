import os
import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
import xgboost as xgb
from scipy import stats
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AdvancedMLTrainer:
    """
    Advanced machine learning trainer with multiple algorithms,
    feature engineering, and breed-specific modeling
    """
    
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            self.model_dir = Path(__file__).parent / 'ml_models'
        else:
            self.model_dir = Path(model_dir)
        
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self.models = {
            'random_forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'xgboost': xgb.XGBRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=6,
                random_state=42,
                n_jobs=-1
            )
        }
        
        # Feature engineering pipeline
        self.scaler = StandardScaler()
        self.feature_selector = SelectKBest(score_func=f_regression, k=20)
        self.label_encoders = {}
        
        # Breed-specific models
        self.breed_models = {}
        
        # Model performance tracking
        self.performance_metrics = {}
        
        logger.info("Advanced ML trainer initialized")
    
    def prepare_training_data(self, measurements_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare and engineer features for training
        """
        try:
            logger.info("Preparing training data with feature engineering")
            
            # Clean data
            df = measurements_data.copy()
            df = self._clean_data(df)
            
            # Feature engineering
            df = self._engineer_features(df)
            
            # Handle categorical variables
            df = self._encode_categorical_features(df)
            
            # Remove outliers
            df = self._remove_outliers(df)
            
            # Select target variables (measurement columns)
            measurement_columns = [
                'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum',
                'hauteur_au_sacrum', 'body_length', 'tour_de_poitrine',
                'perimetre_thoracique', 'largeur_poitrine', 'largeur_hanche',
                'largeur_tete', 'longueur_tete', 'longueur_oreille',
                'longueur_cou', 'tour_du_cou', 'longueur_queue'
            ]
            
            # Prepare features and targets
            feature_columns = [col for col in df.columns if col not in measurement_columns + ['id', 'goat_id']]
            X = df[feature_columns]
            y = df[measurement_columns]
            
            logger.info(f"Prepared dataset with {X.shape[0]} samples and {X.shape[1]} features")
            logger.info(f"Target measurements: {len(measurement_columns)}")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess raw data"""
        logger.info("Cleaning data...")
        
        # Remove rows with too many missing values
        missing_threshold = 0.5
        df = df.dropna(thresh=int(len(df.columns) * missing_threshold))
        
        # Handle missing values in measurement columns
        measurement_columns = [
            'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum',
            'hauteur_au_sacrum', 'body_length', 'tour_de_poitrine',
            'perimetre_thoracique', 'largeur_poitrine', 'largeur_hanche',
            'largeur_tete', 'longueur_tete', 'longueur_oreille',
            'longueur_cou', 'tour_du_cou', 'longueur_queue'
        ]
        
        for col in measurement_columns:
            if col in df.columns:
                # Fill missing values with median for each breed
                if 'breed' in df.columns:
                    df[col] = df.groupby('breed')[col].transform(
                        lambda x: x.fillna(x.median())
                    )
                else:
                    df[col] = df[col].fillna(df[col].median())
        
        # Remove impossible values (negative measurements)
        for col in measurement_columns:
            if col in df.columns:
                df = df[df[col] >= 0]
        
        logger.info(f"Data cleaned, {len(df)} rows remaining")
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engineered features for better model performance"""
        logger.info("Engineering features...")
        
        # Ratio features (important for morphometry)
        if 'hauteur_au_garrot' in df.columns and 'body_length' in df.columns:
            df['height_to_length_ratio'] = df['hauteur_au_garrot'] / df['body_length']
        
        if 'largeur_poitrine' in df.columns and 'largeur_hanche' in df.columns:
            df['chest_to_hip_ratio'] = df['largeur_poitrine'] / df['largeur_hanche']
        
        if 'tour_de_poitrine' in df.columns and 'hauteur_au_garrot' in df.columns:
            df['girth_to_height_ratio'] = df['tour_de_poitrine'] / df['hauteur_au_garrot']
        
        # Body volume estimation
        if all(col in df.columns for col in ['hauteur_au_garrot', 'body_length', 'largeur_poitrine']):
            df['estimated_volume'] = df['hauteur_au_garrot'] * df['body_length'] * df['largeur_poitrine']
        
        # Head features
        if 'largeur_tete' in df.columns and 'longueur_tete' in df.columns:
            df['head_ratio'] = df['largeur_tete'] / df['longueur_tete']
            df['head_area'] = df['largeur_tete'] * df['longueur_tete']
        
        # Image quality features
        if 'confidence_score' in df.columns:
            df['high_confidence'] = (df['confidence_score'] > 0.8).astype(int)
            df['confidence_squared'] = df['confidence_score'] ** 2
        
        # Age and sex interaction features
        if 'age_months' in df.columns:
            df['age_squared'] = df['age_months'] ** 2
            df['age_log'] = np.log1p(df['age_months'])
            
            if 'sex' in df.columns:
                df['age_sex_interaction'] = df['age_months'] * df['sex'].map({'M': 1, 'F': 0})
        
        # Weight estimation features
        if all(col in df.columns for col in ['hauteur_au_garrot', 'tour_de_poitrine']):
            # Schaeffer's formula approximation
            df['estimated_weight'] = (df['tour_de_poitrine'] ** 2 * df['hauteur_au_garrot']) / 300
        
        logger.info(f"Feature engineering completed, {len(df.columns)} total features")
        return df
    
    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features"""
        logger.info("Encoding categorical features...")
        
        categorical_columns = ['breed', 'sex', 'region']
        
        for col in categorical_columns:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col + '_encoded'] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col + '_encoded'] = self.label_encoders[col].transform(df[col].astype(str))
                
                # One-hot encoding for breed (important feature)
                if col == 'breed':
                    breed_dummies = pd.get_dummies(df[col], prefix='breed')
                    df = pd.concat([df, breed_dummies], axis=1)
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """Remove outliers using specified method"""
        logger.info(f"Removing outliers using {method} method...")
        
        initial_count = len(df)
        
        if method == 'iqr':
            # Remove outliers using IQR method for measurement columns
            measurement_columns = [
                'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum',
                'hauteur_au_sacrum', 'body_length', 'tour_de_poitrine',
                'perimetre_thoracique', 'largeur_poitrine', 'largeur_hanche'
            ]
            
            for col in measurement_columns:
                if col in df.columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        elif method == 'zscore':
            # Remove outliers using Z-score method
            from scipy import stats
            z_scores = np.abs(stats.zscore(df.select_dtypes(include=[np.number])))
            df = df[(z_scores < 3).all(axis=1)]
        
        logger.info(f"Removed {initial_count - len(df)} outliers, {len(df)} rows remaining")
        return df
    
    def train_ensemble_models(self, X: pd.DataFrame, y: pd.DataFrame, 
                            test_size: float = 0.2) -> Dict:
        """
        Train ensemble of models for each measurement
        """
        try:
            logger.info("Training ensemble models...")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Feature selection
            X_train_selected = self.feature_selector.fit_transform(X_train_scaled, y_train.iloc[:, 0])
            X_test_selected = self.feature_selector.transform(X_test_scaled)
            
            results = {}
            
            # Train models for each measurement
            for measurement in y.columns:
                logger.info(f"Training models for {measurement}")
                
                y_train_measurement = y_train[measurement]
                y_test_measurement = y_test[measurement]
                
                # Remove NaN values
                valid_indices = ~y_train_measurement.isna()
                X_train_clean = X_train_selected[valid_indices]
                y_train_clean = y_train_measurement[valid_indices]
                
                measurement_results = {}
                
                # Train each model
                for model_name, model in self.models.items():
                    try:
                        # Hyperparameter tuning
                        if model_name == 'random_forest':
                            param_grid = {
                                'n_estimators': [100, 200],
                                'max_depth': [10, 15, 20],
                                'min_samples_split': [2, 5]
                            }
                        elif model_name == 'gradient_boosting':
                            param_grid = {
                                'n_estimators': [100, 200],
                                'learning_rate': [0.05, 0.1, 0.15],
                                'max_depth': [4, 6, 8]
                            }
                        elif model_name == 'xgboost':
                            param_grid = {
                                'n_estimators': [100, 200],
                                'learning_rate': [0.05, 0.1, 0.15],
                                'max_depth': [4, 6, 8]
                            }
                        
                        # Grid search
                        grid_search = GridSearchCV(
                            model, param_grid, cv=5, scoring='neg_mean_absolute_error',
                            n_jobs=-1
                        )
                        grid_search.fit(X_train_clean, y_train_clean)
                        
                        # Best model
                        best_model = grid_search.best_estimator_
                        
                        # Predictions
                        train_pred = best_model.predict(X_train_clean)
                        test_pred = best_model.predict(X_test_selected)
                        
                        # Metrics
                        train_mae = mean_absolute_error(y_train_clean, train_pred)
                        test_mae = mean_absolute_error(y_test_measurement.dropna(), 
                                                     test_pred[:len(y_test_measurement.dropna())])
                        test_r2 = r2_score(y_test_measurement.dropna(), 
                                         test_pred[:len(y_test_measurement.dropna())])
                        
                        # Cross-validation score
                        cv_scores = cross_val_score(
                            best_model, X_train_clean, y_train_clean,
                            cv=5, scoring='neg_mean_absolute_error'
                        )
                        
                        measurement_results[model_name] = {
                            'model': best_model,
                            'best_params': grid_search.best_params_,
                            'train_mae': train_mae,
                            'test_mae': test_mae,
                            'test_r2': test_r2,
                            'cv_score_mean': -cv_scores.mean(),
                            'cv_score_std': cv_scores.std(),
                            'feature_importance': self._get_feature_importance(best_model, X.columns)
                        }
                        
                        logger.info(f"{model_name} for {measurement} - Test MAE: {test_mae:.2f}, R²: {test_r2:.3f}")
                        
                    except Exception as e:
                        logger.error(f"Training failed for {model_name} on {measurement}: {e}")
                        continue
                
                results[measurement] = measurement_results
            
            # Save models
            self._save_models(results)
            
            # Generate performance report
            self._generate_performance_report(results)
            
            logger.info("Ensemble training completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Ensemble training failed: {e}")
            raise
    
    def train_breed_specific_models(self, X: pd.DataFrame, y: pd.DataFrame) -> Dict:
        """
        Train breed-specific models for improved accuracy
        """
        try:
            logger.info("Training breed-specific models...")
            
            if 'breed' not in X.columns:
                logger.warning("No breed information available for breed-specific training")
                return {}
            
            breed_results = {}
            breeds = X['breed'].unique()
            
            for breed in breeds:
                if pd.isna(breed):
                    continue
                    
                logger.info(f"Training models for breed: {breed}")
                
                # Filter data for this breed
                breed_mask = X['breed'] == breed
                X_breed = X[breed_mask]
                y_breed = y[breed_mask]
                
                if len(X_breed) < 20:  # Minimum samples required
                    logger.warning(f"Not enough samples for breed {breed} ({len(X_breed)})")
                    continue
                
                # Remove breed column for training (avoid data leakage)
                X_breed_clean = X_breed.drop(columns=['breed'], errors='ignore')
                
                # Train ensemble for this breed
                breed_models = self.train_ensemble_models(X_breed_clean, y_breed)
                breed_results[breed] = breed_models
                
                # Save breed-specific model
                self._save_breed_model(breed, breed_models)
            
            logger.info(f"Breed-specific training completed for {len(breed_results)} breeds")
            return breed_results
            
        except Exception as e:
            logger.error(f"Breed-specific training failed: {e}")
            raise
    
    def _get_feature_importance(self, model, feature_names: List[str]) -> Dict:
        """Extract feature importance from trained model"""
        try:
            if hasattr(model, 'feature_importances_'):
                # Tree-based models
                importance_dict = dict(zip(feature_names, model.feature_importances_))
                # Sort by importance
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            elif hasattr(model, 'coef_'):
                # Linear models
                importance_dict = dict(zip(feature_names, np.abs(model.coef_)))
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            else:
                return {}
        except Exception as e:
            logger.error(f"Feature importance extraction failed: {e}")
            return {}
    
    def _save_models(self, results: Dict):
        """Save trained models to disk"""
        try:
            for measurement, models in results.items():
                for model_name, model_data in models.items():
                    model_path = self.model_dir / f"{measurement}_{model_name}_model.joblib"
                    joblib.dump(model_data['model'], model_path)
                    
                    # Save scaler and feature selector
                    scaler_path = self.model_dir / f"{measurement}_scaler.joblib"
                    selector_path = self.model_dir / f"{measurement}_feature_selector.joblib"
                    joblib.dump(self.scaler, scaler_path)
                    joblib.dump(self.feature_selector, selector_path)
            
            logger.info(f"Models saved to {self.model_dir}")
            
        except Exception as e:
            logger.error(f"Model saving failed: {e}")
    
    def _save_breed_model(self, breed: str, models: Dict):
        """Save breed-specific model"""
        try:
            breed_model_path = self.model_dir / f"{breed}_breed_model.joblib"
            joblib.dump(models, breed_model_path)
            logger.info(f"Breed model saved for {breed}")
        except Exception as e:
            logger.error(f"Breed model saving failed for {breed}: {e}")
    
    def _generate_performance_report(self, results: Dict):
        """Generate comprehensive performance report"""
        try:
            report_data = []
            
            for measurement, models in results.items():
                for model_name, metrics in models.items():
                    report_data.append({
                        'measurement': measurement,
                        'model': model_name,
                        'test_mae': metrics['test_mae'],
                        'test_r2': metrics['test_r2'],
                        'cv_score_mean': metrics['cv_score_mean'],
                        'cv_score_std': metrics['cv_score_std']
                    })
            
            report_df = pd.DataFrame(report_data)
            
            # Save report
            report_path = self.model_dir / 'model_performance_report.csv'
            report_df.to_csv(report_path, index=False)
            
            # Generate visualizations
            self._create_performance_visualizations(report_df)
            
            logger.info(f"Performance report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
    
    def _create_performance_visualizations(self, report_df: pd.DataFrame):
        """Create performance visualization plots"""
        try:
            # Performance comparison plot
            plt.figure(figsize=(15, 10))
            
            # R² scores by measurement and model
            plt.subplot(2, 2, 1)
            pivot_r2 = report_df.pivot(index='measurement', columns='model', values='test_r2')
            sns.heatmap(pivot_r2, annot=True, fmt='.3f', cmap='Blues')
            plt.title('R² Scores by Measurement and Model')
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)
            
            # MAE scores by measurement and model
            plt.subplot(2, 2, 2)
            pivot_mae = report_df.pivot(index='measurement', columns='model', values='test_mae')
            sns.heatmap(pivot_mae, annot=True, fmt='.2f', cmap='Reds')
            plt.title('MAE Scores by Measurement and Model')
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)
            
            # Average performance by model
            plt.subplot(2, 2, 3)
            avg_performance = report_df.groupby('model')[['test_r2', 'test_mae']].mean()
            avg_performance['test_r2'].plot(kind='bar', ax=plt.gca())
            plt.title('Average R² Score by Model')
            plt.ylabel('R² Score')
            plt.xticks(rotation=45)
            
            # CV score distribution
            plt.subplot(2, 2, 4)
            sns.boxplot(data=report_df, x='model', y='cv_score_mean')
            plt.title('Cross-Validation Score Distribution')
            plt.ylabel('CV Score (MAE)')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = self.model_dir / 'model_performance_plots.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Performance plots saved to {plot_path}")
            
        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
    
    def load_models(self, measurement: str) -> Dict:
        """Load trained models for a specific measurement"""
        try:
            models = {}
            
            for model_name in self.models.keys():
                model_path = self.model_dir / f"{measurement}_{model_name}_model.joblib"
                if model_path.exists():
                    models[model_name] = joblib.load(model_path)
            
            # Load preprocessing components
            scaler_path = self.model_dir / f"{measurement}_scaler.joblib"
            selector_path = self.model_dir / f"{measurement}_feature_selector.joblib"
            
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            if selector_path.exists():
                self.feature_selector = joblib.load(selector_path)
            
            return models
            
        except Exception as e:
            logger.error(f"Model loading failed for {measurement}: {e}")
            return {}
    
    def predict_with_uncertainty(self, X: pd.DataFrame, measurement: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions with uncertainty quantification using ensemble
        """
        try:
            models = self.load_models(measurement)
            
            if not models:
                raise ValueError(f"No trained models found for {measurement}")
            
            # Preprocess input
            X_scaled = self.scaler.transform(X)
            X_selected = self.feature_selector.transform(X_scaled)
            
            # Get predictions from all models
            predictions = []
            for model_name, model in models.items():
                pred = model.predict(X_selected)
                predictions.append(pred)
            
            # Ensemble prediction (mean)
            ensemble_pred = np.mean(predictions, axis=0)
            
            # Uncertainty estimation (standard deviation across models)
            uncertainty = np.std(predictions, axis=0)
            
            return ensemble_pred, uncertainty
            
        except Exception as e:
            logger.error(f"Prediction failed for {measurement}: {e}")
            return np.array([]), np.array([])


def train_models_from_database():
    """
    Train models using data from Django database
    """
    try:
        # Import Django models
        from django.conf import settings
        import django
        if not settings.configured:
            django.setup()
        
        from measurements.models import Goat, MeasurementSession
        
        # Extract training data
        data = []
        
        for goat in Goat.objects.all():
            for session in goat.measurementsession_set.all():
                row = {
                    'goat_id': goat.id,
                    'breed': goat.breed,
                    'sex': goat.sex,
                    'age_months': (session.date - goat.birth_date).days / 30 if goat.birth_date else None,
                    'weight': session.weight,
                    'confidence_score': session.confidence_score,
                    'hauteur_au_garrot': session.hauteur_au_garrot,
                    'hauteur_au_dos': session.hauteur_au_dos,
                    'hauteur_au_sternum': session.hauteur_au_sternum,
                    'hauteur_au_sacrum': session.hauteur_au_sacrum,
                    'body_length': session.body_length,
                    'tour_de_poitrine': session.tour_de_poitrine,
                    'perimetre_thoracique': session.perimetre_thoracique,
                    'largeur_poitrine': session.largeur_poitrine,
                    'largeur_hanche': session.largeur_hanche,
                    'largeur_tete': session.largeur_tete,
                    'longueur_tete': session.longueur_tete,
                    'longueur_oreille': session.longueur_oreille,
                    'longueur_cou': session.longueur_cou,
                    'tour_du_cou': session.tour_du_cou,
                    'longueur_queue': session.longueur_queue,
                }
                data.append(row)
        
        if not data:
            logger.warning("No data available for training")
            return
        
        df = pd.DataFrame(data)
        logger.info(f"Extracted {len(df)} measurement records for training")
        
        # Initialize trainer
        trainer = AdvancedMLTrainer()
        
        # Prepare data
        X, y = trainer.prepare_training_data(df)
        
        # Train ensemble models
        results = trainer.train_ensemble_models(X, y)
        
        # Train breed-specific models
        breed_results = trainer.train_breed_specific_models(X, y)
        
        logger.info("Model training completed successfully")
        return results, breed_results
        
    except Exception as e:
        logger.error(f"Database training failed: {e}")
        raise


if __name__ == "__main__":
    # Run training from command line
    train_models_from_database()
