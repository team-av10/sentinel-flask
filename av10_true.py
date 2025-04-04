import requests
import json

# Sentinel Hub OAuth Credentials
CLIENT_ID = "5953ff63-7e3d-4f21-aa34-c54394d9de10"
CLIENT_SECRET = "CMylvc8vyIlGiNkMEkGeWNsALCOOXWq1"
TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"

# Step 1: Get Access Token
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ Error getting token: {response.status_code} - {response.text}")
        return None

# Step 2: Fetch True-Color RGB Image using Polygon
def get_truecolor_image(access_token, polygon, date):
    API_URL = "https://services.sentinel-hub.com/api/v1/process"

    payload = {
        "input": {
            "bounds": {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon]
                },
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
            },
            "data": [
                {
                    "type": "S2L2A",  # Sentinel-2 L2A (Surface Reflectance)
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date}T00:00:00Z",
                            "to": f"{date}T23:59:59Z"
                        }
                    }
                }
            ]
        },
        "output": {
            "width": 1024,  # High-resolution image
            "height": 1024,
            "format": "image/png"
        },
        "evalscript": """
        // Sentinel-2 True Color Image (RGB)
        function setup() {
            return {
                input: ["B04", "B03", "B02"], // Red, Green, Blue
                output: { bands: 3, sampleType: "UINT8" }
            };
        }

        function evaluatePixel(sample) {
            return [sample.B04 * 255, sample.B03 * 255, sample.B02 * 255]; // Scale to 0-255
        }
        """
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        # Save the RGB True-Color image as a PNG file
        with open("truecolor_output.png", "wb") as f:
            f.write(response.content)
        print("✅ True-Color satellite image saved as 'truecolor_output.png'")
    else:
        print(f"❌ Error fetching True-Color image: {response.status_code} - {response.text}")

# Run the script
if __name__ == "__main__":
    access_token = get_access_token()
    
    if access_token:
        # Define the Polygon (your provided coordinates)
        polygon = [
             [76.9000, 10.3500],  
    [77.0000, 10.3500],  
    [77.0000, 10.2500],  
    [76.9000, 10.2500],  
    [76.9000, 10.3500]   
   # Closing the polygon
        ]

        date = "2024-03-23"

        get_truecolor_image(access_token, polygon, date)
