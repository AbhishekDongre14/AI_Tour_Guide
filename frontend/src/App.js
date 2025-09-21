import React, { useState } from 'react';
import { MapPin, Navigation, FileDown, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const TravelPlanner = () => {
  const [formData, setFormData] = useState({
    start_point: '',
    end_point: '',
    transport_mode: 'DRIVE'
  });
  
  const [isPlanning, setIsPlanning] = useState(false);
  const [isGeneratingGuide, setIsGeneratingGuide] = useState(false);
  const [tripData, setTripData] = useState(null);
  const [mapUrl, setMapUrl] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(null);
    setSuccess(null);
  };

  const planTrip = async () => {
    if (!formData.start_point.trim() || !formData.end_point.trim()) {
      setError('Please enter both start point and destination');
      return;
    }

    setIsPlanning(true);
    setError(null);
    setTripData(null);
    setMapUrl(null);
    setPdfFile(null);

    try {
      const response = await fetch(`${API_BASE_URL}/plan-trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to plan trip');
      }

      setTripData(result);
      setMapUrl(`${API_BASE_URL}/map/${result.map_file}`);
      setSuccess('Trip planned successfully! Check out your route on the map below.');
    } catch (err) {
      setError(err.message || 'Error planning trip. Please try again.');
    } finally {
      setIsPlanning(false);
    }
  };

  const generateGuide = async () => {
    if (!tripData?.data_file) {
      setError('No trip data available. Please plan a trip first.');
      return;
    }

    setIsGeneratingGuide(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/generate-guide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data_file: tripData.data_file }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to generate guide');
      }

      setPdfFile(result.pdf_file);
      setSuccess('Travel guide generated successfully! You can now download it.');
    } catch (err) {
      setError(err.message || 'Error generating travel guide. Please try again.');
    } finally {
      setIsGeneratingGuide(false);
    }
  };

  const downloadGuide = () => {
    if (pdfFile) {
      const link = document.createElement('a');
      // Remove duplicate guide_pdf/ from the path if it exists
      const cleanPath = pdfFile.replace('guide_pdf/', '');
      link.href = `${API_BASE_URL}/download-guide/guide_pdf/${cleanPath}`;
      link.download = 'Travel_Guide.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4 flex items-center justify-center gap-3">
            <Navigation className="text-blue-600" size={40} />
            Travel Planner
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Plan your perfect trip with detailed routes and get a personalized travel guide PDF
          </p>
        </div>

        {/* Main Form */}
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">Plan Your Journey</h2>
          
          <div className="space-y-6">
            {/* Start Point */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="inline mr-2" size={16} />
                Starting Location
              </label>
              <input
                type="text"
                name="start_point"
                value={formData.start_point}
                onChange={handleInputChange}
                placeholder="Enter your current location"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              />
            </div>

            {/* End Point */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="inline mr-2" size={16} />
                Destination
              </label>
              <input
                type="text"
                name="end_point"
                value={formData.end_point}
                onChange={handleInputChange}
                placeholder="Enter your destination"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              />
            </div>

            {/* Transport Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Transportation Mode
              </label>
              <select
                name="transport_mode"
                value={formData.transport_mode}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="DRIVE">Driving</option>
                <option value="WALK">Walking</option>
                <option value="TRANSIT">Public Transit</option>
                <option value="BICYCLE">Cycling</option>
              </select>
            </div>

            {/* Plan Trip Button */}
            <button
              onClick={planTrip}
              disabled={isPlanning}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              {isPlanning ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Planning Trip...
                </>
              ) : (
                <>
                  <Navigation size={20} />
                  Plan My Trip
                </>
              )}
            </button>
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="max-w-2xl mx-auto mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
            <CheckCircle className="text-green-600" size={20} />
            <p className="text-green-800">{success}</p>
          </div>
        )}

        {error && (
          <div className="max-w-2xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="text-red-600" size={20} />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Map Display */}
        {mapUrl && (
          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800">Your Route</h3>
            </div>
            <div className="h-96">
              <iframe
                src={mapUrl}
                className="w-full h-full border-0"
                title="Route Map"
              />
            </div>
          </div>
        )}

        {/* Guide Generation Section */}
        {tripData && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-semibold text-gray-800 mb-4">Generate Travel Guide</h3>
            <p className="text-gray-600 mb-6">
              Get a detailed PDF travel guide with insights about your route, including attractions, 
              restaurants, and useful travel information.
            </p>
            
            <div className="flex gap-4">
              <button
                onClick={generateGuide}
                disabled={isGeneratingGuide}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
              >
                {isGeneratingGuide ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Generating Guide...
                  </>
                ) : (
                  <>
                    <FileDown size={20} />
                    Generate Travel Guide
                  </>
                )}
              </button>

              {pdfFile && (
                <button
                  onClick={downloadGuide}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center gap-2"
                >
                  <FileDown size={20} />
                  Download PDF
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TravelPlanner;
