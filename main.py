import http.server
import socketserver
import json
from openai import OpenAI
import os
import mimetypes
import uuid

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
client = OpenAI(api_key="sk-ccef741bf3b845f48c0d94c05fd84604", base_url="https://api.deepseek.com")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            component_details = data.get('component_details', '')
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Be a machine that generates web component specifications based on user input."},
                    {"role": "user", "content": f"Generate a web component with the following details: {component_details}"},
                ],
                stream=False
            )

            component_code = response.choices[0].message.content
            unique_id = str(uuid.uuid4())
            file_name = f"generated_component_{unique_id}.html"
            file_path = os.path.join(DIRECTORY, file_name)

            with open(file_path, "w") as file:
                file.write(component_code)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"file_path": file_name}).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        if self.path == '/generated_component.html':
            file_path = os.path.join(DIRECTORY, 'generated_component.html')
            if os.path.exists(file_path):
                self.send_response(200)
                mime_type, _ = mimetypes.guess_type(file_path)
                self.send_header('Content-type', mime_type or 'text/html')
                self.end_headers()
                with open(file_path, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404, "Generated component not found")
        else:
            super().do_GET()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()