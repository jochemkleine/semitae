import * as cdk from 'aws-cdk-lib';
import * as appsync from 'aws-cdk-lib/aws-appsync';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import { Construct } from 'constructs';
import * as path from 'path';

export class SemitaeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Encounter Table
    const encounterTable = new dynamodb.Table(this, 'EncounterTable', {
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // Process Instruction Lambda
    const processInstruction = new lambda.Function(this, 'ProcessInstruction', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'process_instruction.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambdas')),
      timeout: cdk.Duration.seconds(30),
    });

    // Create Step Function task
    const processInstructionTask = new tasks.LambdaInvoke(this, 'ProcessInstructionTask', {
      lambdaFunction: processInstruction,
      resultPath: '$.taskResult',
    });

    // Create the state machine
    const stateMachine = new sfn.StateMachine(this, 'InstructionStateMachine', {
      definition: processInstructionTask,
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

    // DynamoDB as data source
    const encounterTableDS = api.addDynamoDbDataSource('EncounterTableDS', encounterTable);

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

    // Create Encounter Resolver
    encounterTableDS.createResolver('CreateEncounter', {
      typeName: 'Mutation',
      fieldName: 'createEncounter',
      requestMappingTemplate: appsync.MappingTemplate.fromString(`
        {
          "version": "2018-05-29",
          "operation": "PutItem",
          "key": {
            "id": $util.dynamodb.toDynamoDBJson($util.autoId())
          },
          "attributeValues": {
            "messageLog": $util.dynamodb.toDynamoDBJson([]),
            "activePlayer": $util.dynamodb.toDynamoDBJson($context.arguments.player1Id),
            "participants": $util.dynamodb.toDynamoDBJson([$context.arguments.player1Id, $context.arguments.player2Id]),
            "createdAt": $util.dynamodb.toDynamoDBJson($util.time.nowISO8601())
          }
        }
      `),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem()
    });

    // Send Instruction Resolver
    sfnDs.createResolver('SendInstruction', {
      typeName: 'Mutation',
      fieldName: 'sendInstruction',
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
        #if($output.taskResult)
          #return($output.taskResult.Payload)
        #end
        $util.toJson($output)
      `)
    });

    // Get Encounter Resolver
    encounterTableDS.createResolver('GetEncounter', {
      typeName: 'Query',
      fieldName: 'getEncounter',
      requestMappingTemplate: appsync.MappingTemplate.fromString(`
        {
          "version": "2018-05-29",
          "operation": "GetItem",
          "key": {
            "id": $util.dynamodb.toDynamoDBJson($context.arguments.id)
          }
        }
      `),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem()
    });

    // Output the API URL and API Key
    new cdk.CfnOutput(this, 'GraphQLApiUrl', {
      value: api.graphqlUrl
    });

    new cdk.CfnOutput(this, 'GraphQLApiKey', {
      value: api.apiKey || ''
    });
  }
}