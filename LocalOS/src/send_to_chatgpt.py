from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Initialize the OpenAI API client
#openai.api_key = api_key

def send_csv_to_chatgpt(csv_file):
    try:
        # Read the CSV content
        with open(csv_file, 'r') as file:
            csv_content = file.read()
        
        if not csv_content:
            raise ValueError("The CSV file is empty.")

        response = client.chat.completions.create(
          model="gpt-4o",
          messages=[
              {"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": f"Please provide a detailed analysis of the following CSV data:\n\n{csv_content}"}
            ],
        )

        # Extract and return the response text
        analysis = response.choices[0].message.content
        return analysis

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    result = send_csv_to_chatgpt('output3.csv')  # Replace with your CSV file path
    if result:
        print("ChatGPT Analysis:")
        print(result)
    else:
        print("Failed to get a response from ChatGPT.")
