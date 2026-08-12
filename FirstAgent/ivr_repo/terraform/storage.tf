/*
Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/


###################################################
# Kinesis Streams
###################################################

###################    Kinesis Module   ##################################################

module "kinesis_ctr_stream" {
  source  = "./modules/tfe.rogers.com/aws/kinesis"
  
  kinesis-stream-name   = "rb-pci-${var.tags.environment}-kds-rbconnect-ctr"
  kinesis-stream-mode   = "ON_DEMAND"
  retention-period      = 24
  shard-count           = null
  #shard-level-metrics   = []
  #kms-key-arn           = data.aws_kms_key.kinesis_kms.arn
  #kms_key_id             = data.aws_kms_key.kinesis_kms.id

  #vpc_id                = var.vpc_id
  #subnet_ids            = var.subnet_ids
  #security_group_ids    = var.security_group_ids
  #vpc_endpoint_id       = var.vpc_endpoint_id

  # Tagging metadata
  environment           = var.tags.environment
  project-id            = var.tags.project-id
  application-owner     = var.tags.application-owner
  #data-classification   = var.data_classification
  #application-id        = var.application-id
  application-role      = var.tags.application-role
  application-name      = var.tags.application-name
  applicationname       = var.tags.applicationname
  PII                   = var.tags.PII
  compliance            = var.tags.compliance
  SCOA                  = var.tags.SCOA
  TFE                   = "YES"
  businessunit          = var.tags.businessunit
  costcenter            = var.tags.costcenter
}


module "kinesis_ae_stream" {
  source  = "./modules/tfe.rogers.com/aws/kinesis"
  
  kinesis-stream-name   = "rb-pci-${var.tags.environment}-kds-rbconnect-agentevents"
  kinesis-stream-mode   = "ON_DEMAND"
  retention-period      = 24
  shard-count           = null
  #shard-level-metrics   = []
  #kms-key-arn           = data.aws_kms_key.kinesis_kms.arn
  #kms_key_id             = data.aws_kms_key.kinesis_kms.id

  #vpc_id                = var.vpc_id
  #subnet_ids            = var.subnet_ids
  #security_group_ids    = var.security_group_ids
  #vpc_endpoint_id       = var.vpc_endpoint_id

  # Tagging metadata
  environment           = var.tags.environment
  project-id            = var.tags.project-id
  application-owner     = var.tags.application-owner
  #data-classification   = var.data_classification
  #application-id        = var.application-id
  application-role      = var.tags.application-role
  application-name      = var.tags.application-name
  applicationname       = var.tags.applicationname
  PII                   = var.tags.PII
  compliance            = var.tags.compliance
  SCOA                  = var.tags.SCOA
  TFE                   = "YES"
  businessunit          = var.tags.businessunit
  costcenter            = var.tags.costcenter
}




###################################################
# Connect instance storage configuration
###################################################

resource "aws_connect_instance_storage_config" "s3_call_recording" {

  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "CALL_RECORDINGS"

  storage_config {
    storage_type = "S3"
    s3_config {
      bucket_name   = module.call-recording.s3-bucket-name
      bucket_prefix = "CallRecordings"

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }
  }
}




resource "aws_connect_instance_storage_config" "data_streaming" {

  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "CONTACT_TRACE_RECORDS"

  storage_config {
    kinesis_stream_config {
      #stream_arn = aws_kinesis_stream.contact_trace_record.arn
      stream_arn = module.kinesis_ctr_stream.kinesis-stream-arn
    }
    storage_type = "KINESIS_STREAM"
  }
}



resource "aws_connect_instance_storage_config" "agent_events" {

  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "AGENT_EVENTS"

  storage_config {
    kinesis_stream_config {
     # stream_arn = aws_kinesis_stream.contact_agent_events.arn
      stream_arn = module.kinesis_ae_stream.kinesis-stream-arn
    }
    storage_type = "KINESIS_STREAM"
  }
}


/*
# Enable Live Media Streaming configuration
resource "aws_connect_instance_storage_config" "live_media_stream" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "MEDIA_STREAMS"

  storage_config {
    kinesis_video_stream_config {
      prefix                 = "rogers"
      retention_period_hours = 3

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.kinesis_kms.arn
      }
    }
    storage_type = "KINESIS_VIDEO_STREAM"
  }
}
*/

# Enable Exported reports configuration
resource "aws_connect_instance_storage_config" "exported_reports" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "SCHEDULED_REPORTS"

  storage_config {
    s3_config {
      bucket_name   = module.scheduled-report.s3-bucket-name
      bucket_prefix = "dev"
      #encryption_config {
      #  encryption_type = "KMS"
      #  key_id          = data.aws_kms_key.connect.arn
      #}
    }
    storage_type = "S3"
  }
}


resource "aws_connect_instance_storage_config" "screen_recording" {
  instance_id = aws_connect_instance.saml_instance.id
  resource_type = "SCREEN_RECORDINGS"
 
  storage_config {
    s3_config {
      bucket_name = module.screen-recording.s3-bucket-name
      bucket_prefix = "ScreenRecordings/"
      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }
    storage_type = "S3"
  }
}
/*
resource "aws_connect_instance_storage_config" "email_storage" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "EMAIL_MESSAGES"

  storage_config {
    s3_config {
      bucket_name   = module.scheduled-report.s3-bucket-name
      bucket_prefix = "connect-email/"

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }

    storage_type = "S3"
  }
}

resource "aws_connect_instance_storage_config" "attachments_storage" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "ATTACHMENTS"

  storage_config {
    s3_config {
      bucket_name   = module.scheduled-report.s3-bucket-name
      bucket_prefix = "connect-attachments/"

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }

    storage_type = "S3"
  }
}*/

/*
resource "aws_connect_instance_storage_config" "restricted_emails_storage" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "EMAIL_MESSAGES"

  storage_config {
    s3_config {
      bucket_name   = module.restricted-emails.s3-bucket-name
      bucket_prefix = "restricted-emails/"

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }

    storage_type = "S3"
  }
}

resource "aws_connect_instance_storage_config" "restricted_attachments_storage" {
  instance_id   = aws_connect_instance.saml_instance.id
  resource_type = "ATTACHMENTS"

  storage_config {
    s3_config {
      bucket_name   = module.restricted-attachments.s3-bucket-name
      bucket_prefix = "connect-attachments/"

      encryption_config {
        encryption_type = "KMS"
        key_id          = data.aws_kms_key.connect.arn
      }
    }

    storage_type = "S3"
  }
}
*/

#########################################################################################
###########                  Cloud watch Dashboard                                  ###
#####################################################################################


resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "rbconnect-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        x    = 0
        y    = 0
        width = 12
        height = 6
        properties = {
          metrics = [
            [ "AWS/Lambda", "Invocations", "FunctionName", "rogers-rbconnect-pci-VoiceMailCopy-function" ],
            [ ".", "Errors", ".", "." ]
          ]
          period = 300
          stat   = "Sum"
          region = "ca-central-1"
          title  = "Lambda Invocations & Errors"
        }
      },
      {
        type = "log"
        x    = 12
        y    = 0
        width = 12
        height = 6
        properties = {
          query = "SOURCE '/aws/lambda/rogers-rbconnect-pci-VoiceMailCopy-function' | fields @timestamp, @message | sort @timestamp desc | limit 20"
          region = "ca-central-1"
          title  = "Latest Lambda Logs"
        }
      }
    ]
  })
}



 
