
#### Artifactory 
variable "artifactory_url" {
  default = ""
  description = "Artifactory URL"
}


variable "artifactory_access_token" {
 type = string
 description = "Artifactory Access Token"
sensitive = true
}

variable "artifactory_user" {
 type = string
  default = ""
 description = "Artifactory user"

}

variable "artifact_hash_layer" {
  description = "Hashed or versioned path to the Lambda layer ZIP in Artifactory"
  type        = string
}

variable "artifactory_env_path" {
  description = "Environment-specific path segment in Artifactory (e.g. qa-ado)"
  type        = string
}


variable "rbconnect-pci-getaccountbycard-lambda" {
  default     = ""
  type        = string
  description = "rb-ccrpci-GetAccountbyCard-lambda"
}

variable "rbconnect-pci-getaccountbyani-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-getaccountbyani-lambda"
}

variable "rbconnect-pci-changepin-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-changepin-lambda"
}

variable "rbconnect-pci-verifypin-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-verifypin-lambda"
}

variable "rbconnect-pci-voicemailcopy-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-voicemailcopy-lambda"
}

variable "rbconnect-pci-voicemailcreatetask-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-voicemailcreatetask-lambda"
}

variable "rbconnect-pci-voicemailtranscriber-lambda" {
  default     = ""
  type        = string
  description = "rbconnect-pci-voicemailtranscriber-lambda"
}

variable "environment" {
  default     = ""
  type        = string
  description = "Environment"
}
variable "account-id" {
  default     = ""
  type        = string
  description = "AWS account ID corresponding to the environment"
}

variable "role-id" {
  default     = ""
  type        = string
  description = "AWS role ID which has the required permission for the resources to be deployed"
}

variable "region" {
  default     = "ca-central-1"
  type        = string
  description = "Region where the infrastructure will be deployed"
}

variable "tags" {
  type = object({
    environment         = string
    project-id          = string
    application-owner   = string
    data-classification = string
    application-id      = string
    application-role    = string
    application-name    = string
    PII                 = string
    compliance          = string
    SCOA                = string
    TFE                 = string
    businessunit        = string
    otl-value           = string
    task-code-value     = string
    applicationname     = string
    costcenter          = string
    application-prefix  = string
  })
}

########################################################
###             Connect related variables           ###
########################################################

variable "ivr_id" {
  default     = "tfdemo"
  type        = string
  description = "The name of the functional alias descriptor of the instance"
}

variable "instance_alias" {
  default     = "app"
  type        = string
  description = "Alias name of the instance"
}

variable "identity_management_type" {
  default     = "Connect_Managed"
  type        = string
  description = "Identity management type; Accepted values SAML, Connect_Managed, Existing_Directory"
  validation {
    condition     = contains(["SAML", "CONNECT_MANAGED", "EXISTING_DIRECTORY"], var.identity_management_type)
    error_message = "Argument \"environment\" must be one of \"SAML\", \"Connect_Managed\", \"Existing_Directory\" ."
  }
}

variable "saml_instance_alias" {
  default     = "app"
  type        = string
  description = "Alias name of the instance"
}

variable "saml_identity_management_type" {
  default     = "Connect_Managed"
  type        = string
  description = "Identity management type; Accepted values SAML, Connect_Managed, Existing_Directory"
  validation {
    condition     = contains(["SAML", "CONNECT_MANAGED", "EXISTING_DIRECTORY"], var.saml_identity_management_type)
    error_message = "Argument \"environment\" must be one of \"SAML\", \"Connect_Managed\", \"Existing_Directory\" ."
  }
}

variable "common_name" {
  default     = "Connect Dev"
  type        = string
  description = "A common name for amazon connect resource"
}

variable "contact_flow_type" {
  default     = "CONTACT_FLOW"
  type        = string
  description = "Type of contact flow"
}

variable "promtID_arn" {
  type        = string
  description = "ARN of the promtID for the AgentQFlow contact-flow"
  default     = "arn:aws:connect:ca-central-1:489551464761:instance/c19e7122-a4f1-4159-a280-0b8eb60eba41/prompt/66832713-49dd-41f3-90a6-03d336f18114"
}

