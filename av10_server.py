from flask import Flask, request, send_file
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)
# Sentinel Hub OAuth Credentials
CLIENT_ID = ""
CLIENT_SECRET = ""
TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"

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

@app.route("/get-ndvi", methods=["GET"])
def get_ndvi_image():
    access_token = get_access_token()
    
    if not access_token:
        return {"error": "Failed to get access token"}, 500

    polygon = [
        [76.9000, 10.3500],  
        [77.0000, 10.3500],  
        [77.0000, 10.2500],  
        [76.9000, 10.2500],
        [76.9000, 10.3500]  
    ]

    date = request.args.get("date", "2024-03-23")  # Default date

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
                output: { bands: 3, sampleType: "UINT8" }
            };
        }

        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let r, g, b;
            
            if (ndvi < 0) {
                r = 0; g = 0; b = 0;
            } else if (ndvi < 0.5) {
                r = 0; g = Math.floor(255 * (ndvi / 0.5)); b = 0;
            } else {
                let intensity = Math.floor(255 * ((ndvi - 0.5) / 0.5));
                r = 0; g = 128 + intensity; b = 0;
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
        file_path = "ndvi_output.png"
        with open(file_path, "wb") as f:
            f.write(response.content)
        return send_file(file_path, mimetype="image/png")
    else:
        return {"error": f"Failed to fetch NDVI: {response.text}"}, 400

if __name__ == "__main__":
    app.run(debug=True)
