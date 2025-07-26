# AWS

_John Whitamore_

_July 2025_

### Intro

AWS (like GCP, Azure, etc) is great because it offers an enormous range of services and configurations in an environment which is secure and automatable. However, this enormous range of services and configurations can be complex to navigate for someone who simply wants to set up an account and build technology.

This note attempts to describe with clarity how - and why - to set up an AWS account in a way that is lean: no detours and no distractions. We're going to:

- Learn the names and meanings of some IAM things: users, roles, permissions and STS
- Understand Identity and Access Management ("IAM")
- Create an admin user
- Create a CLI user so that we can use the command line instead of clicking around inside the AWS website
- Understand key cloud and internet concepts: VPC, CIDR and internet gateway
- Provision the VPC
- Create subnets and internet gateway

This will give you a lean, modular setup upon which you can start to build. It's about 2 hours work if you step through it briskly. Add another hour for reading and thinking if you're new to AWS. And add another hour if you prefer to work in a more relaxed fashion. Overall, 2-4 hours work depending on circumstances.

As examples, we'll use a company name of `saasco` and a project name of `projectx` and a user name of `john`. Please change these appropriately as you develop your own project, of course.

### Names of IAM things

We're going to come across the terms "user", "role" and "STS". Let's get their meanings clear from the start.

A “user” is an identity that does things. It can represent a living, breathing human or a programmatic object such as a container or a CI pipeline. Users should normally be defined at a level that is specific to the things that they do: `john-api-maintenance` is a user representing me doing API maintenance; `ci-pipeline` is a user representing an automated CI pipeline.

A “role” is a bundle of permissions, defined independently from users. A CI pipeline needs a bundle of permissions to do pipeline things. A software engineer needs a bundle of permissions to maintain an API. These bundles of permissions are expressed as roles.

The Security Token Service (STS) allows a user to take on a role by temporarily stepping into the permissions of that role. Taking on the role yields credentials which typically last for 1–12 hours (depending on configuration). The motivation for issuing credentials which are temporary (and not permanent) is to reinforce good security boundaries and lifecycle clarity. In AWS terminology, a user _assumes_ (rather than _takes on_) a role.

The result: a user assumes a role to do things, borrowing exactly the permissions they need, just for the duration required.

### IAM: Identity and Access Management

_What is IAM?_

IAM allows us to:

1. Define users, groups and roles
2. Attach policies that govern access - written in JSON
3. Control fine-grained permissions across AWS services

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

### Create an admin user

We'll create an admin user for the project with admin privileges.

1. Click Users (sidebar menu on the left)
2. Click Create User (orange button top-right)
3. Define a User name for admin e.g. `project-admin`
4. Select "Attach policies directly" (brings up a long menu of permissions policies)
5. Select `AdministratorAccess`: gives full access across AWS so only for founders, CTOs, sole bootstrappers etc
6. Click `Next`: bottom-right of screen (scroll down)
7. Optionally attach one or more tag to the user for traceability, cost mappings and automation hooks. e.g. several users working on the same project might have the project name as a tag. A tag is a key-value pair, e.g. `project-name: projectx`. 

Once the tags have been created (or skipped), the user has been created and the user profile can be reviewed.

### Create a CLI user to use the CLI

First, install the AWS CLI:

1. Click on this link: [Installing or updating to the latest version of the AWS CLI - AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Install the version of AWS CLI which is appropriate for your local machine

Next, set up a user to use the CLI:

1. Use the IAM dashboard to create a new user, exactly as before, but this time a) name the user `cli-operator` and b) select `PowerUserAccess` instead of `AdministratorAccess`. It's a good compromise between full admin privileges and read-only access. We use named CLI profiles (like `cli-operator`) to make identity modular, so that we can switch between projects, environments and so on without re-writing config files. 
2. Add a tag of the form `projectx:cli-operator` to the newly created user.

Next, set up security credentials for the user:

1. Go to the user's "Security Credentials" tab
2. Click "Create access key" and follow the instructions. Take care to copy the Access Key and Secret Access Key securely the first time as they cannot be retrieved later.
3. Use the command line (or Power Shell) to run `aws configure --profile cli-operator`
4. Type or paste in the Access Key and then the Secret Access Key
5. Provide answers to the region name e.g. `eu-west-2` for sunny London and `json` or `table` for the default output format.
6. Confirm everything has worked correctly by running `aws sts get-caller-identity --profile cli-operator` 

### Key cloud and internet concepts

_1. VPC_

A VPC is a Virtual Private Cloud.

A VPC is a logically isolated section of a public cloud (like AWS) where you can define and control your own virtual network. Within this space, you can launch resources (EC2 instances, RDS databases, etc) and configure networking components like subnets, route tables, gateways and security groups.

We need a VPC for:

- Isolation: it gives you a private slice of the cloud, shielding your workloads from other tenants.
- Control: you define IP ranges, subnet layouts, routing rules and access controls.
- Security: you can tightly regulate inbound / outbound traffic, segment workloads and enforce least-privilege access.
- Scalability with safety: you get the elasticity of the public cloud without sacrificing architectural boundaries.

A VPC is analogous to a quiet, well-lit studio in a bustling co-working space. You benefit from the shared infrastructure whilst also being able to design your environment the way that you need it.

_2. CIDR block_

CIDR is Classless Inter-Domain Routing.

