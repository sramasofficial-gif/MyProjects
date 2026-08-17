/*
Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/

###################################################
# S3 bucket for screen recording
###################################################


module "screen-recording" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "screenrecording"
  target-bucket                   = "" # Or leave blank if not needed
  kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  data-classification             = "restricted"
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-screenrecording.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects

  s3_lifecycle_rules = [
    {
      id                                = "screen-recording-lifecycle"
      #prefix                            = "screenrecordings/"
      transition_days                   = 180
      transition_storage_class          = "GLACIER"
      expiration_days                   = 360
      abort_incomplete_upload_days       = 5
      noncurrent_version_expiration_days = 5
      object_size_greater_than           = 0
    },
    {
    id                                  = "delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null 
    noncurrent_version_expiration_days  = null 
    transition_days                     = null 
    transition_storage_class            = null
  }
  ]
}

###################################################
# S3 bucket for call recording
###################################################

module "call-recording" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "callrecording"
  target-bucket                   = ""  #var.target-bucket # Or leave blank if not needed
  #kms-key-arn                     = data.aws_kms_key.s3_kms.id
  kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  data-classification             = "restricted"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-callrecording.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects

  s3_lifecycle_rules = [
  {
    id                                = "call-recording-lifecycle"
    #prefix                            = "callrecordings/"
    transition_days                   = 360
    transition_storage_class          = "GLACIER"
    expiration_days                   = 2550
    abort_incomplete_upload_days       = 5
    noncurrent_version_expiration_days = 5
  },
  {
    id                                  = "delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null
    noncurrent_version_expiration_days = null
    transition_days                     = null
    transition_storage_class            = null
  }
]
}


###################################################
# S3 bucket for voicemail
###################################################

module "voicemail" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "voicemail"
  target-bucket                   = ""  #var.target-bucket # Or leave blank if not needed
  #kms-key-arn                     = data.aws_kms_key.s3_kms.id
  kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  data-classification             = "restricted"
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-voicemail.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects
  create-bucket-notification      = true

  lambda-function-notification = [
    {
      id                  = "S3toAmazonconnectLambda2"
      lambda-function-arn = "arn:aws:lambda:ca-central-1:207567788052:function:rbconnect-dev-pci-voicemailcreatetask-function"
      events              = [
        "s3:ObjectCreated:Put",
        "s3:ObjectCreated:Post",
        "s3:ObjectCreated:Copy",
        "s3:ObjectCreated:CompleteMultipartUpload"
      ]
      filter-prefix       = "transcript/"
      filter-suffix       = ""
    },
    {
      id                  = "S3toTranscriber2"
      lambda-function-arn = "arn:aws:lambda:ca-central-1:207567788052:function:rbconnect-dev-pci-voicemailtranscriber-function"
      events              = [
        "s3:ObjectCreated:Put",
        "s3:ObjectCreated:Post",
        "s3:ObjectCreated:Copy",
        "s3:ObjectCreated:CompleteMultipartUpload"
      ]
      filter-prefix       = "CallRecordings/"
      filter-suffix       = ""
    }
  ]

  lambda_invocation_permissions = [
    {
      statement_id  = "AllowS3InvokeVoicemailCreateTask"
      action        = "lambda:InvokeFunction"
      function_name = "rbconnect-dev-pci-voicemailcreatetask-function"
      principal     = "s3.amazonaws.com"
      source_arn    = "arn:aws:s3:::rb-pci-dev-s3-rbconnect-restricted-voicemail"
    },
    {
      statement_id  = "AllowS3InvokeVoicemailTranscriber"
      action        = "lambda:InvokeFunction"
      function_name = "rbconnect-dev-pci-voicemailtranscriber-function"
      principal     = "s3.amazonaws.com"
      source_arn    = "arn:aws:s3:::rb-pci-dev-s3-rbconnect-restricted-voicemail"
    }
  ]
s3_lifecycle_rules = [
    {
      id                                  = "voicemail-lifecycle"
      #prefix                              = "voicemail/"
      expiration_days                     = 7
      noncurrent_version_expiration_days = 1
      abort_incomplete_upload_days       = 1
    },
    {
    id                                  = "delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null
    noncurrent_version_expiration_days = null
    transition_days                     = null
    transition_storage_class            = null
  }
  ]
}


###################################################
# S3 bucket for scheduled report
###################################################
module "scheduled-report" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "scheduledreport"
  target-bucket                   = ""  #var.target-bucket # Or leave blank if not needed
  kms-key-arn                     = ""
  #kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  data-classification             = "restricted"
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-scheduledreport.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects

  s3_lifecycle_rules = [
    {
      id                                  = "scheduled-report-lifecycle"
      #prefix                              = "scheduledreport/"
      expiration_days                     = null
      transition_days                     = 365 
      transition_storage_class            = "GLACIER"
      noncurrent_version_expiration_days = 365
      abort_incomplete_upload_days       = 1
    },
    {
    id                                  = "delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null
    noncurrent_version_expiration_days = null
    transition_days                     = null
    transition_storage_class            = null
  }
  ]
}
/*
resource "aws_s3_bucket_cors_configuration" "scheduled_report_cors" {
  bucket = module.scheduled-report.s3-bucket-name

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]
    expose_headers  = []
  }
}*/


