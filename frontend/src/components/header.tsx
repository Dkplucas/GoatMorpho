import { Microscope, History, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="bg-agri-green shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Microscope className="text-white mr-3" size={24} />
            <h1 className="text-white text-xl font-bold">GoatMeasure Pro</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:text-agri-light hover:bg-white hover:bg-opacity-10"
            >
              <History size={20} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-white hover:text-agri-light hover:bg-white hover:bg-opacity-10"
            >
              <Settings size={20} />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
