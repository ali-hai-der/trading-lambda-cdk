import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class TradingLambdaStack extends cdk.Stack {
	constructor(scope: Construct, id: string, props?: cdk.StackProps) {
		super(scope, id, props);

		// Look up the default VPC (where EC2 instance is running)
		const vpc = ec2.Vpc.fromLookup(this, 'DefaultVPC', {
			isDefault: true
		});

		// Create security group for Lambda
		const lambdaSecurityGroup = new ec2.SecurityGroup(
			this,
			'LambdaSecurityGroup',
			{
				vpc,
				description: 'Security group for Trading Lambda function',
				allowAllOutbound: true // Allow outbound traffic to reach EC2
			}
		);

		// Create the Lambda function using Docker image
		const tradingLambda = new lambda.DockerImageFunction(
			this,
			'TradingLambdaFunction',
			{
				code: lambda.DockerImageCode.fromImageAsset(
					path.join(__dirname, '../src/trading-lambda')
				),
				timeout: cdk.Duration.minutes(5),
				memorySize: 256,
				vpc,
				vpcSubnets: {
					// Use public subnets (default VPC only has public subnets)
					// Note: Lambda in VPC loses internet access, so we use VPC endpoint for Secrets Manager
					subnetType: ec2.SubnetType.PUBLIC,
					onePerAz: true
				},
				allowPublicSubnet: true, // Acknowledge that Lambda in public subnet cannot access internet
				securityGroups: [lambdaSecurityGroup],
				environment: {
					// Add any environment variables here if needed
					FASTAPI_BASE_URL: 'http://172.31.6.178:8888',
					LAMBDA_API_KEY: process.env.LAMBDA_API_KEY || ''
				}
			}
		);

		// Create VPC endpoint for Secrets Manager in public subnets
		// Lambda in VPC loses internet access, so we need VPC endpoint to access Secrets Manager
		const secretsManagerEndpoint = vpc.addInterfaceEndpoint(
			'SecretsManagerEndpoint',
			{
				service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
				subnets: {
					subnetType: ec2.SubnetType.PUBLIC
				}
			}
		);

		// Grant Secrets Manager permissions to Lambda
		tradingLambda.addToRolePolicy(
			new iam.PolicyStatement({
				effect: iam.Effect.ALLOW,
				actions: [
					'secretsmanager:GetSecretValue',
					'secretsmanager:DescribeSecret'
				],
				resources: [
					// Replace with your actual secret ARN or use wildcard for specific pattern
					`arn:aws:secretsmanager:${this.region}:${this.account}:secret:*`
				]
			})
		);

		// EventBridge Rule 1: Daily trigger for updating contracts table
		const dailyContractsRule = new events.Rule(
			this,
			'DailyContractsUpdateRule',
			{
				schedule: events.Schedule.rate(cdk.Duration.days(1)),
				description: 'Trigger Lambda daily to update contracts table'
			}
		);

		// Add Lambda as target with specific event payload for update_contracts_table
		dailyContractsRule.addTarget(
			new targets.LambdaFunction(tradingLambda, {
				event: events.RuleTargetInput.fromObject({
					method: 'update_contracts_table',
					contracts_details: {
						underlying_symbol: 'SPX',
						underlying_type: 'index',
						exchange: 'SMART'
					}
				})
			})
		);

		// EventBridge Rule 2: 5-minute trigger for capturing account summary
		const accountSummaryRule = new events.Rule(this, 'AccountSummaryRule', {
			schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
			description: 'Trigger Lambda every 5 minutes to capture account summary'
		});

		// Add Lambda as target with specific event payload for capture_account_summary
		accountSummaryRule.addTarget(
			new targets.LambdaFunction(tradingLambda, {
				event: events.RuleTargetInput.fromObject({
					method: 'capture_account_summary',
					account_number: 'DUK273068' // TODO: Replace with actual account number for live trading or use environment variable
				})
			})
		);

		// EventBridge Rule 3: Daily trigger for refreshing orders - May add truncate orders rule separately
		const refreshOrdersRule = new events.Rule(this, 'RefreshOrdersRule', {
			schedule: events.Schedule.cron({ minute: '30', hour: '11' }),
			description: 'Trigger Lambda daily at 5:30 AM CST to refresh orders'
		});

		// Add Lambda as target with specific event payload for refresh_orders
		refreshOrdersRule.addTarget(
			new targets.LambdaFunction(tradingLambda, {
				event: events.RuleTargetInput.fromObject({
					method: 'refresh_orders'
				})
			})
		);

		// Output the Lambda function ARN
		new cdk.CfnOutput(this, 'LambdaFunctionArn', {
			value: tradingLambda.functionArn,
			description: 'Trading Lambda Function ARN'
		});

		// Output the function name
		new cdk.CfnOutput(this, 'LambdaFunctionName', {
			value: tradingLambda.functionName,
			description: 'Trading Lambda Function Name'
		});

		// Output the Lambda security group ID
		new cdk.CfnOutput(this, 'LambdaSecurityGroupId', {
			value: lambdaSecurityGroup.securityGroupId,
			description: 'Lambda Security Group ID - Add this to EC2 inbound rules'
		});
	}
}
