#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { TradingLambdaStack } from '../lib/lambda-stack';
import * as constants from '../lib/constants';

const app = new cdk.App();

// Live trading stack (alternative entrypoint)
new TradingLambdaStack(app, 'TradingCdkLiveStack', {
	env: {
		account: process.env.CDK_DEFAULT_ACCOUNT,
		region: process.env.CDK_DEFAULT_REGION
	},
	fastApiBaseUrl: constants.LIVE_FASTAPI_BASE_URL,
	rdsSecretName: constants.LIVE_RDS_SECRET_NAME
});

// Paper trading stack (alternative entrypoint)
new TradingLambdaStack(app, 'TradingCdkPaperStack', {
	env: {
		account: process.env.CDK_DEFAULT_ACCOUNT,
		region: process.env.CDK_DEFAULT_REGION
	},
	fastApiBaseUrl: constants.PAPER_FASTAPI_BASE_URL,
	rdsSecretName: constants.PAPER_RDS_SECRET_NAME
});
