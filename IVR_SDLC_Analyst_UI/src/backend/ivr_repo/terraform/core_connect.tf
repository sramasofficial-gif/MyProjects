/*
Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/
/*
resource "aws_connect_instance" "saml_instance_new" {
  # required
  identity_management_type = var.identity_management_type
  outbound_calls_enabled   = true
  inbound_calls_enabled    = true
  #instance_alias           = join("-", [var.environment, local.region_shortnames[var.region], var.instance_alias, data.aws_caller_identity.current.account_id])
  instance_alias           = join("-", ["rb", var.environment, var.application-name])
  contact_flow_logs_enabled = true
}

*/


resource "aws_connect_instance" "saml_instance" {
  # required
  identity_management_type = var.saml_identity_management_type
  outbound_calls_enabled   = true
  inbound_calls_enabled    = true
  instance_alias           = join("-", [var.tags.businessunit, "pci", var.tags.environment, "connect"])
#instance_alias           = join("-", [var.environment, local.region_shortnames[var.region], var.saml_instance_alias, data.aws_caller_identity.current.account_id])
  contact_flow_logs_enabled = true
  tags = {
      environment                       = var.tags.environment
      project-id                        = var.tags.project-id
      application-name                  = var.tags.application-name
      applicationname                   = var.tags.applicationname
      application-owner                 = var.tags.application-owner
      application-role                  = var.tags.application-role
      businessunit                      = var.tags.businessunit
      compliance                        = var.tags.compliance
      data-classification               = var.tags.data-classification
      SCOA                              = var.tags.SCOA
      PII                               = var.tags.PII
      costcenter                        = var.tags.costcenter
    }
  }

