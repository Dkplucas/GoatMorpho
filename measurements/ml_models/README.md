# ML Models Directory

This directory contains trained machine learning models for GoatMorpho AI/ML features.

## Model Types

### 1. Ensemble Models
- **Random Forest**: Tree-based ensemble for robust predictions
- **Gradient Boosting**: Sequential ensemble for high accuracy
- **XGBoost**: Optimized gradient boosting for performance

### 2. Breed-Specific Models
- Models trained on specific goat breeds for improved accuracy
- Automatically loaded when breed information is available

### 3. User-Specific Models
- Personalized models trained on individual user's data
- Activated when sufficient user data is available (>10 measurements)

## Model Files

### General Models
- `{measurement}_{algorithm}_model.joblib`: Trained model files
- `{measurement}_scaler.joblib`: Feature scaling transformers
- `{measurement}_feature_selector.joblib`: Feature selection transformers

### Breed-Specific Models
- `{breed}_breed_model.joblib`: Complete breed-specific model ensemble

### User-Specific Models
- `user_{user_id}_model.joblib`: Personalized user models

## Performance Reports
- `model_performance_report.csv`: Detailed performance metrics
- `model_performance_plots.png`: Visualization of model performance

## Usage

Models are automatically loaded and used by the AI/ML features:

1. **Advanced Image Processing**: Uses ensemble models for uncertainty quantification
2. **Measurement Prediction**: Predicts missing measurements from partial data
3. **Trend Analysis**: Analyzes growth patterns and anomalies
4. **AI Insights**: Generates recommendations and insights

## Training

Train new models using the management command:

```bash
python manage.py train_advanced_models --breed-specific --min-samples 50
```

## Model Versioning

Models are versioned by training date and performance metrics. Best performing models are automatically selected for production use.
