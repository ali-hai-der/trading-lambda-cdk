import * as cdk from 'aws-cdk-lib/core';
import { Construct } from 'constructs';
import { TradingLambdaStack } from './lambda-stack';
// import * as sqs from 'aws-cdk-lib/aws-sqs';

export class TradingCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here
    const tradingLambdaStack = new TradingLambdaStack(this, 'TradingLambdaStack', props);
    // example resource
    // const queue = new sqs.Queue(this, 'TradingLambdaCdkQueue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });
  }
}
