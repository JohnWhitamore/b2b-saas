# AWS

### Intro

AWS (like GCP, Azure, etc) is great because it offers an enormous range of services and configurations in an environment which is secure and automatable. In this note, we're going to do only the essentials:

- Learn some names of things
- Understand Identity and Access Management
- Set up a user
- Set ourselves up so that we can use the command line instead of clicking around inside the AWS website

### Names of things

We're going to come across the terms "user", "role" and "STS". Let's get them clear upfront.

A “user” is an identity that does things. It can represent a living, breathing human, a container, a CI pipeline - anything that needs permission to act. The same human might operate under multiple “users,” depending on which identity best expresses the task at hand.

A “role” is a bundle of permissions, defined independently from users. A CI pipeline needs a bundle of permissions to do pipeline things. A software engineer needs a bundle of permissions to maintain an API. These bundles of permissions are expressed as roles.

The Security Token Service (STS) allows a user to assume a role - temporarily stepping into its permissions. Assuming the role yields credentials which typically 1–12 hours depending on configuration. The motivation for issuing credentials which are temporary (and not permanent) is to reinforce good security boundaries and lifecycle clarity.

The result: A user assumes a role to do things, borrowing exactly the permissions they need, just for the duration required.

### IAM: Identity and Access Management

_What is IAM?_

IAM allows us to:

1. define users, groups and roles
2. attach policies that govern access - written in JSON
3. control fine-grained permissions across AWS services

| Element                 | Purpose                                                  | Remarks                                                   |
| ----------------------- | -------------------------------------------------------- | --------------------------------------------------------- |
| **Admin User**          | Root identity for setup + teardown                       | Use MFA, no programmatic access                           |
| **Service Roles**       | Attach to EKS, EC2, Lambda, etc. for runtime permissions | Name by service and intent: `eksNodeRole`, `s3UploadRole` |
| **IAM Groups**          | Bundle policies for similar users (e.g. devs, analysts)  | Optional - use when collaborating with others             |
| **Policies**            | Declarative JSON rules                                   | Create modular, least-privilege policies per step         |
| **Trust Relationships** | Allow one role or account to assume another              | Key for role-chaining, cross-account access               |

Example: define a role called `S3UploadRole` and a JSON policy like this: 

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": ["arn:aws:s3:::your-bucket-name/*"]
    }
  ]
}
```

_Open IAM dashboard_

1. Sign in to AWS console: https://console.aws.amazon.com/
2. Open IAM service: type "IAM" in the search box and select "IAM: manage access to AWS resources"

You will see that the IAM dashboard contains many useful ways to configure the setup. We're focused on the essentials, so we'll just use it to create a user.

### Create a user

We'll create an admin user for the project with admin privileges.

1. Click Users (sidebar menu on the left)
2. Click Create User (orange button top-right)
3. Define a User name for admin e.g. `project-admin`
4. Select "Attach policies directly" (brings up a long menu of permissions policies)
5. Select `AdministratorAccess`: gives full access across AWS so only for founders, CTOs, sole bootstrappers etc
6. Click `Next`: bottom-right of screen (scroll down)
7. Optionally attach one or more tag to the user for traceability, cost mappings and automation hooks. e.g. several users working on the same part of a project might have the project name as a tag. A tag is a key-value pair, e.g. `project: project-x`. 

Once the tags have been created (or skipped), the user has been created and the user profile can be reviewed.

### Set up to use the CLI

First, install the AWS CLI and set up a user to use it.

1. Click on this link: [Installing or updating to the latest version of the AWS CLI - AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Install the version of AWS CLI which is appropriate for your local machine
3. Use the IAM dashboard to create a new user, exactly as before, but this time a) name the user `cli-operator` and b) select `PowerUserAccess` instead of `AdministratorAccess`. It's a good compromise between full admin privileges and read-only access. We use named CLI profiles (like `cli-operator`) to make identity modular, so that we can switch between projects, environments and so on without re-writing config files. 
4. Add a tag of the form `project-name:cli-operator` to the newly created user.

Next, set up security credentials for the user:

1. Go to the user's "Security Credentials" tab
2. Click "Create access key" and follow the instructions. Take care to copy the Access Key and Secret Access Key securely the first time as they cannot be retrieved later.
3. Use the command line (e.g. Power Shell) to run `aws configure --profile cli-operator`
4. Paste in the Access Key and then the Secret Access Key
5. Provide answers to the region name e.g. `eu-west-2` for sunny London and `json` or `table` for the default output format.
6. Confirm everything has worked correctly by running `aws sts get-caller-identity --profile cli-operator` 

