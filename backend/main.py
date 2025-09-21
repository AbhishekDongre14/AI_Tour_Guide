from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
from travel_guide import generate_travel_insights_pdf
from trip_planner import plan_trip_with_routes

app = FastAPI(title="Travel Planner API", version="1.0.0")

# Add CORS middleware to allow React frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("guide_pdf", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Pydantic models for request/response
class TripRequest(BaseModel):
    start_point: str
    end_point: str
    transport_mode: str = "DRIVE"

class TripResponse(BaseModel):
    success: bool
    message: str
    data_file: str = None
    map_file: str = None

@app.get("/")
async def root():
    return {"message": "Travel Planner API is running!"}

@app.post("/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest):
    """
    Plan a trip with routes between start and end points
    """
    try:
        # Validate input
        if not request.start_point.strip() or not request.end_point.strip():
            raise HTTPException(status_code=400, detail="Start point and end point are required")
        
        # Call the trip planning function
        result = plan_trip_with_routes(
            request.start_point, 
            request.end_point, 
            request.transport_mode
        )
        
        if result and "data_file" in result:
            return TripResponse(
                success=True,
                message="Trip planned successfully",
                data_file=result["data_file"],
                map_file=result.get("map_file", "routes_map.html")
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to plan trip")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning trip: {str(e)}")

@app.get("/map/{filename}")
async def get_map(filename: str):
    """
    Serve the generated map HTML file
    """
    try:
        if not filename.endswith('.html'):
            filename += '.html'
        
        file_path = filename
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Map file not found")
        
        # Read the HTML content and return it directly
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving map: {str(e)}")

class GuideRequest(BaseModel):
    data_file: str

@app.post("/generate-guide")
async def generate_guide(request: GuideRequest):
    """
    Generate travel guide PDF from route data
    """
    try:
        if not os.path.exists(request.data_file):
            raise HTTPException(status_code=404, detail="Route data file not found")
        
        # Generate unique filename for the PDF
        pdf_filename = f"guide_pdf/Tour_guide_{hash(request.data_file)}.pdf"
        
        # Generate the travel guide PDF
        result = generate_travel_insights_pdf(request.data_file, pdf_filename)
        
        if os.path.exists(pdf_filename):
            return JSONResponse(content={
                "success": True,
                "message": "Travel guide generated successfully",
                "pdf_file": pdf_filename
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to generate travel guide")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating guide: {str(e)}")

@app.get("/download-guide/{filename:path}")
async def download_guide(filename: str):
    """
    Download the generated travel guide PDF
    """
    try:
        # Handle both "guide_pdf/file.pdf" and "file.pdf" formats
        if not filename.startswith("guide_pdf/"):
            clean_filename = filename.replace("guide_pdf/", "")
            file_path = f"guide_pdf/{clean_filename}"
        else:
            file_path = filename
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Guide file not found: {file_path}")
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading guide: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Travel Planner API is operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
