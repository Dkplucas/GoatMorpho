export default function Footer() {
  return (
    <footer className="bg-agri-gray text-white py-8 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-semibold mb-4">GoatMeasure Pro</h3>
            <p className="text-sm text-gray-300">
              Professional morphometric analysis for livestock management
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Support</h4>
            <ul className="text-sm text-gray-300 space-y-2">
              <li>
                <a href="#" className="hover:text-agri-light transition-colors">
                  User Guide
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-agri-light transition-colors">
                  API Documentation
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-agri-light transition-colors">
                  Contact Support
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Version Info</h4>
            <p className="text-sm text-gray-300">Version 1.0.0</p>
            <p className="text-sm text-gray-300">Express Backend Ready</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
