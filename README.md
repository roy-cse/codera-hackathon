# Codera Lambda Function

This repository contains a Python AWS Lambda function for handling error events and providing insights and assistance for debugging. The function integrates with various services, including AWS SNS, Slack, Stack Overflow, and OpenAI, to provide comprehensive error analysis and assistance.

## Prerequisites

Before deploying and using this Lambda function, make sure you have the following prerequisites in place:

1. **AWS Account**: You should have an active AWS account to deploy and manage Lambda functions.

2. **AWS Lambda**: Familiarity with AWS Lambda and how to create and configure Lambda functions is essential.

3. **AWS CloudWatch Logs**: You should be using AWS CloudWatch Logs to capture and store error events.

4. **OpenAI API Key**: You need to obtain an OpenAI API key and set it as an environment variable named `OPENAI_API_KEY`.

5. **Slack Webhook URL**: You should have a Slack webhook URL for sending error notifications to Slack channels. Set this URL as an environment variable named `SLACK_WEBHOOK_URL`.

6. **SNS Topic ARN**: You need an AWS SNS topic ARN for sending email notifications. Set the ARN as an environment variable named `SNS_TOPIC_ARN`.

7. **Application Type**: Define the type of application you are monitoring by setting the `APPLICATION_TYPE` environment variable.

## Code Overview

The Lambda function consists of several components and functionalities:

1. **HTML Parsing**: The `MyHTMLParser` class is used to parse HTML content into plain text.

2. **Notification Functions**: Functions like `send_email_sns` and `send_slack_message` handle sending notifications to AWS SNS and Slack channels, respectively.

3. **Stack Overflow Search**: The `search_stackoverflow` function queries the Stack Exchange API to find relevant Stack Overflow questions related to the error.

4. **OpenAI Integration**: The `get_openai_answer` function uses the OpenAI GPT-3.5 Turbo model to generate responses for error messages.

5. **Lambda Handler**: The `lambda_handler` function is the entry point for the Lambda function. It decompresses and processes CloudWatch log events, extracts error messages, searches Stack Overflow for related questions, generates responses using OpenAI, and sends notifications.

6. **Context Retrieval**: The `get_log_context_events` function retrieves context events before and after the error event from CloudWatch Logs.

## Usage

1. This lambda code is compatible with Python3.7. After cloning the repository, run `pip install -r requirements.txt`.
   - This will install all the python packages. We'll compress the entire folder with the main.py file and the python packages and we'll upload it to Lambda later.  

2. Set up the Lambda function in your AWS account, ensuring it has the necessary permissions to access SNS, CloudWatch Logs, and other required services.

3. Set the environment variables `OPENAI_API_KEY`, `SLACK_WEBHOOK_URL`, `SNS_TOPIC_ARN`, and `APPLICATION_TYPE` with the appropriate values.

4. Configure CloudWatch Logs to trigger the Lambda function when specific error events occur i.e. set up a subscription filter for the preferred log group.

5. When an error event is detected, the Lambda function will:

   - Extract the error message.
   - Search Stack Overflow for related questions.
   - Retrieve context events from CloudWatch Logs.
   - Use OpenAI to generate responses.
   - Send notifications to Slack and email (SNS) with error details, Stack Overflow links, and OpenAI responses.

## Customization

You can customize this Lambda function to suit your specific use case by modifying the code, adjusting environment variables, or adding additional integrations.

## Credits

This Lambda function utilizes the following technologies and services:

- [AWS Lambda](https://aws.amazon.com/lambda/): Serverless computing service by AWS.
- [AWS SNS](https://aws.amazon.com/sns/): Simple Notification Service for sending email notifications.
- [AWS CloudWatch Logs](https://aws.amazon.com/cloudwatch/features/logs/): Log storage and monitoring service.
- [OpenAI GPT-3.5 Turbo](https://beta.openai.com/signup/): Powerful language model for generating responses.
- [Stack Exchange API](https://api.stackexchange.com/docs): API for accessing Stack Overflow questions and answers.
- [Slack Webhooks](https://api.slack.com/messaging/webhooks): Webhooks for sending messages to Slack channels.

## License

This code is provided under the [MIT License](LICENSE). Feel free to use and modify it according to your requirements.
