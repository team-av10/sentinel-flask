import requests
import json

# Sentinel Hub OAuth Credentials
CLIENT_ID = ""
CLIENT_SECRET = ""
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

# Step 2: Fetch NDVI Image using Polygon
def get_ndvi_image(access_token, polygon, date):
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
                    "type": "S2L2A",
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
            "width": 512,
            "height": 512,
            "format": "image/png"
        },
        "evalscript": """
        function setup() {
            return {
                input: ["B08", "B04"],
                output: { bands: 3, sampleType: "UINT8" } // Ensure RGB output
            };
        }

        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            
    // Apply color mapping
    let r, g, b;

    if (ndvi < 0) {
        // Black for non-vegetation areas (NDVI < 0)
        r = 0;
        g = 0;
        b = 0;
    } else if (ndvi < 0.5) {
        // Dark green for lower vegetation levels
        r = 0;
        g = Math.floor(255 * (ndvi / 0.5)); // Gradually increase green
        b = 0;
    } else {
        // Different shades of green for 0.5 to 1.0
        let intensity = Math.floor(255 * ((ndvi - 0.5) / 0.5)); // Scale from 0-255

        r = 0;
        g = 128 + intensity; // Shades from dark to bright green
        b = 0;
    }

    return [r, g, b];
    }
        """
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        # Save the NDVI image as a PNG file
        with open("ndvi_output.png", "wb") as f:
            f.write(response.content)
        print("✅ NDVI image saved as 'ndvi_output.png'")
    else:
        print(f"❌ Error fetching NDVI: {response.status_code} - {response.text}")

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
        ]

        date = "2024-03-23"

        get_ndvi_image(access_token, polygon, date)
