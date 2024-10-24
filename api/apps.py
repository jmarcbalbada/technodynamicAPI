from django.apps import AppConfig
from threading import Thread
import requests
import time
import os

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'api'

    def ready(self):
        # Start a separate thread with a delay to call the startBackgroundCreation after server start
        if not self.isTesting():
            thread = Thread(target=self.delayedApiCall)
            thread.start()

    def delayedApiCall(self):
        # Wait a few seconds to allow the server to start fully
        time.sleep(5)  # Adjust the delay as needed
        self.callApiOnStartup()

    def callApiOnStartup(self):
        # Set the base URL dynamically based on the environment
        if os.environ.get('DJANGO_ENV') == 'production':
            base_url = "https://technodynamicv2-73437bf08784.herokuapp.com"
        else:
            base_url = "http://localhost:8000"

        url = base_url.strip() + "/api/suggestions/contents/startWorker/"

        headers = {
            'Content-Type': 'application/json',
        }

        try:
            # Make a POST request to the startBackgroundCreation endpoint
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                print("Background content creation started successfully.")
            else:
                print(f"Failed to start background content creation: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error during background content creation start: {e}")

    def isTesting(self):
        # Avoid running during tests
        import sys
        return 'test' in sys.argv[1:]
