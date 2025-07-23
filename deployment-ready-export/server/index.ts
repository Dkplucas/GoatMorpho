import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import path from 'path';
import { fileURLToPath } from 'url';
import multer from 'multer';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5000;

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Middleware
app.use(helmet({
  contentSecurityPolicy: false, // Disabled for development
}));
app.use(compression());
app.use(cors({
  origin: process.env.CORS_ORIGIN || ['http://localhost:3000', 'http://localhost:5000'],
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

// Mock measurement data for testing
let measurements: any[] = [];
let nextId = 1;

// API Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Auth routes (mock for now)
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  
  if (username && password) {
    res.json({
      success: true,
      message: 'Login successful',
      user: { id: 1, username, email: `${username}@example.com` },
      token: 'mock-jwt-token'
    });
  } else {
    res.status(400).json({
      success: false,
      message: 'Invalid credentials'
    });
  }
});

app.post('/api/auth/register', (req, res) => {
  const { username, password, email } = req.body;
  
  if (username && password) {
    res.json({
      success: true,
      message: 'Registration successful',
      user: { id: nextId++, username, email: email || `${username}@example.com` },
      token: 'mock-jwt-token'
    });
  } else {
    res.status(400).json({
      success: false,
      message: 'Missing required fields'
    });
  }
});

// Measurement routes
app.get('/api/measurements', (req, res) => {
  res.json({ results: measurements });
});

app.get('/api/measurements/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const measurement = measurements.find(m => m.id === id);
  
  if (measurement) {
    res.json(measurement);
  } else {
    res.status(404).json({ error: 'Measurement not found' });
  }
});

app.post('/api/measurements', upload.single('image'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image file provided' });
    }

    // Create mock measurement with processing simulation
    const measurement = {
      id: nextId++,
      user: 1,
      image: req.file.filename,
      image_url: `/uploads/${req.file.filename}`,
      original_name: req.file.originalname,
      file_size: req.file.size,
      mime_type: req.file.mimetype,
      image_width: 1920,
      image_height: 1080,
      
      // Mock measurements (would be from ML processing)
      wh: 65.2, // Hauteur au garrot
      bh: 60.1, // Hauteur au dos
      sh: 30.5, // Hauteur au sternum
      rh: 62.8, // Hauteur au Sacrum
      
      hg: 85.3, // Tour de poitrine
      cc: 78.9, // Périmètre thoracique
      ag: 95.2, // Tour abdominal
      ng: 45.1, // Tour du cou
      
      bd: 25.4, // Diamètre biscotal
      cw: 28.7, // Largeur poitrine
      rw: 30.2, // Largeur de Hanche
      hw: 15.8, // Largeur de la tête
      
      bl: 75.6, // Body length
      hl: 20.3, // Longueur de la tête
      nl: 35.4, // Longueur du cou
      tl: 25.8, // Longueur de la queue
      
      el: 12.5, // Longueur oreille
      
      confidence_score: 0.92,
      processing_time: 2.3,
      status: 'completed',
      error_message: null,
      measurement_count: 17,
      
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    measurements.push(measurement);
    res.json(measurement);
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});

// Serve uploaded files
app.use('/uploads', express.static(uploadsDir));

// Serve static files in production
if (process.env.NODE_ENV === 'production') {
  const publicDir = path.join(__dirname, 'public');
  app.use(express.static(publicDir));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
  });
}

// Error handling
app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 GoatMeasure Pro server running on port ${PORT}`);
  console.log(`📁 Uploads directory: ${uploadsDir}`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});