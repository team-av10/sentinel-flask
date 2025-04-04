import requests
import numpy as np
import cv2

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
        input: [\"B08\", \"B04\"],
        output: { bands: 3, sampleType: \"UINT8\" } // Change to 3 bands for RGB output
    };
}

function evaluatePixel(sample) {
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    
    // Convert NDVI (-1 to 1) → (0 to 255)
    let ndvi_scaled = Math.round((ndvi + 1) / 2 * 255);

    // Apply color mapping (Jet colormap)
    let r = 0, g = 0, b = 0;
    
    if (ndvi_scaled < 85) {
        // Low NDVI (brown to red)
        r = 139; g = 69; b = 19;
    } else if (ndvi_scaled < 170) {
        // Moderate NDVI (yellow-green)
        r = 173; g = 255; b = 47;
    } else {
        // High NDVI (dark green)
        r = 34; g = 139; b = 34;
    }

    return [r, g, b];
}"""
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        # Save the raw NDVI image
        with open("ndvi_raw.tiff", "wb") as f:
            f.write(response.content)
        print("✅ NDVI raw image saved as 'ndvi_raw.tiff'")

        # Convert to colorized image
        colorize_ndvi("ndvi_raw.tiff", "ndvi_colorized.png")
    else:
        print(f"❌ Error fetching NDVI: {response.status_code} - {response.text}")

# Step 3: Colorize NDVI Image
def colorize_ndvi(input_path, output_path):
    # Load NDVI image (assuming float32 TIFF format)
    ndvi = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

    if ndvi is None:
        print("⚠️ Failed to load NDVI image. Check the file format.")
        return

    # Normalize NDVI values to range 0-255 for visualization
    ndvi = np.nan_to_num(ndvi)  # Replace NaNs with zero
    ndvi = np.clip(ndvi, -1, 1)  # Limit range to valid NDVI values
    ndvi_normalized = ((ndvi + 1) / 2 * 255).astype(np.uint8)

    # Apply color mapping
    ndvi_colormap = cv2.applyColorMap(ndvi_normalized, cv2.COLORMAP_JET)

    # Save the colorized NDVI image
    cv2.imwrite(output_path, ndvi_colormap)
    print(f"✅ Colorized NDVI image saved as '{output_path}'")

# Run the script
if __name__ == "__main__":
    access_token = get_access_token()
    
    if access_token:
        # Define the polygon coordinates
        polygon = [
            [76.8131, 11.0845],  # Northwest
            [77.0369, 11.0845],  # Northeast
            [77.0369, 10.8760],  # Southeast
            [76.8131, 10.8760],  # Southwest
            [76.8131, 11.0845]   # Closing the polygon
        ]
        date = "2024-03-23"

        get_ndvi_image(access_token, polygon, date)
