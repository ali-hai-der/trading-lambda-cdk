#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { TradingCdkStack } from '../lib/trading-cdk-stack';
import { EC2ApiGatewayStack } from '../lib/EC2ApiGatewayStack';

const app = new cdk.App();

// Original Trading Stack
new TradingCdkStack(app, 'TradingCdkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// EC2 API Gateway Stack with Cognito
new EC2ApiGatewayStack(app, 'EC2ApiGatewayStack', {
  ec2InstanceId: process.env.EC2_INSTANCE_ID || 'i-xxxxxxxxxxxxxxxxx',
  ec2Port: parseInt(process.env.EC2_PORT || '8888'),
  ec2PublicDns: process.env.EC2_PUBLIC_DNS || 'ec2-54-167-171-28.compute-1.amazonaws.com',
  existingUserPoolId: process.env.COGNITO_USER_POOL_ID || 'us-east-1_lohKhxW0i',
  existingUserPoolClientId: process.env.COGNITO_CLIENT_ID || '178lf9j46nk6l1902052pavn31',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
