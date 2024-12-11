import * as cdk from 'aws-cdk-lib';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { Construct } from 'constructs';
import * as fs from 'fs';
import * as path from 'path';

export class SemitaeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Process Instruction Lambda
    const processInstruction = new lambda.Function(this, 'ProcessInstruction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'process_instruction.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambdas')),
      timeout: cdk.Duration.seconds(30),
    });

    // Generate Message Lambda
    const generateMessage = new lambda.Function(this, 'GenerateMessage', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'generate_message.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambdas')),
      timeout: cdk.Duration.seconds(30),
    });

    // Load and prepare state machine definition
    const definitionPath = path.join(__dirname, '../statemachine/definition.json');
    const definitionTemplate = fs.readFileSync(definitionPath, 'utf-8');

    // Replace the placeholders with actual Lambda ARNs
    const definition = definitionTemplate
      .replace('${ProcessInstructionFunctionArn}', processInstruction.functionArn)
      .replace('${GenerateMessageFunctionArn}', generateMessage.functionArn);

    // Create the state machine
    const stateMachine = new sfn.StateMachine(this, 'InstructionStateMachine', {
      definitionBody: sfn.DefinitionBody.fromString(definition),
      stateMachineType: sfn.StateMachineType.EXPRESS,
      timeout: cdk.Duration.minutes(5),
      tracingEnabled: true,
      logs: {
        destination: new cdk.aws_logs.LogGroup(this, 'StateMachineLogs', {
          retention: cdk.aws_logs.RetentionDays.ONE_WEEK,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }),
        level: sfn.LogLevel.ALL,
        includeExecutionData: true,
      },
    });

    // Grant Lambda permissions
    processInstruction.grantInvoke(stateMachine);
    generateMessage.grantInvoke(stateMachine);

    // AppSync API
    const api = new appsync.GraphqlApi(this, 'SemitaeApi', {
      name: 'semitae-api',
      schema: appsync.SchemaFile.fromAsset('graphql/schema.graphql'),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.API_KEY,
          apiKeyConfig: {
            expires: cdk.Expiration.after(cdk.Duration.days(365))
          }
        },
      },
    });

    // Step Functions as data source
    const sfnDs = api.addHttpDataSource(
      'StepFunctionsDataSource',
      `https://sync-states.${this.region}.amazonaws.com/`,
      {
        name: 'stepFunctionsDS',
        authorizationConfig: {
          signingRegion: this.region,
          signingServiceName: 'states',
        },
      }
    );

    // Grant permission to execute state machine
    stateMachine.grantStartSyncExecution(sfnDs.grantPrincipal);

    // Send Instruction Resolver
    sfnDs.createResolver('SendInstruction', {
      typeName: 'Mutation',
      fieldName: 'sendInstruction',
      // In the CDK stack, update the SendInstruction resolver's requestMappingTemplate:
      requestMappingTemplate: appsync.MappingTemplate.fromString(`
        {
          "version": "2018-05-29",
          "method": "POST",
          "resourcePath": "/",
          "params": {
            "headers": {
              "content-type": "application/x-amz-json-1.0",
              "x-amz-target": "AWSStepFunctions.StartSyncExecution"
            },
            "body": {
              "stateMachineArn": "${stateMachine.stateMachineArn}",
              "input": "{\\\"encounterId\\\": \\\"$ctx.arguments.encounterId\\\", \\\"playerId\\\": \\\"$ctx.arguments.playerId\\\", \\\"instruction\\\": \\\"$ctx.arguments.instruction\\\"}"
            }
          }
        }
      `),
      responseMappingTemplate: appsync.MappingTemplate.fromString(`
        #if($ctx.error)
          $util.error($ctx.error.message, $ctx.error.type)
        #end
        #set($body = $util.parseJson($ctx.result.body))
        #set($output = $util.parseJson($body.output))
        $util.toJson($output)
      `)
    });

    // Outputs
    new cdk.CfnOutput(this, 'GraphQLApiUrl', {
      value: api.graphqlUrl
    });

    new cdk.CfnOutput(this, 'GraphQLApiKey', {
      value: api.apiKey || ''
    });
  }
}