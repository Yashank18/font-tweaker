from flask import Flask, jsonify, request, send_file, make_response
from fontTools.ttLib import TTFont, newTable
import io
import requests
import json
from flask_cors import CORS  # Import CORS from flask_cors
import mimetypes

app = Flask(__name__)
# Configure the first CORS instance
CORS(app)


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
    

@app.route('/api/get-all-font-data', methods=['POST'])
def get_all_font_data():
    try:
        font_url = request.json.get('fontUrl')
        font = TTFont(io.BytesIO(requests.get(font_url).content))

        return json.dumps(font.toXML(), indent=4), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-font-data-buffer', methods=['POST'])
def extract_font_data_from_buffer():
    try:
        font_file = request.files['fontFile']
        font_buffer = font_file.read()
        font = TTFont(io.BytesIO(font_buffer))
        
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
            font_data['os2']['panose'] = os2_table.panose

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

        font = TTFont(io.BytesIO(requests.get(font_url).content))

        # Determine the MIME type based on the font_url
        mime_type, _ = mimetypes.guess_type(font_url)

        if 'OS/2' in font:
            os2 = font['OS/2']
            os2.usWinAscent = usWinAscent
            os2.usWinDescent = usWinDescent

        buffer = io.BytesIO()
        font.save(buffer)


        # Create a Flask HTTP response with the modified font
        response = make_response(buffer.getvalue())

        # Set the Content-Type header
        response.headers['Content-Type'] = mime_type if mime_type else 'application/octet-stream'

        # Set the Content-Disposition header with the correct filename
        response.headers['Content-Disposition'] = 'attachment; filename=myfont_modified.ttf'

        # Set the Content-Length header
        response.headers['Content-Length'] = len(response.data)
        
        # Close the buffer
        buffer.close()
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/update-font-data-from-file', methods=['POST'])
def update_font_data_from_file():
    try:
        # Check if 'fontFile' and 'newData' keys exist in the request
        if 'fontFile' not in request.files or 'newData' not in request.form:
            return jsonify({'error': 'fontFile and/or newData missing in the request'}), 400
        
        font_file = request.files['fontFile']
        new_data = json.loads(request.form['newData'])
        usWinAscent = new_data['usWinAscent']
        usWinDescent = new_data['usWinDescent']

        font = TTFont(io.BytesIO(font_file.read()))

        # Determine the MIME type based on the font file
        mime_type, _ = mimetypes.guess_type(font_file.filename)

        if 'OS/2' in font:
            os2 = font['OS/2']
            os2.usWinAscent = usWinAscent
            os2.usWinDescent = usWinDescent

        buffer = io.BytesIO()
        font.save(buffer)

        # Create a Flask HTTP response with the modified font
        response = make_response(buffer.getvalue())

        # Set the Content-Type header
        response.headers['Content-Type'] = mime_type if mime_type else 'application/octet-stream'

        # Set the Content-Disposition header with the correct filename
        response.headers['Content-Disposition'] = f'attachment; filename={font_file.filename}_modified.ttf'

        # Set the Content-Length header
        response.headers['Content-Length'] = len(response.data)
        
        # Close the buffer
        buffer.close()
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 400
