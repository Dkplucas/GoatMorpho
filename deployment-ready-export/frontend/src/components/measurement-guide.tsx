import { Card, CardContent } from "@/components/ui/card";
import { Book, CheckCircle } from "lucide-react";

export default function MeasurementGuide() {
  return (
    <Card className="shadow-md">
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-agri-gray mb-6 flex items-center">
          <Book className="mr-3 text-agri-green" size={24} />
          Measurement Guide
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Measurement Definitions */}
          <div>
            <h3 className="font-semibold text-agri-gray mb-4">Measurement Definitions</h3>
            <div className="space-y-3 text-sm">
              <div className="border-b border-gray-200 pb-2">
                <strong>Hauteur au garrot (WH):</strong> Vertical distance from ground to the highest point of the withers
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Tour de poitrine (HG):</strong> Circumference around the chest behind the front legs
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Body length (BL):</strong> Distance from the point of shoulder to the point of the rump
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Largeur poitrine (CW):</strong> Width of the chest between the front legs
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Longueur oreille (EL):</strong> Length of the ear from base to tip
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Périmètre thoracique (CC):</strong> Circumference around the thoracic region
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Tour abdominal (AG):</strong> Circumference around the abdominal region
              </div>
              <div className="border-b border-gray-200 pb-2">
                <strong>Diamètre biscotal (BD):</strong> Distance between the two hip bones
              </div>
            </div>
          </div>
          
          {/* Best Practices */}
          <div>
            <h3 className="font-semibold text-agri-gray mb-4">Best Practices</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Position goat on level ground in natural standing position</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Ensure good lighting to avoid shadows on measurement points</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Take multiple photos from different angles for verification</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Include a reference object for scale validation</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Verify measurements against manual tape measurements when possible</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Keep the goat calm and still during photo capture</span>
              </div>
              <div className="flex items-start">
                <CheckCircle className="text-agri-success mr-2 mt-0.5 flex-shrink-0" size={16} />
                <span>Capture images from a consistent distance and angle</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
