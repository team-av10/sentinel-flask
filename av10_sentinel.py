import requests

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

# Step 2: Fetch NDVI Image using Bounding Box
def get_ndvi_image(access_token, bbox, date):
    API_URL = "https://services.sentinel-hub.com/api/v1/process"

    payload = {
        "input": {
            "bounds": {
                "bbox": bbox,
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
        input: [\"B08\", \"B04\"],
        output: { bands: 3, sampleType: \"UINT8\" } // Ensure RGB output
    };
}

function evaluatePixel(sample) {
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    
    // Normalize NDVI (-1 to 1) → (0 to 1)
    let normalized = (ndvi + 1) / 2;

    // Apply colormap (from blue → brown → green)
    let r = Math.min(255, Math.max(0, 255 * (1 - normalized) * 2));
    let g = Math.min(255, Math.max(0, 255 * normalized));
    let b = Math.min(255, Math.max(0, 255 * (1 - normalized) * 2));

    return [r, g, b];
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
        # Define a bounding box (minLon, minLat, maxLon, maxLat)
        bbox = [77.5900, 12.9700, 77.6000, 12.9800]  # Example: Bangalore, India
        date = "2024-03-23"

        get_ndvi_image(access_token, bbox, date)
