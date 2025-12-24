#!/bin/bash
# Script to help clean up security group dependencies

SECURITY_GROUP_ID="sg-04e575c083fa372db"
REGION="${AWS_REGION:-us-east-1}"  # Change if needed

echo "Checking what's using security group: $SECURITY_GROUP_ID"

# Check for ENIs using this security group
echo ""
echo "=== Checking Elastic Network Interfaces ==="
aws ec2 describe-network-interfaces \
  --filters "Name=group-id,Values=$SECURITY_GROUP_ID" \
  --region $REGION \
  --query 'NetworkInterfaces[*].[NetworkInterfaceId,Status,Description,PrivateIpAddress]' \
  --output table

# Check for VPC endpoints
echo ""
echo "=== Checking VPC Endpoints ==="
aws ec2 describe-vpc-endpoints \
  --filters "Name=group-id,Values=$SECURITY_GROUP_ID" \
  --region $REGION \
  --query 'VpcEndpoints[*].[VpcEndpointId,State,ServiceName]' \
  --output table

# Check for ingress rules referencing this security group
echo ""
echo "=== Checking Ingress Rules ==="
aws ec2 describe-security-groups \
  --group-ids $SECURITY_GROUP_ID \
  --region $REGION \
  --query 'SecurityGroups[0].IpPermissions' \
  --output json

echo ""
echo "=== Instructions ==="
echo "1. If ENIs are found, wait 5-10 minutes for them to auto-delete after Lambda deletion"
echo "2. Or manually delete ENIs: aws ec2 delete-network-interface --network-interface-id <eni-id>"
echo "3. If VPC endpoints exist, delete them first: aws ec2 delete-vpc-endpoint --vpc-endpoint-id <endpoint-id>"
echo "4. Then retry stack deletion: cdk destroy TradingLambdaCdkStack"

