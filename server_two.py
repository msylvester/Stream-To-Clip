from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Sample video links
SAMPLE_VIDEOS = [
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4"
]

@app.route('/api/process-video', methods=['POST'])
def process_video():
    try:
        data = request.json
        url = data.get('url')
        rez = data.get('resolution') 
        print(f'the url is {url} and the rez is {rez}')

        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
       # For demonstration, we'll return all sample videos regardless of input URL
       
       # we need to create a compound string with the url + {rez}
       # plus_url = url + {rez} 
       # we need to cd into mac_version and then execute the command `python process_vid_v2.py {plus_url`-


       # i want the repsonse to include the videos clips created after running `process_vid_v2.py {url}{rez}`

       response_data = {
            'videos': SAMPLE_VIDEOS
        }
        return jsonify({
            'output': json.dumps(response_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)  # Changed port to 5001
