import * as pulumi from "@pulumi/pulumi";
import * as archive from "@pulumi/archive";
import * as aws from "@pulumi/aws";

const assumeRole = aws.iam.getPolicyDocument({
    statements: [{
        effect: "Allow",
        principals: [{
            type: "Service",
            identifiers: ["lambda.amazonaws.com"],
        }],
        actions: ["sts:AssumeRole"],
    }],
});

const iamForLambda = new aws.iam.Role("iam_for_lambda", {
    name: "iam_for_lambda",
    assumeRolePolicy: assumeRole.then(assumeRole => assumeRole.json),
    inlinePolicies: [{
        name: "an_inline_policy",
        policy: JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Action: "cloudwatch:PutMetricData",
                Effect: "Allow",
                Sid: "",
                Resource: "*",
            }],
        }),
    }],
});

const lambda = archive.getFile({
    type: "zip",
    sourceDir: "src/",
    outputPath: "lambda_function_payload.zip",
});

const weatherPutMetricLambda = new aws.lambda.Function("weatherPutMetricLambda", {
    code: new pulumi.asset.FileArchive("lambda_function_payload.zip"),
    name: "put_weather_info",
    role: iamForLambda.arn,
    handler: "lambda.handler",
    sourceCodeHash: lambda.then(lambda => lambda.outputBase64sha256),
    runtime: aws.lambda.Runtime.Python3d13,
    // layers: [layerWithRequests.arn],
    environment: {
        variables: {
            LOCATION: "pre-defined+location",
        },
    },
});

export const out = weatherPutMetricLambda.name;
