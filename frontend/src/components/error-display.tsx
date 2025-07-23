import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, XCircle } from "lucide-react";

interface ErrorDisplayProps {
  error: string[];
  className?: string;
}

export default function ErrorDisplay({ error, className }: ErrorDisplayProps) {
  // Parse error message to extract individual issues
  const parseErrorMessage = (errorMsg: string) => {
    // Check if it's a JSON error response with multiple errors
    try {
      const parsed = JSON.parse(errorMsg);
      if (parsed.errors && Array.isArray(parsed.errors)) {
        return parsed.errors;
      }
    } catch {
      // Not JSON, treat as single error
    }

    // Check for common quality issues
    if (
      errorMsg.includes("resolution") ||
      errorMsg.includes("blurry") ||
      errorMsg.includes("visible")
    ) {
      return [
        "Image resolution too low for accurate measurements",
        "Goat not fully visible in frame",
        "Image too blurry for feature detection",
      ];
    }

    return [errorMsg];
  };

  const errorList = parseErrorMessage(error);

  return (
    <Card className="shadow-md">
      <CardContent className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="font-semibold text-red-800 mb-4 flex items-center">
            <AlertTriangle className="mr-2" size={20} />
            Image Quality Issues Detected
          </h3>
          <div className="space-y-2 text-sm text-red-700">
            {errorList.map((issue, index) => (
              <div key={index} className="flex items-start">
                <XCircle
                  className="text-red-500 mr-2 mt-0.5 flex-shrink-0"
                  size={16}
                />
                <span>{issue}</span>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button
              onClick={onRetry}
              className="bg-agri-warning hover:bg-orange-600 text-white"
            >
              Upload New Image
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