CIDR is a method for allocating IP address ranges and defining subnets. Instead of using rigid "classful" blocks (like Class A, B, C), CIDR allows you to specify IP ranges with flexible prefix lengths using notation like `192.168.0.0/24`.

We need a CIDR block for:

- Efficient IP allocation: CIDR lets you define just the right number of IPs for a subnet without over-provisioning.
- Routing aggregation: CIDR enables route summarisation, reducing the size of routing tables and improving performance.
- Subnet precision: you can define granular boundaries between public / private zones, workloads or departments.

In AWS, CIDR blocks are the scaffolding for your VPC’s IP architecture.

_3. Choosing an IP address range_

The IP address range (e.g. `192.168.0.0`) defines the starting address of your network block. A well-informed choice would take into account:

- Private vs public scope: `192.168.0.0` is part of the private IPv4 range, meaning that it's reserved for internal use. This makes it perfect for VPCs, home networks and internal SaaS infrastructure. Other private ranges include `10.0.0.0` and `172.16.0.0`.
- Avoiding conflicts: choose an IP address range that doesn't conflict with other networks you might a) peer with or b) connect to (such as VPNs or partner VPCs). For example, if your office VPN uses `192.168.1.0` then you might want to pick `192.168.100.0` to avoid collisions.
- Separation of concerns: you might want to choose one IP range (e.g. `192.168.42.0`) for a subnet that handles analytics pipelines and a different one (e.g. `192.168.85.0`) for a CI/CD pipeline.
- AWS uses `172.31.0.0/16` as a default for VPCs. For custom VPCs `10.0.0.0/16` and `192.168.x.x/16` are common starting points.

_4. Choosing a CIDR prefix length_

The number `24` in `192.168.0.0/24` is the CIDR prefix length. It defines how many bits of the IP address are reserved for the network portion. The number 24 allocates 24 bits to the network, leaving 32-24=8 bits for host addresses.

A well-informed choice of CIDR prefix length takes into account how many IP addresses you need and how you want to segment your network.

- Estimate the number of resources (EC2s, containers, RDS instances, etc.) that will live in the subnet.
- Add buffer for growth, NAT gateways, load balancers, etc.
- Consider future segmentation: smaller blocks (`/26`, `/27`) allow more granular control.

| CIDR  | Usable IPs | Common Use Case                      |
| ----- | ---------- | ------------------------------------ |
| `/30` | 2          | Point-to-point links                 |
| `/28` | 14         | Small services or dev environments   |
| `/24` | 254        | Standard subnet for apps or teams    |
| `/22` | 1022       | Larger clusters or shared services   |
| `/16` | 65,534     | Entire VPC or enterprise-scale block |

### Provision the VPC

You’ll define a CIDR block (e.g. `10.0.0.0/16`) and give the VPC the name `saasco-vpc-main`. Enter this command at the CLI (or Power Shell).

```bash
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=saasco-vpc-main}]' \
  --profile cli-operator
```

This creates the VPC and tags it with a name. You’ll get a `VpcId` in the response which you need to note down so that you can enter it in some of the subsequent commands.

Typically, a newly created VPC transitions from `"pending"` to `"available"` within a few seconds to a minute. It’s one of the faster AWS resource initializations, especially since VPCs are logical constructs rather than physical deployments.

If it’s still pending after a couple of minutes, it’s worth checking:

- That your CLI credentials are valid and not rate-limited
- That the VPC isn’t waiting on dependent resources (though it usually isn’t)
- That there’s no region mismatch or propagation delay

You can confirm its status with:

```bash
aws ec2 describe-vpcs \
  --vpc-ids YOUR_VPC_ID \
  --profile cli-operator
```

Look for `"State": "available"` in the output. If it’s still `"pending"` after 5 minutes, that’s unusual but not necessarily broken. AWS sometimes lags in surfacing state transitions via CLI.

### Create subnets and internet gateway

Even a minimal split into public and private subnets helps future-proof your architecture.

Create a public subnet:

```bash
aws ec2 create-subnet \
  --vpc-id YOUR_VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone eu-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=saasco-public-subnet-a}]' \
  --profile cli-operator
```

Create an internet gateway:

```bash
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=saasco-igw}]' \
  --profile cli-operator
```

Note down the `IgwID` (internet gateway ID) and use it to attach the internet gateway:

```bash
aws ec2 attach-internet-gateway \
  --vpc-id YOUR_VPC_ID \
  --internet-gateway-id YOUR_IGW_ID \
  --profile cli-operator
```

Once those are in place, you’ll have a lean, minimal network scaffold capable of hosting subnets, route tables and eventually services like RDS, EKS and FastAPI.

You can confirm the attachment with a quick CLI check. Here's the cleanest way:

```bash
aws ec2 describe-internet-gateways \
  --internet-gateway-ids YOUR_IGW_ID \
  --profile cli-operator
```

Look for a block like this in the output:

```json
"Attachments": [
  {
    "State": "available",
    "VpcId": "vpc-xxxxxxxxxxxxxxxxx"
  }
]
```

If `"State"` is `"available"` and the `VpcId` matches your VPC, then the gateway is successfully attached and operational.

If you see `"detached"` or no `Attachments` block at all, the gateway isn’t linked yet. In that case, you can re-run:

```bash
aws ec2 attach-internet-gateway \
  --vpc-id YOUR_VPC_ID \
  --internet-gateway-id YOUR_IGW_ID \
  --profile cli-operator
```

### Done
