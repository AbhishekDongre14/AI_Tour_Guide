import os
import json
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from reportlab.lib.utils import simpleSplit

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def generate_travel_insights_pdf(json_file_path: str, output_pdf="travel_insights.pdf"):
    """
    Generate a travel guide PDF using Gemini API based on JSON file input.
    Direct PDF generation using ReportLab (no HTML needed).
    """
    # Load route data from JSON file
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    with open(json_file_path, "r", encoding="utf-8") as f:
        route_data = json.load(f)

    # Get trip info
    trip_info = route_data["trip"]
    routes = route_data["routes"]

    # Pick the first route as default for guide
    main_route = routes[0]
    strategy = main_route["strategy"]
    distance = main_route["distance_text"]
    duration = main_route["duration_text"]
    fare = list(main_route["fare_info"]["fares"].values())[0]["fare"]

    # Prepare prompt for Gemini API
    prompt = f"""
You are an experienced travel guide for India. Create a comprehensive travel guide for a road trip.
The selected route is {strategy} covering {distance} in {duration} with estimated fuel cost of ₹{fare}.

Start: {trip_info['start']}
End: {trip_info['end']}

Please provide:
1. Route Overview
2. Major Stopovers
3. Cultural Highlights
4. Food Recommendations
5. Safety & Travel Tips
6. Seasonal Considerations
7. Budget Breakdown
8. Photography Spots

Make it engaging, structured, and easy to read with short paragraphs. Use emojis to make it fun.
"""

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={API_KEY}"
    response = requests.post(url, json={
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    })

    data = response.json()
    if "error" in data:
        raise Exception(f"API Error: {data['error']['message']}")

    # After calling Gemini API
    insights = data["candidates"][0]["content"]["parts"][0]["text"]

    # Create PDF with wrapping + page breaks
    create_pdf_with_wrapping(output_pdf, "🤖 AI-Generated Travel Insights", insights)
    return output_pdf


def create_pdf_with_wrapping(output_pdf, title, content):
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    margin = 50
    max_width = width - 2 * margin
    y = height - 80
    line_height = 16

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - 50, title)

    # Text
    c.setFont("Helvetica", 11)

    for line in content.split("\n"):
        # Wrap line into multiple if needed
        wrapped_lines = simpleSplit(line, "Helvetica", 11, max_width)
        for wline in wrapped_lines:
            if y < margin:  # New page if space finished
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - margin
            c.drawString(margin, y, wline)
            y -= line_height

    c.save()
