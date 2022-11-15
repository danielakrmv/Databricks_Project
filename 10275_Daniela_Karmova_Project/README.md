# UAPC TPL - Template Project for UAPC

This project serves as a template for UAPC applications.

## Prerequisites

1. DevOps pipeline variables within the pipeline definitions, i.e. `azure-pipeline-<test|deploy|undeploy>.yaml`, need to be set correctly for your project:

   - `PROJECT_ID` is the short id for your project
   - `PROJECT_COUNTRY` is the country abbreviation of your project (usually `int` but `xx` for the TPL project)

2. Within the pipeline definitions, template calls for components that are not needed have to be removed as well as the pipeline parameters associated, e.g. `deployKubernetes` and `undeployKubernetes`.
For components that are needed, the template parameters may need to be adjusted for your project, e.g.
   - `databricksWorkspaceUrl` is the Databricks workspace URL that needs to be replaced with your project's Databricks workspace URLs for all three stages in the deploy and undeploy pipelines.

3. DevOps environments (`DEV`, `DVB`, `QAS`, `PRD`) must be created, preferably with approval checks and branch control
   (e.g. only allow deployments on QAS and PRD from `/refs/heads/master`) in place.
   Details can be found here [Azure DevOps Repository Setup](https://confluence.schwarz/x/8s_ZBw)

4. The three DevOps Pipelines, `azure-pipeline-<test|deploy|undeploy>.yaml`, must be created in the DevOps UI.
   Details can be found here [Azure DevOps Repository Setup](https://confluence.schwarz/x/8s_ZBw)

5. DevOps Branch Protection and Build Validation should be enabled for the `develop` and `master` branches in order to avoid accidental merges to these special branches, see [Azure DevOps Repository Setup](https://confluence.schwarz/x/8s_ZBw).

## Stages & Configuration

We differentiate between the four stages

- **DEV**: Development Stage,
- **DVB**: Development Backup Stage,
- **QAS**: Quality Assurance Stage,
- **PRD**: Production Stage,

which correspond to the respective infrastructure stages (e, b, q, p).

DVB is a special stage which serves as a fallback for DEV when a platform deployment unintentionally introduces bugs or erros in DEV! For more information, see [UAPC Platform Updates](https://confluence.schwarz/x/z4uwD).

Our project configuration is stored in the `conf` directory where we have

- `COMMON.conf`, our base configuration, which is used in all stages and the integration test,
- `<DEV|DVB|QAS|PRD>.conf`, the stage-specific configurations that can be used to add and/or overwrite entries from the base configuration,
- `INTEGRATION_TEST_{DEV|DVB}.conf`, the "stage-specific" configuration that is used for the integration test deployment.

The configuration is written in the [HOCON](https://github.com/lightbend/config) format.

For the deployment, we use the `create_config.py` script to merge the config files and boil it down to a single JSON file:

```bash
python create_config.py --stage <DEV|DVB|QAS|PRD|INTEGRATION_TEST_{DEV|DVB}> --format json conf.json
```

## Development & Deployment Workflow

This repository is tailored to a specific development and deployment workflow that we recommend using. For more information, see [Development & Deployment Workflow](https://confluence.schwarz/x/DixDCQ).

## Pipelines

All pipelines found in the root directory, that is `azure-pipeline-<test|deploy|undeploy>.yaml` act as the entrypoint and execute the respective component-specific pipeline templates found in the component directories `<component>/azure-pipeline/<test|deploy|undeploy>.yaml`.

Note that the component-specific pipeline templates are not executed in the order given in the pipeline definitions. Instead, they will be executed simultaneously. If the execution order matters to you, you can resort to multiple manual pipeline runs where you select only a subset of components (see [Deployment Pipeline](#deployment-pipeline)) each time.

### Test Pipeline

The *Test Pipeline* can be triggered manually on a commit or a branch. If the Azure DevOps project is configured correctly, it will also be required to run successfully before a pull request (PR) can be merged.

Usually, the test pipeline performs unit tests, code quality checks and dependency vulnerability scanning. For a more detailed description, see the component-specific READMEs.

#### SonarQube

The code quality reports are usually sent to SonarQube where they can be inspected. For more information, see [Automatic Code Analysis - SonarQube](https://confluence.schwarz/x/QZ0oBw).

#### Dependency Scanner (Snyk)

Dependency scanning and monitoring is performed on open source dependencies in build artifacts and containers. Reports are usually sent to Snyk where they can be inspected. For more information, see [Dependency Scanner - Snyk](https://confluence.schwarz/x/C7fnBg).

### Deployment Pipeline

The *Deployment Pipeline*, as a first step, generates a *Deployment Label* from the branch name, which is used to identify a specific deployment as well as it enables the pipeline to overwrite a potentially existing deployment with the same label on the same stage (*DEV/DVB/QAS/PRD*). As a result, a deployment is always linked to a Git branch.

By convention, the regular *DEV/DVB* deployment should always be performed from the `develop` branch while the regular *QAS* and *PRD* deployments should be performed from the `master` branch.

That is also why we provide automatic pipeline runs for all commits on `develop` (deployment to *DEV/DVB*) and `master` (deployment to *QAS*), which deploy *all components*.

For manual triggers of the deployment pipelines you can select

- the **stage** to deploy to,
- the **components** to be deployed.

Manual deployment pipeline runs will usually be performed for

- *PRD* deployments and
- deployments of feature branches (usually to *DEV/DVB*) for testing purposes.

For a more detailed description of the tasks performed during deployment, see the component-specific READMEs.

### Undeployment Pipeline

The *Undeployment Pipeline*, just like the deployment pipeline, generates the corresponding *Deployment Label* from the branch name in order to select the deployment to be removed. That means that the undeployment of a specific deployment needs to be triggered from the same branch.

For manual triggers of the undeployment pipelines you can select

- the **stage** to undeploy from,
- the **components** to be undeployed.

The undeployment pipeline will undo the tasks of the deployment pipeline but it will not remove artifacts (Python Wheels or container images) from the Artifactory. It will also not remove any data generated by a job (e.g. Databricks or a Kubernetes Pod).
