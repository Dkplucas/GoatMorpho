import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Header from "@/components/header";
import Footer from "@/components/footer";
import ImageUpload from "@/components/image-upload";
import ImagePreview from "@/components/image-preview";
import MeasurementResults from "@/components/measurement-results";
import MeasurementGuide from "@/components/measurement-guide";
import ErrorDisplay from "@/components/error-display";
import type { Measurement } from "@/shared/schema";
export default function Home() {
  const [currentMeasurementId, setCurrentMeasurementId] = useState<
    number | null
  >(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { data: measurement, isLoading: isMeasurementLoading } = useQuery({
    queryKey: ["/api/measurements", currentMeasurementId],
    enabled: currentMeasurementId !== null,
    refetchInterval: (query) => {
      // Keep refetching if status is still processing
      const measurementData = query.state.data as Measurement;
      return measurementData?.status === "processing" ? 2000 : false;
    },
  });
  const handleUploadSuccess = (measurementId: number) => {
    setCurrentMeasurementId(measurementId);
    setUploadError(null);
  };
  const handleUploadError = (error: string) => {
    setUploadError(error);
    setCurrentMeasurementId(null);
  };
  const handleReset = () => {
    setCurrentMeasurementId(null);
    setUploadError(null);
  };
  const handleNewAnalysis = () => {
    setCurrentMeasurementId(null);
    setUploadError(null);
  };
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Section */}
        <section className="mb-8">
          <ImageUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </section>
        {/* Error Display */}
        {uploadError && (
          <section className="mb-8">
            <div className="alert alert-danger">{uploadError as string}</div>
          </section>
        )}
        {/* Preview Section */}
        {currentMeasurementId && (
          <section className="mb-8">
            <ImagePreview
              measurement={measurement as Measurement}
              isLoading={isMeasurementLoading}
              onReset={handleReset}
            />
          </section>
        )}
        {/* Results Section */}
        {measurement && (measurement as Measurement).status === "completed" && (
          <section className="mb-8">
            <MeasurementResults
              measurement={measurement as Measurement}
              onNewAnalysis={handleNewAnalysis}
            />
          </section>
        )}
        {/* Guide Section */}
        <section>
          <MeasurementGuide />
        </section>
      </main>
      <Footer />
    </div>
  );
}
