import subprocess
import tempfile
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

    # Step 1: Save XML to a temp file
    with tempfile.NamedTemporaryFile(suffix='.xml', mode='wb', delete=False) as temp_xml:
        temp_xml.write(xml_bytes)
        temp_xml.flush()

        with tempfile.NamedTemporaryFile(suffix='.dsl', mode='r+', delete=False) as temp_dsl:
            temp_dsl_filename = temp_dsl.name

            # Step 2: Call xml2dsl.py with input/output filenames
            result = subprocess.run(
                ['python', 'xml2dsl.py', temp_xml.name, temp_dsl_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                return jsonify({'error': 'Conversion failed', 'stderr': result.stderr}), 500

            # Step 3: Read the output DSL
            temp_dsl.seek(0)
            dsl_code = temp_dsl.read()

    return jsonify({'dsl': dsl_code})

if __name__ == '__main__':
    app.run(debug=True)
