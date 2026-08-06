import httpx
from langchain_core.tools import tool

@tool
def get_current_weather(location: str) -> str:
    """
    Fetches the real-time current weather for a given location using wttr.in.
    Args:
        location: The name of the city, region, or zip code (e.g., 'New York', 'London', '90210').
    Returns:
        A formatted string describing the current weather conditions, or an error message if the lookup fails.
    """
    try:
        # We use wttr.in with the format=j1 to get a JSON response
        url = f"https://wttr.in/{location}?format=j1"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            
            if response.status_code != 200:
                return f"Weather API Error: Failed to fetch weather for '{location}' (HTTP {response.status_code})."
                
            data = response.json()
            
            if not data or "current_condition" not in data or not data["current_condition"]:
                return f"Weather API Error: Could not parse weather data for '{location}'."
                
            current = data["current_condition"][0]
            
            temp_c = current.get("temp_C", "N/A")
            condition = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "N/A")
            wind_speed = current.get("windspeedKmph", "N/A")
            feels_like = current.get("FeelsLikeC", "N/A")
            
            report = (
                f"Current Weather in {location}:\n"
                f"- Temperature: {temp_c}°C (Feels like {feels_like}°C)\n"
                f"- Condition: {condition}\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind_speed} km/h"
            )
            
            return report
            
    except httpx.RequestError as e:
        return f"Weather API Error: Network request failed - {str(e)}"
    except Exception as e:
        return f"Weather API Error: An unexpected error occurred - {str(e)}"