###################################################
# S3 bucket for Restricted Emails
###################################################

module "restricted-emails" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "emails"
  target-bucket                   = ""  #var.target-bucket # Or leave blank if not needed
  #kms-key-arn                     = data.aws_kms_key.s3_kms.id
  kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  data-classification             = "restricted"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-restricted-emails.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects

  s3_lifecycle_rules = [
  {
    id                                = "restricted-emails-lifecycle"
    #prefix                            = "callrecordings/"
    transition_days                   = 360
    transition_storage_class          = "GLACIER"
    expiration_days                   = 2550
    abort_incomplete_upload_days       = 5
    noncurrent_version_expiration_days = 5
  },
  {
    id                                  = "restricted-emails-delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null
    noncurrent_version_expiration_days = null
    transition_days                     = null
    transition_storage_class            = null
  }
]
 
}

resource "aws_s3_bucket_cors_configuration" "restricted_emails_cors" {
  bucket = module.restricted-emails.s3-bucket-name

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["https://rb-pci-dev-connect.my.connect.aws*"]
    expose_headers  = []
  }
}

###################################################
# S3 bucket for Restricted attachments
###################################################

module "restricted-attachments" {
  source                          = "./modules/tfe.rogers.com/aws/s3"
  #bucket-name                    = "rogers-rbconnect-dev-cnx-export"
  bucket-number                   = "attachments"
  target-bucket                   = ""  #var.target-bucket # Or leave blank if not needed
  #kms-key-arn                     = data.aws_kms_key.s3_kms.id
  kms-key-arn                     = data.aws_kms_key.s3-default-kms-key.arn
  enable_acl                      = false
  enable_object_lock              = false
  object_ownership_mode           = "BucketOwnerEnforced"
  data-classification             = "restricted"
  environment                     = var.tags.environment
  application-owner               = var.tags.application-owner
  application-role                = var.tags.application-role
  SCOA                            = var.tags.SCOA
  project-id                      = var.tags.project-id
  compliance                      = var.tags.compliance
  application-name                = var.tags.application-name
  applicationname                 = var.tags.applicationname
  businessunit                    = var.tags.businessunit
  costcenter                      = var.tags.costcenter
  #create-additional-bucket-policy = var.create-additional-bucket-policy-cnx
  create-additional-bucket-policy = var.create-additional-bucket-policy-main
  s3-bucket-policy-json-file      = "./templates/connectS3BucketPolicy-restricted-attachments.json"
  #s3-objects                      = var.s3-objects-cnx # Optional: different set of objects

  s3_lifecycle_rules = [
  {
    id                                = "restricted-attachments-lifecycle"
    #prefix                            = "callrecordings/"
    transition_days                   = 360
    transition_storage_class          = "GLACIER"
    expiration_days                   = 2550
    abort_incomplete_upload_days       = 5
    noncurrent_version_expiration_days = 5
  },
  {
    id                                  = "restricted-attachments-delete-expired-objects-rule"
    enabled                             = true
    expired_object_delete_marker        = true
    abort_incomplete_upload_days        = 1
    expiration_days                     = null
    noncurrent_version_expiration_days = null
    transition_days                     = null
    transition_storage_class            = null
  }
]
 
}

resource "aws_s3_bucket_cors_configuration" "restricted_email_attachments_cors" {
  bucket = module.restricted-attachments.s3-bucket-name

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["https://rb-pci-dev-connect.my.connect.aws*"]
    expose_headers  = []
  }
}





