import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Eye, Play, RotateCcw } from "lucide-react";
import type { Measurement } from "@shared/schema";

interface ImagePreviewProps {
  measurement: Measurement | undefined;
  isLoading: boolean;
  onReset: () => void;
}

export default function ImagePreview({ measurement, isLoading, onReset }: ImagePreviewProps) {
  if (isLoading || !measurement) {
    return (
      <Card className="shadow-md">
        <CardContent className="p-6">
          <h2 className="text-2xl font-bold text-agri-gray mb-6 flex items-center">
            <Eye className="mr-3 text-agri-green" size={24} />
            Image Preview & Analysis
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-agri-gray mb-3">Original Image</h3>
              <Skeleton className="w-full h-96 rounded-lg" />
            </div>
            
            <div>
              <h3 className="font-semibold text-agri-gray mb-3">Measurement Overlay</h3>
              <Skeleton className="w-full h-96 rounded-lg" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const imageUrl = `/api/uploads/${measurement.filename}`;
  const isProcessing = measurement.status === "processing";

  return (
    <Card className="shadow-md">
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-agri-gray mb-6 flex items-center">
          <Eye className="mr-3 text-agri-green" size={24} />
          Image Preview & Analysis
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Original Image */}
          <div>
            <h3 className="font-semibold text-agri-gray mb-3">Original Image</h3>
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <img 
                src={imageUrl} 
                alt={measurement.originalName}
                className="w-full h-auto max-h-96 object-contain rounded-lg"
              />
            </div>
          </div>
          
          {/* Processed Image with Measurements */}
          <div>
            <h3 className="font-semibold text-agri-gray mb-3">Measurement Overlay</h3>
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 relative">
              <img 
                src={imageUrl} 
                alt="Processed goat image with measurements"
                className="w-full h-auto max-h-96 object-contain rounded-lg"
              />
              
              {/* Processing overlay */}
              {isProcessing && (
                <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
                  <div className="bg-white p-4 rounded-lg text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-agri-green mx-auto mb-2"></div>
                    <p className="text-sm text-agri-gray">Processing measurements...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Processing Progress */}
        {isProcessing && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800 mb-2">Analysis in Progress</h3>
            <Progress value={undefined} className="mb-2" />
            <p className="text-sm text-blue-700">
              Analyzing goat morphometric features and extracting measurements...
            </p>
          </div>
        )}
        
        {/* Analysis Controls */}
        <div className="mt-6 flex flex-wrap gap-4">
          <Button
            variant="outline"
            onClick={onReset}
            className="flex items-center"
          >
            <RotateCcw className="mr-2" size={16} />
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
