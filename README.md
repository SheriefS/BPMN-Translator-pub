# BPMN-Translator

The code included will allow access to a simple web-based application which will allow for conversion of a BPMN file to a CSV file. Once the CSV file is generated, there is an option to use the CSV file and send it to the OpenAI API for a response.  Currently, ChatGPT is simply being requested to provide an analysis of the file. The response will be saved in a .txt file named by the user.

## How to use: ##

There are two options for running the code. 
-  **Option 1** is for all the necessary libraries and programs locally. These steps will be OS dependant. 
-  **Option 2** uses Docker to deploy the container. This can be deployed on any machine as long as Docker is installed.

## _Option 1: Local MacOS_ ##

1. Download and install the latest version of Python for the appropriate operating system [here](https://www.python.org/downloads/).
2. Download the requirement.txt file and the src folder from the repository.
3. Go to Applications > Utilities and open Terminal.
4. Type `python --version` to confirm that python was installed.
5. If Python is installed, use `python3 -m ensurepip` which will install pip, which allows for extensions to be installed for Python.
6. Once Pip is installed, navigate to the directory in the terminal where the repository was downloaded.
7. Execute the command `pip install -r requirements.txt`. If for some reason that does not work, try `pip3 install -r requirements.txt`. You must be in the directory that includes the .txt file.
8. Check to make sure that OpenSSL is installed using `openssl version`. If it is not, install it. We will use this to generate a certificate so that we can use HTTPS instead of HTTP for the local server.
9. Navigate into the _/src_ folder.
10. Execute the command `openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes` to generate the encrypted certificate and key locally. This will be valid for one year.
11. From the _/src_ folder, execute the command `python3 Flask_GUI.py`. This will start the Flask server. You will see something similar to the below in the terminal.

   ![](/Flask_running.png)

12. Now open any browser. In the address bar, paste: [_https://127.0.0.1:5000_](https://127.0.0.1:5000). (Note: You may get a 'Risk' message as the certificate is not going through a authority. You can proceed.)
13. You can how use the application.
    * Choose a BPMN file and convert it to CSV. The *.csv output can be found in the folder _/src/generated_csvs_. A green text message will appear when complete.
    * Choose a CSV and send it to chatGPT. The *.txt output can be found in the folder _/src/chatgpt_responses_. (Note: This will take about 10 seconds based on current prompts. A green text message will appear when complete.)
14. Press Ctrl-C in the terminal to end the program
15. To rerun the program, open a terminal and repeat steps 11 to 13. All other steps are for setup only.
   
## _Option 2: Docker_ ##

1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Download all files in the [/Docker](/Docker) folder from the repository.
3. Open Docker and set it up if necessary.
4. Locate the terminal within Docker Desktop in the bottom right (may be different for MacOS version).
5. Navigate to the folder that contains the Dockerfile downloaded from the repository.
6. Execute the command `docker build -t bpmn-translator .`. This will create the image.
7. Execute the command `docker-compose up`. This will create the container.
8. The Flask Server will start and text similar to the below will appear:
   ![](/Flask_running.png)
9. The app can now be accessed by visiting [https://localhost:5000](https://localhost:5000) in any browser (Note: You may get a 'Risk' message as the certificate is not going through a authority. You can proceed.).
10. You can how use the application.
    * Choose a BPMN file and convert it to CSV. The *.csv output can be found in the folder _/generated_csvs_. A green text message will appear when complete.
    * Choose a CSV and send it to chatGPT. The *.txt output can be found in the folder _/chatgpt_responses_. (Note: This will take about 10 seconds based on current prompts. A green text message will appear when complete.)
11. You can use Ctrl-C in the Docker terminal to end the program. Or you can navigate to the "Containers" category and use the buttons under "Actions" Column.
12. Restart the program using the play Actions next to the container.

A brief explanation of each file can be found below.

## Contents: ##
- ._/BPMN Project_: Main Project folder.
   - _Dockerfile_: file for use with Docker to build _(See option 2)_.
   - _docker-compose.yml_: file for use with Docker to build _(See option 2)_.
   - _requirements.txt_: File used for python addon setup.
   - _/src_: Contains the python files and folders for output files.
    * _/templates_: Contains HTML for webpage.
      * _index.html_: Html document to gererate webpage.
    * _.env_: Contains the Openai API key.
    * _Flask_GUI.py_: This is the main python script which will run all others.
    * _send_to_chatgpt.py_: Contains the functions for handling the communication with OpenAI.
    * _XML_to_CSV_Converter.py_: Script responsible for converting the BPMN XML code to the desired CSV output.


  
