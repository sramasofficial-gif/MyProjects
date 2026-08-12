/*
Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/



data "aws_caller_identity" "current" {}

data "local_file" "files" {
  for_each = fileset("./exports/resources/operating-hours", "*.json")
  filename = "${path.module}/exports/resources/operating-hours/${each.value}"
}

data "aws_connect_hours_of_operation" "basic_hours" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "Basic Hours"
}

data "aws_connect_contact_flow" "basic_outbound" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "Default outbound"
}

data "aws_connect_contact_flow" "cfOutboundWhispher" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfOutboundWhisper"
}

data "aws_connect_contact_flow" "cfrogersPinChangeQuickConnect" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfrogersPinChangeQuickConnect"
}

data "aws_connect_contact_flow" "cfInCallPinValidation_En" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfInCallPinValidation_En"
}

data "aws_connect_contact_flow" "cfInCallPinValidation_Fr" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfInCallPinValidation_Fr"
}

data "aws_connect_contact_flow" "cfFraudInvestigatorQuickConnect" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfFraudInvestigatorQuickConnect"
}

data "aws_connect_contact_flow" "cfDefaultQueueTransfer" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfDefaultQueueTransfer"
}

data "aws_connect_contact_flow" "cfBalTransferQC_EN" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfBalTransferQC_EN"
}

data "aws_connect_contact_flow" "cfProductSwitchQC_EN" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfProductSwitchQC_EN"
}

data "aws_connect_contact_flow" "cfProductSwitchQC_Fr" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfProductSwitchQC_Fr"
}

#data "aws_connect_contact_flow" "cfLegalDisclaimer" {
#  instance_id = aws_connect_instance.saml_instance.id
#  name        = "cfLegalDisclaimer"
#}

data "aws_connect_contact_flow" "cfInCallStepUpAuthentication_EN" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfInCallStepUpAuthentication_EN"
}

data "aws_connect_contact_flow" "cfInCallStepUpAuthentication_FR" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfInCallStepUpAuthentication_FR"
}

data "aws_connect_contact_flow" "cfBackOfficeTaskFlow" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "cfBackOfficeTaskFlow"
}

data "aws_connect_queue" "BasicQueue" {
  //for_each = local.decode_quick_connect
  instance_id = aws_connect_instance.saml_instance.id
  name        = "BasicQueue"
}


data "aws_connect_quick_connect" "example" {
  instance_id =  aws_connect_instance.saml_instance.id
  name        = "Test Chat"
}

#data "aws_connect_phone_number" "Test-oubound" {
#  instance_id = aws_connect_instance.saml_instance.id
#  phone_number = "+18335743288"
#}

## Retrieving KMS key for Kinesis streams ###
data "aws_kms_key" "kinesis_kms" {
  key_id = "alias/aws/kinesis"
}

data "aws_kms_key" "s3_kms" {
  key_id = "alias/aws/s3"
}


data "aws_kms_key" "connect" {
  key_id = "alias/aws/connect"
}

data "aws_kms_key" "s3-default-kms-key" {
  key_id = "alias/aws/s3"
}

