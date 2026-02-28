#!/usr/bin/env node
// Load environment variables from .env file
import * as dotenv from 'dotenv';
dotenv.config();

import * as cdk from 'aws-cdk-lib/core';
import { TradingLambdaStack } from '../lib/lambda-stack';
import * as constants from '../lib/constants';

const app = new cdk.App();

// Live trading stack
new TradingLambdaStack(app, 'LiveTradingLambdaSyncCdkStack', {
	env: {
		account: process.env.CDK_DEFAULT_ACCOUNT,
		region: process.env.CDK_DEFAULT_REGION
	},
	fastApiBaseUrl: constants.LIVE_FASTAPI_BASE_URL,
	rdsSecretName: constants.LIVE_RDS_SECRET_NAME
});

// Paper trading stack
new TradingLambdaStack(app, 'PaperTradingLambdaSyncCdkStack', {
	env: {
		account: process.env.CDK_DEFAULT_ACCOUNT,
		region: process.env.CDK_DEFAULT_REGION
	},
	fastApiBaseUrl: constants.PAPER_FASTAPI_BASE_URL,
	rdsSecretName: constants.PAPER_RDS_SECRET_NAME
});
