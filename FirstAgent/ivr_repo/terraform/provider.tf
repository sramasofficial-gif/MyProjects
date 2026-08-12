provider "aws" {
  region = var.region

  assume_role {
    role_arn = "arn:aws:iam::${var.account-id}:role/${var.role-id}"
  }
  default_tags {
    tags = {
      applicationname = "RB-PCI-RBCONNECT"
    }
  }
}

provider "awscc" {
  region         = "ca-central-1"
  assume_role = {
          role_arn = "arn:aws:iam::${var.account-id}:role/${var.role-id}"
          external_id = "aws-account"
      }
}

terraform {
  required_providers {

    aws = {
      source  = "hashicorp/aws"
      #version = "5.1.0"
      version = "6.19.0"
    }

    awscc = {
      source = "hashicorp/awscc"
      version = "1.68.0"
    }

    artifactory = {
      source  = "registry.terraform.io/jfrog/artifactory"
      #version = "9.5.1"
    }

    http = {
      source = "hashicorp/http"
      version = "3.4.0"
    }
  }
}

provider "http" {
  # Configuration options
  
}

# Configure the Artifactory provider
provider "artifactory" {
  url           = "${var.artifactory_url}/artifactory"
  #access_token  = var.artifactory_access_token
  access_token  = "${var.artifactory_access_token}"
  check_license = false
 }