variable "Music_Pop_ThisAndThatIsLife_Inst_arn" {
  type        = string
  description = "ARN of the promtID for the AgentQFlow contact-flow"
  default     = "arn:aws:connect:ca-central-1:489551464761:instance/c19e7122-a4f1-4159-a280-0b8eb60eba41/prompt/4379e94f-14ca-482d-822c-712907d2c146"
}

variable "connect_instance_id" {
  description = "Amazon Connect instance ID"
  type        = string
  default     = "c19e7122-a4f1-4159-a280-0b8eb60eba41"
}

variable "s3_bucket" {
  description = "S3 bucket name for storing contact flows and modules"
  type        = string
  default     = "connect-admin-objects"
}

variable "operating_hours_dir" {
  description = "Directory that contains JSON files for operating hours"
  default     = "./exports/resources/operating-hours"
}

variable "queues_dir" {
  description = "Directory that contains JSON files for connect queues"
  default     = "./exports/resources/queues"
}

variable "quick_connect_dir" {
  description = "Directory that contains JSON files for connect quick-connects"
  default     = "./exports/resources/quick-connects"
}

variable "routing_profiles_dir" {
  description = "Directory that contains JSON files for connect routing profiles"
  default     = "./exports/resources/routing-profiles"
}


variable "content_source" {
  description = "source for the s3 object"
  type        = string
  default     = ""
}


variable "env" {
  type    = string
  default = ""
}


variable "repo" {
  type        = string
  description = "The name of the repository hosting the code for this deployment"
  default     = null
}

variable "capability_id" {
  type        = string
  description = "The name of the capability descriptor for the microservice"
  default     = null
}

# TODO * Try creating the var manually and see if it takes. Maybe the passed in var is diff somehow
variable "contact_flow_modules_state" {
  type        = list(string)
  description = "Array passed in from build script that contains all contact flow modules that are currently in state file. Used to determine whether or not to provision a slug module"
  default     = []
}

variable "contact_flows_state" {
  type        = list(string)
  description = "Array passed in from build script that contains all contact flows that are currently in state file. Used to determine whether or not to provision a slug module"
  default     = []
}

variable "connect_instance_arn" {
  type        = string
  description  = "amazon connect instance arn"
  default      = ""
}


############################################################################
#                         S3 variables                                      #
###########################################################################


variable "enable_bucket_versioning" {
  description = "Enable versioning on the bucket"
  type        = bool
  default     = false
}

variable "enable_public_access_block" {
  description = "Block all public access to the bucket"
  type        = bool
  default     = false
}

variable "enable_ownership_controls" {
  description = "Enable ownership controls on the bucket"
  type        = bool
  default     = false
}

variable "s3-objects" {
  type        = list(any)
  description = "List of folders that for aws connect s3 bucket"
}

variable "s3-objects-cnx" {
  description = "List of S3 objects to upload to the CNX export bucket"
  type        = list(object({
    key          = string
    source       = string
    content_type = optional(string)
  }))
  default     = []
}

variable "create-additional-bucket-policy-main" {
  type        = bool
  default     = false
  description = "Whether to create s3 bucket policy statement in addition to the default."
}

variable "s3-bucket-policy-json-file" {
  type        = string
  default     = ""
  description = "Provide the S3 bucket policy json file name."
}

variable "kms-key-arn" {
  default     = ""
  type        = string
  description = "Please enter KMS key ARN for encryption(if not provided it will take aws default KMS key aws/s3)"
}

############################################################################################
##                     Event bridge                                                        ##
##########################################################################################


variable "create_event_targets" {
  type        = bool
  default     = false
  description = "Whether to create event targets"
}

variable "create_event_bus" {
  type        = bool
  default     = false
  description = "Whether to create a custom EventBridge event bus"
}

variable "create_event_rules" {
  type        = bool
  default     = false
  description = "Whether to create EventBridge rules"
}

