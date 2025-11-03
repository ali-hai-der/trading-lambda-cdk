#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { TradingCdkStack } from '../lib/trading-cdk-stack';

const app = new cdk.App();

// Original Trading Stack
new TradingCdkStack(app, 'TradingCdkStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
