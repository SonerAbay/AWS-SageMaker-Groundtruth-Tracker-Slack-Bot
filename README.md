# AWS SageMaker Groundtruth Slack Bot

*This repo is created to track your private workforce on SageMaker Groundtruth.*

You need to create your own mysql server to make it work. You can delete send_telegram function if you are not interested in getting notified for every single labeling action.

**Usage:**

1. Create the mysql tables as in the screenshots. You should manually add the cognito_sub_id of your workers and slack_id to the table. Then set cognito_sub_id in the labels table as foreign key to users table.

2. Create 3 api gateways for your slash commands with public access on AWS.

3. Create your slackbot with 3 slash commands: myscore, teamscore, top10 with your api gateway destinations as URL.
 
4. Create 3 different AWS Lambda functions.
After creating a lambda function on AWS. You can upload the zip files on "Code Entry Type" menu. Upload myscore, teamscore and top10 .zip files to the different Lambda Functions.

5. Add your api gateways as trigger to the Lambda function.

6. Add your slackbot to your workspace.  


**Note:** If you want you can handle all of the requests with a single api gateway and lambda function. If you want to do it, you should process the command in the invoke event.
