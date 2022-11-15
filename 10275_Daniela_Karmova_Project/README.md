# UAPC AIACAD Project - Final Project for Python Academy
## Description of the problem
This project should detect inconsistencies in the data: missing bon rows. There is a field in the data that relates to the line in the receipt. Its name is "bon_zeile".
Every bon should have all its rows: the line count should not be broken by missing numbers. Should use the sales data for Bulgaria (mandant_id = 8) from the last 5 weeks to determine the 10 most purchased and 10 least purchased articles (defined by the art_id/kl_art_id field) based on the amount (not price/turnover). 
Making separate comparisons for articles that are sold per unit and those sold by their weight.

## Architecture
- **total quantity for art per unit and weight etl job**: this job gets the sales data of Kaufland stores in Bulgaria(mandant_id = 8), filters the data for the last 5 weeks, filters only the valid bons(without missing rows), aggregates data and add columns with description of articles for better illustration in the end of my analysis. Finally it loads the data to a data storage.
- **ten top and flop articles per weight etl job**: this job depends on the total quantity for art per unit and weight etl job, reads from the cleared data, filters only those articles that are sold per weight ("einh_id" = "KG"), group by "kl_art_id", find total quantity in kg per each article and then finds the ten most purchased and ten less purchased articles per weight. Finally it loads the data to a data storage.
- **ten top and flop articles per unit etl job**: this job depends on the top total quantity for art per unit and weight etl job, reads from the aggregates data, filters only those articles that are sold per unit ("einh_id" = "ST"), group by "kl_art_id", find total quantity per each article and then finds the ten most purchased and ten of the least purchased articles per weight. Finally it loads the data to a data storage. 
- **vis top and flop articles per weight evl job**: this job depends on the 10 top and flop articles per weight etl job, reads from the aggregates data and than visualize top 10 and flop 10 articles that are sold per weight. 
- **vis top and flop articles per unit evl job**: this job depends on the 10 top and flop articles per unit etl job, reads from the aggregates data and than visualize top 10 and flop 10 articles that are sold per unit

## Stages & Configuration
We differentiate between the four stages
- **DEV**: Development Stage,
- **DVB**: Development Backup Stage,
- **QAS**: Quality Assurance Stage,
- **PRD**: Production Stage
which correspond to the respective infrastructure stages (e, b, q, p).

DVB is a special stage which serves as a fallback for DEV when a platform deployment unintentionally introduces bugs or erros in DEV! For more information, see UAPC Platform Updates .
Our project configuration is stored in the conf directory where we have:

- `COMMON.conf`, our base configuration, which is used in all stages and the integration test,
- `<DEV|DVB|QAS|PRD>.conf`, the stage-specific configurations that can be used to add and/or overwrite entries from the base configuration,
- `INTEGRATION_TEST_{DEV|DVB}.conf`, the "stage-specific" configuration that is used for the integration test deployment.

For the deployment, we use the `create_config.py` script to merge the config files and boil it down to a single JSON file:

## Development & Deployment Workflow

This repository is tailored to a specific development and deployment workflow that we recommend using. For more information, see [Development & Deployment Workflow](https://confluence.schwarz/x/DixDCQ).

## Pipelines

All pipelines found in the root directory, that is `azure-pipeline-<test|deploy|undeploy>.yaml` act as the entrypoint and execute the respective component-specific pipeline templates found in the component directories `<component>/azure-pipeline/<test|deploy|undeploy>.yaml`.

Note that the component-specific pipeline templates are not executed in the order given in the pipeline definitions. Instead, they will be executed simultaneously. If the execution order matters to you, you can resort to multiple manual pipeline runs where you select only a subset of components (see [Deployment Pipeline](#deployment-pipeline)) each time.

### Test Pipeline

The *Test Pipeline* can be triggered manually on a commit or a branch. If the Azure DevOps project is configured correctly, it will also be required to run successfully before a pull request (PR) can be merged.

Usually, the test pipeline performs unit tests, code quality checks and dependency vulnerability scanning. For a more detailed description, see the component-specific READMEs.

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
