from flask import Flask, jsonify, request, send_file
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
        font = TTFont(io.BytesIO(requests.get(font_url).content))
        print('font {}'.format(font['hhea']))
        # Update the 'hhea' table
        # Update the 'hhea' table
        if 'hhea' in new_data:
            hhea_data = new_data['hhea']
            hhea_table = font['hhea']
            for key, value in hhea_data.items():
                if hasattr(hhea_table, key):
                    setattr(hhea_table, key, value)
        print('Step 1')
        # Update the 'os2' table
        if 'os2' in new_data:
            os2_data = new_data['os2']
            os2_table = font['OS/2']
            for key, value in os2_data.items():
                if hasattr(os2_table, key):
                    setattr(os2_table, key, value)
        print('Step 2')
        # Update the 'head' table
        if 'head' in new_data:
            head_data = new_data['head']
            head_table = font['head']
            for key, value in head_data.items():
                if hasattr(head_table, key):
                    setattr(head_table, key, value)
        print('Step 3')

        # Set the usWeightClass value of the OS/2 table
        if 'OS/2' not in font:
            font['OS/2'] = newTable('OS/2')
        os2 = font['OS/2']
        if not hasattr(os2, 'usWeightClass'):
            os2.usWeightClass = 400
        else:
            os2.usWeightClass = max(1, min(1000, os2.usWeightClass))

        font['OS/2'] = os2_table

        # Save the modified font to a new file
        updated_font_file = io.BytesIO()
        print('Step 4')
        try: 
            font.save(updated_font_file)
        except Exception as e:
            print('Error {}'.format(e))
        print('Step 5')
        updated_font_file.seek(0)
        print('Step 6')

        return send_file(updated_font_file, as_attachment=True, download_name='updated_font.ttf'), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
