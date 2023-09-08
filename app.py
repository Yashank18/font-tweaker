from flask import Flask, jsonify, request, send_file, make_response
from fontTools.ttLib import TTFont, newTable
import io
import requests
import json
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://font-tweaker-ui.vercel.app"}})


# Helper function to serialize Panose data
def serialize_panose(panose_obj):
    return {
        'bFamilyType': panose_obj.bFamilyType,
        'bSerifStyle': panose_obj.bSerifStyle,
        # Add more properties as needed
    }

# Custom JSON encoder to handle Panose objects
class FontDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

@app.route('/api/get-font-data', methods=['POST'])
def get_font_data():
    try:
        font_url = request.json.get('fontUrl')
        font = TTFont(io.BytesIO(requests.get(font_url).content))
        
        # Extract font data (modify this part to extract specific data you need)
        font_data = {
            'hhea': font['hhea'].__dict__,
            'head': font['head'].__dict__,
            'os2': font['OS/2'].__dict__,
            # Add more attributes as needed
        }

        # Serialize Panose data from the 'OS/2' table
        os2_table = font['OS/2']
        if hasattr(os2_table, 'panose'):
            font_data['os2']['panose'] = serialize_panose(os2_table.panose)

        return json.dumps(font_data, cls=FontDataEncoder), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-font-data', methods=['POST'])
def update_font_data():
    try:
        # Check if 'fontUrl' and 'newData' keys exist in the JSON data
        if 'fontUrl' not in request.json or 'newData' not in request.json:
            return jsonify({'error': 'fontUrl and/or newData missing in JSON data'}), 400
        
        font_url = request.json.get('fontUrl')
        new_data = request.json.get('newData')
        usWinAscent = new_data['usWinAscent']
        usWinDescent = new_data['usWinDescent']

        font_url = request.json.get('fontUrl')
        font = TTFont(io.BytesIO(requests.get(font_url).content))

        if 'OS/2' in font:
            os2 = font['OS/2']
            os2.usWinAscent = usWinAscent
            os2.usWinDescent = usWinDescent

        buffer = io.BytesIO()
        font.save(buffer)

        # Create a Flask HTTP response with the modified font
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = 'attachment; filename=myfont_modified.ttf'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 400

