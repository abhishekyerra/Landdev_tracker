"""
Weather Service for Columbia, TN 38401
Uses National Weather Service API (no API key required)
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Columbia, TN coordinates
COLUMBIA_LAT = 35.6151
COLUMBIA_LON = -87.0353

class WeatherService:
    """
    Weather service using National Weather Service API
    Free, no API key required, reliable
    """
    
    BASE_URL = "https://api.weather.gov"
    
    def __init__(self):
        self.headers = {
            'User-Agent': '(Land Development Tracker, contact@example.com)',
            'Accept': 'application/json'
        }
    
    def get_current_weather(self) -> Optional[Dict]:
        """Get current weather conditions for Columbia, TN"""
        try:
            # Get grid point data
            point_url = f"{self.BASE_URL}/points/{COLUMBIA_LAT},{COLUMBIA_LON}"
            point_response = requests.get(point_url, headers=self.headers, timeout=10)
            
            if point_response.status_code != 200:
                logger.error(f"Failed to get grid point: {point_response.status_code}")
                return None
            
            point_data = point_response.json()
            
            # Get observation station
            stations_url = point_data['properties']['observationStations']
            stations_response = requests.get(stations_url, headers=self.headers, timeout=10)
            
            if stations_response.status_code != 200:
                return None
            
            stations = stations_response.json()
            if not stations['features']:
                return None
            
            # Get latest observation
            station_id = stations['features'][0]['properties']['stationIdentifier']
            obs_url = f"{self.BASE_URL}/stations/{station_id}/observations/latest"
            obs_response = requests.get(obs_url, headers=self.headers, timeout=10)
            
            if obs_response.status_code != 200:
                return None
            
            obs = obs_response.json()['properties']
            
            # Convert temperature from Celsius to Fahrenheit
            temp_c = obs.get('temperature', {}).get('value')
            temp_f = (temp_c * 9/5) + 32 if temp_c else None
            
            return {
                'temperature': round(temp_f, 1) if temp_f else None,
                'temperature_unit': 'F',
                'conditions': obs.get('textDescription', 'Unknown'),
                'wind_speed': obs.get('windSpeed', {}).get('value'),
                'wind_direction': obs.get('windDirection', {}).get('value'),
                'humidity': obs.get('relativeHumidity', {}).get('value'),
                'timestamp': obs.get('timestamp'),
                'location': 'Columbia, TN'
            }
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
    
    def get_forecast(self) -> Optional[List[Dict]]:
        """Get 7-day forecast for Columbia, TN"""
        try:
            # Get grid point
            point_url = f"{self.BASE_URL}/points/{COLUMBIA_LAT},{COLUMBIA_LON}"
            point_response = requests.get(point_url, headers=self.headers, timeout=10)
            
            if point_response.status_code != 200:
                return None
            
            point_data = point_response.json()
            forecast_url = point_data['properties']['forecast']
            
            # Get forecast
            forecast_response = requests.get(forecast_url, headers=self.headers, timeout=10)
            
            if forecast_response.status_code != 200:
                return None
            
            forecast_data = forecast_response.json()
            periods = forecast_data['properties']['periods']
            
            # Format forecast
            forecast = []
            for period in periods[:14]:  # 7 days (day + night)
                forecast.append({
                    'name': period['name'],
                    'temperature': period['temperature'],
                    'temperature_unit': period['temperatureUnit'],
                    'wind_speed': period['windSpeed'],
                    'wind_direction': period['windDirection'],
                    'short_forecast': period['shortForecast'],
                    'detailed_forecast': period['detailedForecast'],
                    'precipitation_probability': period.get('probabilityOfPrecipitation', {}).get('value', 0),
                    'is_daytime': period['isDaytime']
                })
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return None
    
    def get_work_recommendations(self, forecast: List[Dict]) -> Dict:
        """
        Analyze weather forecast and provide construction work recommendations
        """
        if not forecast:
            return {'recommendations': [], 'alerts': []}
        
        recommendations = []
        alerts = []
        
        # Analyze next 3 days
        for i, period in enumerate(forecast[:6]):  # 3 days
            if not period['is_daytime']:
                continue
            
            day_name = period['name']
            temp = period['temperature']
            precip_prob = period['precipitation_probability']
            short_forecast = period['short_forecast'].lower()
            
            # Rain alerts
            if precip_prob and precip_prob > 50:
                alerts.append({
                    'day': day_name,
                    'type': 'rain',
                    'severity': 'high' if precip_prob > 70 else 'medium',
                    'message': f"{day_name}: {precip_prob}% chance of rain - Plan indoor work"
                })
                recommendations.append({
                    'day': day_name,
                    'category': 'indoor',
                    'tasks': [
                        'Electrical/plumbing inspections',
                        'Utility meter installations',
                        'Review plans and permits',
                        'Equipment maintenance'
                    ]
                })
            
            # Good weather
            elif precip_prob < 30 and 'clear' in short_forecast or 'sunny' in short_forecast:
                recommendations.append({
                    'day': day_name,
                    'category': 'outdoor',
                    'tasks': [
                        'Grading and earthwork',
                        'Concrete work (if temps 40-90°F)',
                        'Asphalt paving',
                        'Utility trenching',
                        'Erosion control maintenance'
                    ]
                })
            
            # Cold weather
            if temp < 40:
                alerts.append({
                    'day': day_name,
                    'type': 'cold',
                    'severity': 'medium',
                    'message': f"{day_name}: {temp}°F - Concrete curing may be affected"
                })
            
            # Hot weather
            if temp > 90:
                alerts.append({
                    'day': day_name,
                    'type': 'heat',
                    'severity': 'medium',
                    'message': f"{day_name}: {temp}°F - Implement heat safety measures for crew"
                })
        
        return {
            'recommendations': recommendations,
            'alerts': alerts
        }
    
    def get_weather_summary(self) -> Dict:
        """Get complete weather summary with current conditions, forecast, and recommendations"""
        current = self.get_current_weather()
        forecast = self.get_forecast()
        recommendations = self.get_work_recommendations(forecast) if forecast else {}
        
        return {
            'current': current,
            'forecast': forecast,
            'recommendations': recommendations.get('recommendations', []),
            'alerts': recommendations.get('alerts', []),
            'location': {
                'city': 'Columbia',
                'state': 'TN',
                'zip': '38401',
                'coordinates': {
                    'lat': COLUMBIA_LAT,
                    'lon': COLUMBIA_LON
                }
            },
            'last_updated': datetime.utcnow().isoformat()
        }

# Create singleton instance
weather_service = WeatherService()
