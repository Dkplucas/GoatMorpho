import { useState, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, CloudUpload, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

interface ImageUploadProps {
  onUploadSuccess: (measurementId: number) => void;
  onUploadError: (error: string) => void;
}

export default function ImageUpload({ onUploadSuccess, onUploadError }: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileSelect = async (file: File) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      onUploadError("Please select an image file");
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      onUploadError("File size must be less than 10MB");
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('/api/measurements/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Upload failed');
      }

      const result = await response.json();
      onUploadSuccess(result.id);
      
      toast({
        title: "Upload successful",
        description: "Your image has been uploaded and analysis has started.",
      });
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError(error instanceof Error ? error.message : 'Upload failed');
      
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : 'Upload failed',
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  return (
    <Card className="shadow-md">
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-agri-gray mb-6 flex items-center">
          <Upload className="mr-3 text-agri-green" size={24} />
          Upload Goat Image
        </h2>
        
        {/* Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-agri-green bg-green-50'
              : 'border-agri-light bg-gray-50 hover:bg-gray-100'
          } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={!isUploading ? handleClick : undefined}
        >
          <CloudUpload className="mx-auto text-agri-green mb-4" size={64} />
          <p className="text-lg text-agri-gray mb-2">
            {isUploading ? 'Uploading...' : 'Drop your goat image here or click to browse'}
          </p>
          <p className="text-sm text-gray-500">
            Supported formats: JPG, PNG, WebP (Max 10MB)
          </p>
          
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept="image/*"
            onChange={handleFileInputChange}
            disabled={isUploading}
          />
        </div>
        
        {/* Image Quality Requirements */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2 flex items-center">
            <Info className="mr-2" size={16} />
            Image Quality Requirements
          </h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Goat should be in profile (side view) position</li>
            <li>• Clear, well-lit image with minimal shadows</li>
            <li>• Entire goat visible in frame</li>
            <li>• Minimum resolution: 1024x768 pixels</li>
            <li>• Avoid blurry or heavily distorted images</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
