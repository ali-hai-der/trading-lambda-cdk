#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { TradingLambdaStack } from '../lib/lambda-stack';

const app = new cdk.App();

// Original Trading Stack
new TradingLambdaStack(app, 'TradingLambdaCdkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
