from flask import Flask, jsonify, request, send_file
from fontTools.ttLib import TTFont
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
        font_url = request.json.get('fontUrl')
        new_data = request.json.get('newData')
        font = TTFont(io.BytesIO(requests.get(font_url).content))
        
        # Update font data (modify this part to update specific data)
        # For example, you can update the 'ascender' and 'descender' attributes in the 'head' table
        font['head'].ascender = new_data['head']['ascender']
        font['head'].descender = new_data['head']['descender']
        
        # Save the modified font to a new file
        updated_font_file = io.BytesIO()
        font.save(updated_font_file)
        updated_font_file.seek(0)

        return send_file(updated_font_file, as_attachment=True, download_name='updated_font.ttf'), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
