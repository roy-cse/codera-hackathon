# Author: Abhishek Roy
# Description: This code is an AWS Lambda function for error handling and analysis, integrating with various services.
# License: MIT License

# Import necessary libraries
import boto3
import requests
import gzip
import base64
import json
from html.parser import HTMLParser
import os
import openai  # Import the OpenAI library

# Get environment variables
slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
openai_api_key = os.environ.get("OPENAI_API_KEY")  # Set your OpenAI API key as an environment variable
application_type = os.environ.get("APPLICATION_TYPE")


def get_filter_pattern_from_name(log_group_name, filter_name):
    try:
        client = boto3.client('logs')
        response = client.describe_subscription_filters(
            logGroupName=log_group_name,
            filterNamePrefix=filter_name  # Use filterNamePrefix to match the filter name
        )

        if 'subscriptionFilters' in response:
            for filter in response['subscriptionFilters']:
                if filter['filterName'] == filter_name:
                    return filter.get('filterPattern')
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return None

# Define a custom HTML parser class
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def get_plain_text(self):
        return ''.join(self.result)

# Function to send an email using Amazon SNS
def send_email_sns(subject, message):
    sns_client = boto3.client("sns")
    sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=message
    )

# Function to send a Slack message
def send_slack_message(message):

    # Create a payload without a divider block
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
              "type": "divider"
            }
        ]
    }

    # Convert the payload to JSON
    payload_json = json.dumps(payload)
    response = requests.post(slack_webhook_url, data=payload_json)
    if response.status_code != 200:
        print(f"Failed to send Slack message: {response.text}")

# Function to search Stack Overflow for error information
def search_stackoverflow(error):
    url = "https://api.stackexchange.com/2.3/search?order=desc&sort=activity&tagged={}&intitle={}&site=stackoverflow"
    formatted_url = url.format(application_type, error)
    resp = requests.get(formatted_url)
    return resp.json()

# Function to retrieve the accepted answer body from Stack Overflow
def get_accepted_answer_body(answer_id):
    resp = requests.get(f"https://api.stackexchange.com/2.3/answers/{answer_id}?order=desc&sort=activity&site=stackoverflow&filter=withbody")
    data = resp.json()
    answer_html = data["items"][0]["body"]

    parser = MyHTMLParser()
    parser.feed(answer_html)
    answer_text = parser.get_plain_text()
    # Split the answer text into lines and select the first two lines
    answer_lines = answer_text.split('\n')
    first_two_lines = '\n'.join(answer_lines[:2])

    return first_two_lines

# Function to print the top answers from Stack Overflow
def print_top_answers(json_dict, num_answers=1):
    count = 0
    answers = []

    for i in json_dict['items']:
        if i['is_answered']:
            answer_info = {
                "title": i['title'],
                "link": i['link'],
                "accepted_answer_id": i['accepted_answer_id']
            }
            answers.append(answer_info)
            count += 1
            if count == num_answers:
                break

    return answers

# Function to get an AI-generated answer using OpenAI
def get_openai_answer(error_message):
    openai.api_key = openai_api_key

    prompt = f"You are an AI assistant to help with the possible cause of errors generated from {application_type} code. Keep the reply in 50 words. If you don't know the possible cause of the error, please reply with I don't know. Error: {error_message}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": prompt}
        ],
    )
    return response['choices'][0]['message']['content']

# Lambda function handler
def lambda_handler(event, context):
    print("Received event:", event)
    
    compressed_payload = event['awslogs']['data']
    decoded_payload = base64.b64decode(compressed_payload)
    decompressed_payload = gzip.decompress(decoded_payload).decode('utf-8')
    print("Decompressed Payload:", decompressed_payload)
    before_lines = 10
    after_lines = 10
    log_data = json.loads(decompressed_payload)
    log_group = log_data['logGroup']
    filter_name = log_data.get("subscriptionFilters", [])
    # Initialize the message with log group and log stream information
    message = f"*Log Group*: {log_group}\n"

    client = boto3.client('logs')

    response = client.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )

    latest_stream = response['logStreams'][0]['logStreamName']
    if filter_name:
        filter_name = filter_name[0]
        print("Subscription Filter:", filter_name)
    else:
        print("No subscription filters found in the JSON data.")
    filter_pattern = get_filter_pattern_from_name(log_group, filter_name)
    
    if filter_pattern is not None:
        print(f"Filter Pattern for '{filter_name}': {filter_pattern}")
    else:
        print(f"Subscription filter '{filter_name}' not found or does not have a filter pattern.")
    response = client.filter_log_events(
        logGroupName=log_group,
        logStreamNames=[latest_stream],
        filterPattern=filter_pattern,
        limit=50
    )

    matching_events = [event for event in response.get('events', []) if filter_pattern in event.get('message', '')]

    if matching_events:
        latest_matching_event = max(matching_events, key=lambda x: x['timestamp'])
        error_message = latest_matching_event['message'].strip()
        context_events = get_log_context_events(log_group, latest_stream, latest_matching_event['timestamp'], before_lines, after_lines)
        stackoverflow_query = error_message

        # Get Stack Overflow question IDs
        json_data = search_stackoverflow(stackoverflow_query)
        stackoverflow_question_ids = print_top_answers(json_data)

        # Get answer from OpenAI for the error message
        openai_answer = get_openai_answer(error_message)

        # Append log stream and error message to the message
        message += f"*Log stream*: {latest_stream}\n*Error*: {error_message}\n\n*Log Lines*:\n"
        
        for event in context_events:
            message += event['message']

        for question in stackoverflow_question_ids:
            accepted_answer_id = question["accepted_answer_id"]
            answer_snippet = get_accepted_answer_body(accepted_answer_id)
            message += "\n*Accepted Answer from Stack Overflow*:\n" + answer_snippet + "... "

            # Construct the "View More Details" link using the accepted answer's link
            answer_link = f"(<https://stackoverflow.com/a/{accepted_answer_id}|View More Details>)\n"  # Modified line
            message += answer_link

        # Append OpenAI answer to the message
        message += "\n*Answer from OpenAI*:\n" + openai_answer

        send_email_sns("Error Occurred", message)
        send_slack_message(message)

# Function to retrieve log events around the time of the error
def get_log_context_events(log_group, log_stream, timestamp, before_lines, after_lines):
    client = boto3.client('logs')
    response = client.get_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        startTime=timestamp - (before_lines * 1000),
        endTime=timestamp + (after_lines * 1000),
        limit=before_lines + after_lines + 1
    )
    return response['events']
