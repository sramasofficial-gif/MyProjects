module "ccrpci" {
  source = "../dev/modules/"
  tags                          = var.tags
  environment                   = var.tags.environment

  artifactory_env_path                  = var.artifactory_env_path
  artifact_hash_layer                   = var.artifact_hash_layer   
  artifactory_access_token              = var.artifactory_access_token
  artifactory_user                      = var.artifactory_user
  artifactory_url                       = var.artifactory_url
  rbconnect-pci-getaccountbycard-lambda = var.rbconnect-pci-getaccountbycard-lambda
  rbconnect-pci-changepin-lambda        = var.rbconnect-pci-changepin-lambda
  rbconnect-pci-getaccountbyani-lambda  = var.rbconnect-pci-getaccountbyani-lambda
  rbconnect-pci-verifypin-lambda        = var.rbconnect-pci-verifypin-lambda
  rbconnect-pci-voicemailcopy-lambda    = var.rbconnect-pci-voicemailcopy-lambda 
  rbconnect-pci-voicemailcreatetask-lambda = var.rbconnect-pci-voicemailcreatetask-lambda
  rbconnect-pci-voicemailtranscriber-lambda = var.rbconnect-pci-voicemailtranscriber-lambda

  getaccountbycardlambda_sg   = var.getaccountbycardlambda_sg
  getaccountbyANI_sg          = var.getaccountbyANI_sg
  verifypin_sg                = var.verifypin_sg
  changepin_sg                = var.changepin_sg
  lambda-exec-role-arn          = var.lambda-exec-role-arn
  lambda_insights_layer_arn     = var.lambda_insights_layer_arn
}

output "ccrpci" {
  value     = module.ccrpci
  sensitive = true
}

output "ccrpci_aws_account_id" {
  value = module.ccrpci.account_id
}


output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "assume_role" {
  value = "arn:aws:iam::${var.account-id}:role/${var.role-id}"
}


