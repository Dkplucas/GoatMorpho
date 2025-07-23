import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Ruler,
  ArrowUpDown,
  RotateCcw,
  ArrowLeftRight,
  MoveHorizontal,
  Star,
  BarChart3,
  Download,
  Save,
  Plus,
} from "lucide-react";
import type { Measurement } from "@shared/schema";

interface MeasurementResultsProps {
  measurement: Measurement;
  onNewAnalysis: () => void;
}

export default function MeasurementResults({
  measurement,
  onNewAnalysis,
}: MeasurementResultsProps) {
  const formatMeasurement = (value: number | null) => {
    if (value === null || value === undefined) return "N/A";
    return `${value.toFixed(1)} cm`;
  };

  const handleExportResults = () => {
    // Create CSV content
    const csvContent = [
      ["Measurement", "Value (cm)"],
      ["Hauteur au garrot (WH)", measurement.wh?.toFixed(1) || "N/A"],
      ["Hauteur au dos (BH)", measurement.bh?.toFixed(1) || "N/A"],
      ["Hauteur au sternum (SH)", measurement.sh?.toFixed(1) || "N/A"],
      ["Hauteur au Sacrum (RH)", measurement.rh?.toFixed(1) || "N/A"],
      ["Tour de poitrine (HG)", measurement.hg?.toFixed(1) || "N/A"],
      ["Périmètre thoracique (CC)", measurement.cc?.toFixed(1) || "N/A"],
      ["Tour abdominal (AG)", measurement.ag?.toFixed(1) || "N/A"],
      ["Tour du cou (NG)", measurement.ng?.toFixed(1) || "N/A"],
      ["Diamètre biscotal (BD)", measurement.bd?.toFixed(1) || "N/A"],
      ["Largeur poitrine (CW)", measurement.cw?.toFixed(1) || "N/A"],
      ["Largeur de Hanche (RW)", measurement.rw?.toFixed(1) || "N/A"],
      ["Largeur de la tête (HW)", measurement.hw?.toFixed(1) || "N/A"],
      ["Body length (BL)", measurement.bl?.toFixed(1) || "N/A"],
      ["Longueur de la tête (HL)", measurement.hl?.toFixed(1) || "N/A"],
      ["Longueur du cou (NL)", measurement.nl?.toFixed(1) || "N/A"],
      ["Longueur de la queue (TL)", measurement.tl?.toFixed(1) || "N/A"],
      ["Longueur oreille (EL)", measurement.el?.toFixed(1) || "N/A"],
    ]
      .map((row) => row.join(","))
      .join("\n");

    // Create and download file
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `goat_measurements_${measurement.id}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card className="shadow-md">
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-agri-gray mb-6 flex items-center">
          <Ruler className="mr-3 text-agri-green" size={24} />
          Morphometric Measurements
        </h2>

        {/* Measurement Categories */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {/* Height Measurements */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-4 flex items-center">
              <ArrowUpDown className="mr-2" size={16} />
              Height Measurements
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-green-700">
                  Hauteur au garrot (WH)
                </span>
                <Badge variant="outline" className="text-green-800">
                  {formatMeasurement(measurement.wh)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-green-700">
                  Hauteur au dos (BH)
                </span>
                <Badge variant="outline" className="text-green-800">
                  {formatMeasurement(measurement.bh)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-green-700">
                  Hauteur au sternum (SH)
                </span>
                <Badge variant="outline" className="text-green-800">
                  {formatMeasurement(measurement.sh)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-green-700">
                  Hauteur au Sacrum (RH)
                </span>
                <Badge variant="outline" className="text-green-800">
                  {formatMeasurement(measurement.rh)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Girth Measurements */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800 mb-4 flex items-center">
              <RotateCcw className="mr-2" size={16} />
              Girth Measurements
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700">
                  Tour de poitrine (HG)
                </span>
                <Badge variant="outline" className="text-blue-800">
                  {formatMeasurement(measurement.hg)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700">
                  Périmètre thoracique (CC)
                </span>
                <Badge variant="outline" className="text-blue-800">
                  {formatMeasurement(measurement.cc)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700">
                  Tour abdominal (AG)
                </span>
                <Badge variant="outline" className="text-blue-800">
                  {formatMeasurement(measurement.ag)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-blue-700">Tour du cou (NG)</span>
                <Badge variant="outline" className="text-blue-800">
                  {formatMeasurement(measurement.ng)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Width Measurements */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-800 mb-4 flex items-center">
              <ArrowLeftRight className="mr-2" size={16} />
              Width Measurements
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">
                  Diamètre biscotal (BD)
                </span>
                <Badge variant="outline" className="text-purple-800">
                  {formatMeasurement(measurement.bd)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">
                  Largeur poitrine (CW)
                </span>
                <Badge variant="outline" className="text-purple-800">
                  {formatMeasurement(measurement.cw)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">
                  Largeur de Hanche (RW)
                </span>
                <Badge variant="outline" className="text-purple-800">
                  {formatMeasurement(measurement.rw)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-purple-700">
                  Largeur de la tête (HW)
                </span>
                <Badge variant="outline" className="text-purple-800">
                  {formatMeasurement(measurement.hw)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Length Measurements */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h3 className="font-semibold text-orange-800 mb-4 flex items-center">
              <MoveHorizontal className="mr-2" size={16} />
              Length Measurements
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">
                  Body length (BL)
                </span>
                <Badge variant="outline" className="text-orange-800">
                  {formatMeasurement(measurement.bl)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">
                  Longueur de la tête (HL)
                </span>
                <Badge variant="outline" className="text-orange-800">
                  {formatMeasurement(measurement.hl)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">
                  Longueur du cou (NL)
                </span>
                <Badge variant="outline" className="text-orange-800">
                  {formatMeasurement(measurement.nl)}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-orange-700">
                  Longueur de la queue (TL)
                </span>
                <Badge variant="outline" className="text-orange-800">
                  {formatMeasurement(measurement.tl)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Special Measurements */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-800 mb-4 flex items-center">
              <Star className="mr-2" size={16} />
              Special Measurements
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-yellow-700">
                  Longueur oreille (EL)
                </span>
                <Badge variant="outline" className="text-yellow-800">
                  {formatMeasurement(measurement.el)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Analysis Summary */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
              <BarChart3 className="mr-2" size={16} />
              Analysis Summary
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">
                  Total Measurements
                </span>
                <Badge variant="outline" className="text-gray-800">
                  17
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Confidence Score</span>
                <Badge variant="outline" className="text-agri-success">
                  {measurement.confidence_score
                    ? `${(measurement.confidence_score * 100).toFixed(1)}%`
                    : "N/A"}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">Processing Time</span>
                <Badge variant="outline" className="text-gray-800">
                  {measurement.processing_time
                    ? `${measurement.processing_time.toFixed(1)}s`
                    : "N/A"}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-wrap gap-4">
          <Button
            onClick={handleExportResults}
            className="bg-agri-green hover:bg-green-700 text-white flex items-center"
          >
            <Download className="mr-2" size={16} />
            Export Results
          </Button>
          <Button
            variant="outline"
            onClick={onNewAnalysis}
            className="flex items-center"
          >
            <Plus className="mr-2" size={16} />
            New Analysis
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
