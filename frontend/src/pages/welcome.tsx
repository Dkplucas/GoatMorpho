import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Microscope, 
  Upload, 
  BarChart3, 
  Download, 
  CheckCircle,
  Star,
  Users,
  Shield,
  Zap,
  ArrowRight
} from "lucide-react";

interface WelcomePageProps {
  onGetStarted: () => void;
}

export default function WelcomePage({ onGetStarted }: WelcomePageProps) {
  const features = [
    {
      icon: <Upload className="text-agri-green" size={24} />,
      title: "Easy Image Upload",
      description: "Drag & drop goat images or browse from your device. Supports JPG, PNG, and WebP formats up to 10MB."
    },
    {
      icon: <BarChart3 className="text-blue-600" size={24} />,
      title: "17 Precise Measurements",
      description: "Comprehensive morphometric analysis including height, girth, width, and length measurements."
    },
    {
      icon: <Zap className="text-yellow-600" size={24} />,
      title: "Real-time Processing",
      description: "Advanced computer vision algorithms process your images in seconds with live status updates."
    },
    {
      icon: <Download className="text-purple-600" size={24} />,
      title: "Export Results",
      description: "Download measurement data in CSV format for further analysis and record keeping."
    },
    {
      icon: <Shield className="text-green-600" size={24} />,
      title: "Quality Validation",
      description: "Automatic image quality checks ensure accurate measurements and reliable results."
    },
    {
      icon: <Users className="text-indigo-600" size={24} />,
      title: "Professional Tools",
      description: "Built for livestock professionals, researchers, and farmers requiring precise measurements."
    }
  ];

  const measurements = [
    "Hauteur au garrot (WH)", "Hauteur au dos (BH)", "Hauteur au sternum (SH)",
    "Tour de poitrine (HG)", "Périmètre thoracique (CC)", "Tour abdominal (AG)",
    "Diamètre biscotal (BD)", "Largeur poitrine (CW)", "Body length (BL)",
    "Longueur de la tête (HL)", "Longueur oreille (EL)", "Longueur du cou (NL)"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Hero Section */}
      <section className="bg-agri-green text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-white bg-opacity-20 p-4 rounded-full">
              <Microscope size={48} />
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-6">GoatMeasure Pro</h1>
          <p className="text-xl mb-8 max-w-3xl mx-auto leading-relaxed">
            Revolutionary automated morphometric analysis for goats using advanced computer vision technology. 
            Eliminate manual measurement errors and save time with precision digital analysis.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              onClick={onGetStarted}
              size="lg"
              className="bg-white text-agri-green hover:bg-gray-100 font-semibold px-8 py-3"
            >
              Get Started
              <ArrowRight className="ml-2" size={20} />
            </Button>
            <Button 
              variant="outline"
              size="lg"
              className="border-white text-white hover:bg-white hover:text-agri-green font-semibold px-8 py-3"
            >
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-agri-gray mb-4">Why Choose GoatMeasure Pro?</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our platform combines cutting-edge technology with agricultural expertise to deliver 
              the most accurate and efficient morphometric analysis solution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="shadow-lg hover:shadow-xl transition-shadow">
                <CardContent className="p-6 text-center">
                  <div className="flex justify-center mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-agri-gray mb-3">{feature.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Measurements Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-agri-gray mb-4">Comprehensive Measurements</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Extract 17 different morphometric measurements automatically from a single image
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {measurements.map((measurement, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 rounded-lg bg-green-50 border border-green-200">
                  <CheckCircle className="text-agri-success flex-shrink-0" size={16} />
                  <span className="text-sm font-medium text-agri-gray">{measurement}</span>
                </div>
              ))}
              <div className="flex items-center space-x-3 p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                <Star className="text-yellow-600 flex-shrink-0" size={16} />
                <span className="text-sm font-medium text-agri-gray">And 5 more measurements...</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-agri-gray mb-4">How It Works</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Simple, fast, and accurate - get professional measurements in just three steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-agri-green text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                1
              </div>
              <h3 className="text-xl font-semibold text-agri-gray mb-4">Upload Image</h3>
              <p className="text-gray-600">
                Upload a clear side-view image of your goat. Our system accepts multiple formats and validates image quality.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-agri-green text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                2
              </div>
              <h3 className="text-xl font-semibold text-agri-gray mb-4">AI Analysis</h3>
              <p className="text-gray-600">
                Advanced computer vision algorithms analyze the image and extract 17 different morphometric measurements automatically.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-agri-green text-white w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                3
              </div>
              <h3 className="text-xl font-semibold text-agri-gray mb-4">Get Results</h3>
              <p className="text-gray-600">
                View detailed measurements with confidence scores and export data in CSV format for your records.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-agri-green text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to Get Started?</h2>
          <p className="text-xl mb-8 leading-relaxed">
            Join professionals worldwide who trust GoatMeasure Pro for accurate, 
            efficient morphometric analysis. No manual measurements needed.
          </p>
          <Button 
            onClick={onGetStarted}
            size="lg"
            className="bg-white text-agri-green hover:bg-gray-100 font-semibold px-12 py-4 text-lg"
          >
            Start Measuring Now
            <ArrowRight className="ml-2" size={20} />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-agri-gray text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <Microscope className="mr-3" size={24} />
                <h3 className="text-xl font-bold">GoatMeasure Pro</h3>
              </div>
              <p className="text-gray-300 mb-4">
                Professional morphometric analysis for livestock management using advanced computer vision technology.
              </p>
              <div className="flex space-x-2">
                <Badge variant="outline" className="text-gray-300 border-gray-300">Version 1.0.0</Badge>
                <Badge variant="outline" className="text-gray-300 border-gray-300">AI-Powered</Badge>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Features</h4>
              <ul className="text-sm text-gray-300 space-y-2">
                <li>17 Measurements</li>
                <li>Real-time Processing</li>
                <li>Quality Validation</li>
                <li>CSV Export</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="text-sm text-gray-300 space-y-2">
                <li>User Guide</li>
                <li>API Documentation</li>
                <li>Contact Support</li>
                <li>FAQ</li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}