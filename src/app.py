import subprocess
import tempfile
import os
import json
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_xml_to_dsl():
    if 'file' not in request.files:
        return jsonify({'error': 'No XML file uploaded'}), 400

    xml_file = request.files['file']
    xml_bytes = xml_file.read()

    temp_xml_path = None
    temp_dsl_path = None
    try:
        # Write XML to a temp file
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False, mode='wb') as temp_xml:
            temp_xml.write(xml_bytes)
            temp_xml_path = temp_xml.name

        # Create temp DSL file
        with tempfile.NamedTemporaryFile(suffix='.dsl', delete=False, mode='r+') as temp_dsl:
            temp_dsl_path = temp_dsl.name

        # Call xml2dsl.py with input/output filenames
        print(f"Running subprocess with {temp_xml_path} -> {temp_dsl_path}")
        result = subprocess.run(
            ['python', 'xml2dsl.py', temp_xml_path, temp_dsl_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Subprocess completed with return code {result.returncode}")

        if result.returncode != 0:
            return jsonify({
                'error': 'Conversion failed',
                'stderr': result.stderr,
                'stdout': result.stdout
            }), 500

        # Read the output DSL
        with open(temp_dsl_path, 'r', encoding='utf-8') as dsl_file:
            dsl_code = dsl_file.read()

        # Parse React Flow JSON from stdout
        try:
            react_flow_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return jsonify({
                'error': 'Failed to parse React Flow JSON',
                'stdout': result.stdout,
                'json_error': str(e)
            }), 500

        # Return both DSL and React Flow data
        return jsonify({
            'dsl': dsl_code,
            'react_flow': react_flow_data
        })

    except Exception as e:
        # Log the full traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500

    finally:
        # Clean up temp files safely
        for temp_file in [temp_xml_path, temp_dsl_path]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except PermissionError as e:
                    print(f"Warning: Could not delete {temp_file}: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)