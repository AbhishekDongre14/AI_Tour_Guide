import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import requests
import polyline
import folium
import googlemaps
import math
from enum import Enum

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


# ---------- ENUMS ----------
class TravelMode(Enum):
    DRIVE = "DRIVE"
    WALK = "WALK"
    BICYCLE = "BICYCLE"
    TRANSIT = "TRANSIT"
    TWO_WHEELER = "TWO_WHEELER"


# ---------- FARE CALCULATOR ----------
class IntegratedFareCalculator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.fallback_rates = {
            "personal_car": {"per_km": 7},
            "personal_bike": {"per_km": 3}
        }

    def get_comprehensive_fares(self, distance_meters, mode):
        distance_km = distance_meters / 1000
        fares = {}

        if mode == TravelMode.DRIVE:
            fares["personal_car"] = {
                "fare": round(distance_km * self.fallback_rates["personal_car"]["per_km"], 0),
                "currency": "INR"
            }

        elif mode == TravelMode.TWO_WHEELER:
            fares["personal_bike"] = {
                "fare": round(distance_km * self.fallback_rates["personal_bike"]["per_km"], 0),
                "currency": "INR"
            }

        return {
            "fares": fares,
            "distance_km": round(distance_km, 2)
        }


# ---------- ROUTE OPTIMIZER ----------
class EnhancedRouteOptimizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.fare_calculator = IntegratedFareCalculator(api_key)
        self.gmaps = googlemaps.Client(key=api_key)

    def geocode_place(self, place):
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        resp = requests.get(url, params={"address": place, "key": self.api_key, "region": "in"}).json()
        loc = resp["results"][0]["geometry"]["location"]
        return {"lat": loc["lat"], "lng": loc["lng"]}, (loc["lat"], loc["lng"]), resp["results"][0]["formatted_address"]

    def get_all_route_strategies(self, origin, dest, mode):
        all_routes = []

        # Default routes
        all_routes += self._get_routes_google_api(origin, dest, mode.value, strategy="Default")

        # Additional strategies only for DRIVE
        if mode == TravelMode.DRIVE:
            all_routes += self._get_routes_google_api(origin, dest, mode.value, avoid=["highways"], strategy="No Highways")
            all_routes += self._get_routes_google_api(origin, dest, mode.value, avoid=["tolls"], strategy="No Tolls")

        # Remove duplicates
        all_routes = self._remove_duplicates(all_routes)

        # Renumber sequentially
        for i, r in enumerate(all_routes, start=1):
            r["route_number"] = i

        return all_routes

    def _get_routes_google_api(self, origin, dest, mode, avoid=None, strategy="Default"):
        params = {"origin": origin, "destination": dest, "mode": mode.lower(), "alternatives": True, "key": self.api_key}
        if avoid: params["avoid"] = "|".join(avoid)
        resp = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params).json()

        routes = []
        if resp["status"] == "OK":
            for r in resp["routes"]:
                routes.append({
                    "summary": r.get("summary", ""),
                    "distance": r["legs"][0]["distance"]["value"],
                    "duration": r["legs"][0]["duration"]["value"],
                    "distance_text": r["legs"][0]["distance"]["text"],
                    "duration_text": r["legs"][0]["duration"]["text"],
                    "polyline": r["overview_polyline"]["points"],
                    "strategy": strategy
                })
        return routes

    def _remove_duplicates(self, routes):
        seen, unique = set(), []
        for r in routes:
            key = (r["distance"], r["duration"], r["strategy"])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def process_routes_with_fares(self, routes, mode):
        for r in routes:
            r["fare_info"] = self.fare_calculator.get_comprehensive_fares(r["distance"], mode)
        return routes


# ---------- CREATE INTERACTIVE MAP ----------
def create_comprehensive_map(origin, dest, routes, start_place, end_place):
    m = folium.Map(location=[(origin[0] + dest[0]) / 2, (origin[1] + dest[1]) / 2], zoom_start=6)
    folium.Marker(origin, tooltip="Start").add_to(m)
    folium.Marker(dest, tooltip="End").add_to(m)
    colors = ["blue", "red", "green", "purple"]
    for i, r in enumerate(routes):
        if "polyline" in r:
            folium.PolyLine(polyline.decode(r["polyline"]), color=colors[i % len(colors)], weight=5,
                            tooltip=f"Route {r['route_number']}: {r['distance_text']}").add_to(m)
    return m

# ---------- SAVE ROUTE DATA ----------
def save_routes_data(routes, start, end, origin, dest, mode, filename="route_data.json"):
    # Remove polyline before saving JSON
    cleaned_routes = []
    for r in routes:
        r_copy = {k: v for k, v in r.items() if k != "polyline"}
        cleaned_routes.append(r_copy)

    data = {
        "trip": {
            "start": start,
            "end": end,
            "mode": mode,
            "generated_at": datetime.now().isoformat()
        },
        "routes": cleaned_routes
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename


# ---------- MAIN FUNCTION ----------
def plan_trip_with_routes(start_place, end_place, travel_mode):
    if not API_KEY:
        raise Exception("Google API key missing in .env")

    optimizer = EnhancedRouteOptimizer(API_KEY)
    mode_enum = getattr(TravelMode, travel_mode.upper(), TravelMode.DRIVE)

    origin_dict, origin_coords, start_fmt = optimizer.geocode_place(start_place)
    dest_dict, dest_coords, end_fmt = optimizer.geocode_place(end_place)

    routes = optimizer.get_all_route_strategies(start_fmt, end_fmt, mode_enum)
    routes = optimizer.process_routes_with_fares(routes, mode_enum)

    map_file = "routes_map.html"
    data_file = "route_data.json"

    route_map = create_comprehensive_map(origin_coords, dest_coords, routes, start_fmt, end_fmt)
    route_map.save(map_file)
    save_routes_data(routes, start_fmt, end_fmt, origin_coords, dest_coords, mode_enum.value, data_file)

    return {"map_file": map_file, "data_file": data_file, "routes_found": len(routes)}