#variable "event_bus_name" {
#  type        = string
#  description = "Name of the custom EventBridge event bus"
#}

variable "rules" {
  description = "Map of EventBridge rules to create"
  type = map(object({
    name            = string
    name_prefix         = optional(string)
    description     = optional(string)
    event_pattern       = optional(any)  
    event_bus_name  = optional(string)
    schedule_expression = optional(string)
    state           = optional(string)
    role_arn        = optional(string)
  }))
  default = {}
}

variable "targets" {
  description = "Map of EventBridge rule targets to create"
  type = map(object({
    name               = string
    rule_name          = string
    arn                = string
    target_id          = string
    role_arn           = string
    event_bus_name     = string
    partition_key_path = optional(string)
    input              = optional(string)
    input_path         = optional(string)
    input_transformer = optional(object({
      input_template  = string
      input_paths_map = map(string)
    }))
  }))
  default = {}
}


#################################################################################
#####                  Event pipe                                           ####
################################################################################

variable "create_pipes" {
  description = "Controls whether EventBridge Pipes should be created"
  type        = bool
  default     = false
}

variable "pipes" {
  description = "Map of EventBridge Pipes and their configurations"
  type = map(object({
    name          = string
    role_arn      = string
    source        = string
    target        = string
    desired_state = string

    disable_default_cloudwatch_logging = optional(bool, false)

    source_parameters = object({
      kinesis_stream_parameters = object({
        batch_size                         = number
        starting_position                  = string
        maximum_batching_window_in_seconds = optional(number)
        maximum_record_age_in_seconds      = optional(number)
        maximum_retry_attempts             = optional(number)
        on_partial_batch_item_failure      = optional(string)
        parallelization_factor             = optional(number)
        starting_position_timestamp        = optional(string)
        dead_letter_config = optional(object({
          arn = optional(string)
        }))
      })
      filter_criteria = object({
        filter = list(object({
          pattern = any
        }))
      })
    })

    target_parameters = object({
      input_template = string
      eventbridge_event_bus_parameters = object({
        detail_type = string
        source      = string
        resources   = list(string)          # <-- CHANGE from string to list(string)
        endpoint_id = optional(string)
        time        = optional(string)
      })
    })

    log_configuration = optional(any)
  }))
  default = {}
}



##############################################################################
#                          Global Variables                                  #
##############################################################################



variable "availability_zones" {
  type        = list(string)
  description = "Provide the list of availability zones if you wish to split the nodes"
  default     = []
}

variable "environment-variables" {
  type        = map(any)
  default     = {}
  sensitive   = true
  description = "A map that defines environment variables for the Lambda function."
}

variable "artifactory_secret_arn" {
  type = string
  default = ""
}

variable "getaccountbycardlambda_sg" {
  type = list(string)
  description = "ccrpci auth lambda Security Group"
}


variable "getaccountbyANI_sg" {
  type = list(string)
  description = "ccrpci auth lambda Security Group"
}

variable "verifypin_sg" {
  type = list(string)
  description = "ccrpci auth lambda Security Group"
}

variable "changepin_sg" {
  type = list(string)
  description = "ccrpci auth lambda Security Group"
}

variable "lambda-exec-role-arn" {
  default     = ""
  type        = string
  description = "Provide the lambda function execution role ARN."
}

variable "layers" {
  default     = []
  type        = list(string)
  description = "List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function."
}

variable "lambda_insights_layer_arn" {
  description = "ARN of the Lambda Insights layer"
  type        = string
}

############################################################################################
##                     Amazon Connect Data Tables                                        ##
##########################################################################################


variable "data_tables" {
  type = map(object({
    name             = string
    description      = optional(string)
    time_zone        = optional(string)
    value_lock_level = optional(string)
    attributes = list(object({
      name        = string
      value_type  = string   # TEXT|NUMBER|BOOLEAN|TEXT_LIST|NUMBER_LIST
      primary     = optional(bool)
      description = optional(string)
    }))
  }))
}

