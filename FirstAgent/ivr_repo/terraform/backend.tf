terraform {
  backend "remote" {
    hostname = "prd.tfe.rogers.com"
    organization = "aws"

    workspaces {
      name = "aws-rb-ccr-pci-dev"
    }
  }
}



