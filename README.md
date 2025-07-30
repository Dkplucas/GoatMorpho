# GoatMorpho - Automated Goat Morphometric Analysis

🐐 **GoatMorpho** is a Django-based web application that uses computer vision and AI to automatically extract morphometric measurements from goat images, reducing human errors typically associated with manual tape measurements.

## Features

### 🔍 Automated Measurement Extraction

- **Computer Vision Processing**: Uses MediaPipe and OpenCV for pose detection
- **17 Morphometric Measurements**: Comprehensive body measurements including:
  - **Heights**: Wither, Back, Sternum, Rump
  - **Circumferences**: Heart Girth, Chest, Abdominal, Neck
  - **Widths**: Chest, Hip, Head, Bi-costal Diameter
  - **Lengths**: Body, Head, Neck, Ear, Tail

### 📊 Measurement Management

- **Goat Database**: Store and manage multiple goats with breed, age, sex information
- **Measurement History**: Track measurements over time
- **Confidence Scoring**: AI confidence ratings for each measurement
- **Manual Corrections**: Hybrid AI-assisted + manual correction workflow

### 🎯 Accuracy Features

- **Reference Object Scaling**: Use known objects in images for accurate scaling
- **Keypoint Detection**: Detailed anatomical landmark detection
- **Multiple Measurement Methods**: Automatic, Manual, or Hybrid approaches

## Morphometric Variables Measured

| Variable | Code                 | Description (French)     | Description (English) |
| -------- | -------------------- | ------------------------ | --------------------- |
| WH       | hauteur_au_garrot    | Hauteur au garrot        | Wither Height         |
| BH       | hauteur_au_dos       | Hauteur au dos           | Back Height           |
| SH       | hauteur_au_sternum   | Hauteur au sternum       | Sternum Height        |
| RH       | hauteur_au_sacrum    | Hauteur au Sacrum        | Rump Height           |
| HG       | tour_de_poitrine     | Tour de poitrine         | Heart Girth           |
| CC       | perimetre_thoracique | Périmètre thoracique   | Chest Circumference   |
| AG       | tour_abdominal       | Tour abdominal           | Abdominal Girth       |
| BD       | diametre_biscotal    | Diamètre biscotal       | Bi-costal Diameter    |
| CW       | largeur_poitrine     | Largeur poitrine         | Chest Width           |
| RW       | largeur_hanche       | Largeur de Hanche/bassin | Rump Width            |
| EL       | longueur_oreille     | Longueur oreille         | Ear Length            |
| HL       | longueur_tete        | Longueur de la tête     | Head Length           |
| HW       | largeur_tete         | Largeur de la tête      | Head Width            |
| BL       | body_length          | Body length              | Body Length           |
| NL       | longueur_cou         | Longueur du cou          | Neck Length           |
| NG       | tour_du_cou          | Tour du cou              | Neck Girth            |
| TL       | longueur_queue       | Longueur de la queue     | Tail Length           |

## Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd GoatMorpho
   ```
2. **Create and activate virtual environment**

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure database**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **Create superuser**

   ```bash
   python manage.py createsuperuser
   ```
6. **Run development server**

   ```bash
   python manage.py runserver
   ```
7. **Access the application**

   - Web Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - API Endpoints: http://127.0.0.1:8000/api/

## Usage

### Web Interface

1. **Dashboard**: Overview of your goats and measurements
2. **Upload Image**: Upload goat images for analysis
3. **Admin Panel**: Manage goats, measurements, and review results

### API Endpoints

#### Upload and Process Image

```http
POST /api/upload/
Content-Type: multipart/form-data

{
  "image": <image_file>,
  "goat_id": "<optional_goat_uuid>",
  "goat_name": "<optional_new_goat_name>",
  "reference_length_cm": <optional_float>
}
```

#### List Goats

```http
GET /api/goats/
Authorization: Token <your_token>
```

#### Get Goat Measurements

```http
GET /api/goats/<goat_id>/measurements/
Authorization: Token <your_token>
```

#### Update Measurement

```http
PUT /api/measurements/<measurement_id>/update/
Authorization: Token <your_token>
Content-Type: application/json

{
  "hauteur_au_garrot": 75.5,
  "body_length": 120.2,
  "notes": "Manual correction applied"
}
```

## Computer Vision Pipeline

1. **Image Preprocessing**: Resize, normalize, and prepare image
2. **Pose Detection**: Use MediaPipe to detect anatomical landmarks
3. **Keypoint Extraction**: Extract 2D coordinates of key body points
4. **Scale Calculation**: Determine pixel-to-centimeter ratio
5. **Measurement Calculation**: Calculate distances and proportions
6. **Confidence Assessment**: Evaluate reliability of measurements

## Best Practices for Image Capture

### 📸 Image Quality

- Use high-resolution images (minimum 1024x768)
- Ensure good lighting conditions
- Side view preferred for most measurements
- Entire goat should be visible in frame

### 📏 Measurement Accuracy

- Include a reference object of known length
- Goat should be standing naturally
- Minimize background clutter
- Capture when goat is calm and still

### 🔄 Workflow

1. Capture image following best practices
2. Upload through web interface or API
3. Review AI-generated measurements
4. Make manual corrections if needed
5. Save final measurements

## Technology Stack

- **Backend**: Django 5.2.4, Django REST Framework
- **Computer Vision**: OpenCV, MediaPipe
- **Machine Learning**: TensorFlow (future enhancements)
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Image Processing**: Pillow, scikit-image

## Database Schema

### Models

- **Goat**: Basic goat information (name, breed, age, sex, weight)
- **MorphometricMeasurement**: All 17 measurements with metadata
- **KeyPoint**: Detected anatomical landmarks with coordinates
- **MeasurementSession**: Batch processing sessions

## Development

### Project Structure

```
GoatMorpho/
├── goat_morpho/          # Django project settings
├── measurements/         # Main application
│   ├── models.py        # Database models
│   ├── views.py         # API endpoints and web views
│   ├── cv_processor.py  # Computer vision processing
│   ├── serializers.py   # API serializers
│   └── templates/       # Web interface templates
├── media/               # Uploaded images
├── static/              # Static files
└── requirements.txt     # Python dependencies
```

### Adding New Measurements

1. Add field to `MorphometricMeasurement` model
2. Update `cv_processor.py` calculation logic
3. Add to serializers and admin interface
4. Create migration: `python manage.py makemigrations`

## Future Enhancements

- [ ] 3D pose estimation for circumference measurements
- [ ] Breed-specific measurement standards
- [ ] Batch processing of multiple images
- [ ] Mobile app for field use
- [ ] Integration with livestock management systems
- [ ] Machine learning model training on goat-specific datasets
- [ ] Export to standard formats (CSV, Excel, PDF reports)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use GoatMorpho in your research, please cite:

```
GoatMorpho: Automated Goat Morphometric Analysis System
[DOSSOU KPONGAN LFCY/Animal Breeding and genetics]
[2025]
```

## Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Contact: [dossoukponganfleming@gmail.com]

---

**Note**: This is a research/development tool. Always verify AI measurements with manual checks for critical applications.
