import os, datetime, random, subprocess, time
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

def random_seed():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_number = random.randint(1000, 9999)
    return f"{timestamp}_{random_number}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'tflite'}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    with open('index.html', 'r') as file:
        html = file.read()

    if request.method == 'POST':
        print(request.url)
        device = request.form.get('device')
        print(f"Device: {device}")
        
        if 'file' not in request.files:
            html.replace('<h1>Upload your .tflite model</h1>', '<h1>.tflite file not found.</h1>')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            html.replace('<h1>Upload your .tflite model</h1>', '<h1>.tflite file not found.</h1>')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            tflite_name = secure_filename(file.filename)
            seed = random_seed()

            print(f'Generate a upload instance:{seed}')
            os.makedirs(f"{app.config['UPLOAD_FOLDER']}/{seed}", exist_ok=True)
            saved_path = os.path.join(f"{app.config['UPLOAD_FOLDER']}/{seed}", tflite_name)
            file.save(saved_path)

            cmd = f"./neuronpilot-6.0.5/neuron_sdk/host/bin/ncc-tflite --arch={device} --relax-fp32 {saved_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"Return code: {result.returncode}")
            print(f"Output: {result.stdout}")
            print(f"Error: {result.stderr}")

            if int(result.returncode) == 0:
                dla_name = tflite_name.rstrip('.tflite') + '.dla'
                response = send_from_directory(f"{app.config['UPLOAD_FOLDER']}/{seed}", dla_name)
                device_name = device.replace('.', '_')
                response.headers['name'] = dla_name.replace('.dla', f'_{device_name}.dla')
                return response
            else:
                saved_path = os.path.join(f"{app.config['UPLOAD_FOLDER']}/{seed}", "error_message.txt")
                with open(saved_path, 'w') as f:
                    f.write(result.stdout + '\n' + result.stderr)
                response = send_from_directory(f"{app.config['UPLOAD_FOLDER']}/{seed}", "error_message.txt")
                response.headers['name'] = "error_message.txt"
                return response
    return html

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=80)