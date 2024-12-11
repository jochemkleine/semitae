import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as child_process from 'child_process';
import { Construct } from 'constructs';
import * as fs from 'fs';
import * as path from 'path';

export class LambdaLayerBuilder {
    private readonly scope: Construct;
    private readonly layerId: string;
    private compatibleRuntimes: lambda.Runtime[] = [
        lambda.Runtime.PYTHON_3_9,
        lambda.Runtime.PYTHON_3_10,
        lambda.Runtime.PYTHON_3_11,
    ];

    constructor(scope: Construct, layerId: string) {
        this.scope = scope;
        this.layerId = layerId;
    }

    public createLayerFromPackage(packageName: string, description?: string): lambda.LayerVersion {
        const layerDir = 'lambda_layer';
        const pythonDir = path.join(layerDir, 'python');

        // Create directories if they don't exist
        if (!fs.existsSync(pythonDir)) {
            fs.mkdirSync(pythonDir, { recursive: true });
        }

        try {
            // Create a virtual environment
            child_process.execSync(
                `python3 -m venv venv && \
        source venv/bin/activate && \
        pip install ${packageName} --platform manylinux2014_x86_64 --target ${pythonDir} --only-binary=:all: --implementation cp --python-version 3.9 --abi cp39 && \
        deactivate`,
                { stdio: 'inherit', shell: '/bin/bash' }
            );

            // Create and return the layer
            return new lambda.LayerVersion(this.scope, this.layerId, {
                code: lambda.Code.fromAsset(layerDir),
                compatibleRuntimes: this.compatibleRuntimes,
                description: description ?? `Layer containing ${packageName} package and its dependencies`,
            });
        } finally {
            // Cleanup temporary files
            const filesToClean = [layerDir, 'venv'];
            filesToClean.forEach(file => {
                if (fs.existsSync(file)) {
                    fs.rmSync(file, { recursive: true, force: true });
                }
            });
        }
    }

    public setCompatibleRuntimes(runtimes: lambda.Runtime[]): void {
        this.compatibleRuntimes = runtimes;
    }
}