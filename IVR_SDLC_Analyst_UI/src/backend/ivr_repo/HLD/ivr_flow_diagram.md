flowchart TD
    start["Start"]
    account_lookup["AccountLookup<br>#phoneNo"]
    lookup_result["Result"]
    lookup_fail_csr["CSR"]
    lookup_fail_queue["QueueName =<br>CSR"]
    insert_ani["Insert ANI on MCNS"]
    insert_ani_inputs["Inputs:<br>Account ID"]
    account_status["Account Status<br>(XP - account details)"]
    account_status_inputs["Inputs:<br>Account ID, CustomerId"]
    status_decision["Status"]
    fraud_transfer_message["Please hold your call<br>is being transferred."]
    fraud_csr["Fraud CSR"]
    fraud_queue["QueueName =<br>FRD"]
    agency_code["Agency<br>code?"]
    agency_primary_user["Primary<br>User"]
    agency_route_selector["Yes"]
    aic_transfer["External<br>Transfer"]
    aic_queue["QueueName =<br>855-553-4541"]
    cbvds1_transfer["External<br>Transfer"]
    cbvds1_queue["QueueName =<br>855-528-5378"]
    cbvds2_transfer["External<br>Transfer"]
    cbvds2_queue["QueueName =<br>855-553-4015"]
    agency_not_primary_message["We are unable to provide information at this time.<br>The primary cardholder of your account<br>must call in for<br>further information."]
    end_call["End call"]
    mca_transfer["External<br>Transfer"]
    mca_queue["QueueName =<br>888-797-7727"]
    lgl_transfer["External<br>Transfer"]
    lgl_queue["QueueName =<br>888-323-7453"]
    tsi_transfer["External<br>Transfer"]
    tsi_queue["QueueName =<br>888-510-0694"]
    past_due["past<br>due"]
    past_due_primary_user["Primary User"]
    past_due_message["We see that your account is past due. To make a payment arrangement<br>press 1.<br><br>If you do not wish to make a payment<br>arrangement, press 2.<br>To hear these options again press, pound key."]
    payment_input["Input"]
    payment_transfer["External<br>Transfer"]
    payment_queue["QueueName =<br>888-241-7875"]
    activate_card["Activate Card"]
    activate_card_inputs["Inputs:<br>Account ID, Customer ID"]
    activate_result["Result"]
    activate_fail_message["Please hold your call<br>is being transferred."]
    activate_fail_csr["CSR"]
    activate_fail_queue["QueueName =<br>Activate card CSR"]
    premenu_option["PreMenu<br>Option"]
    premenu_zero_message["Please hold your call<br>is being transferred."]
    premenu_zero_csr["CSR"]
    premenu_zero_queue["QueueName =<br>CSR/SMB"]
    credit_limit["Credit Limit<br>( Pre Menu )"]
    account_summary["Account Summary<br>Info"]
    start --> account_lookup
    account_lookup --> lookup_result
    lookup_result -->|"Fail"| lookup_fail_csr
    lookup_fail_csr --> lookup_fail_queue
    lookup_result -->|"Pass"| insert_ani
    insert_ani_inputs --> insert_ani
    insert_ani --> account_status
    account_status_inputs --> account_status
    account_status --> status_decision
    status_decision -->|"SF"| fraud_transfer_message
    fraud_transfer_message --> fraud_csr
    fraud_csr --> fraud_queue
    status_decision -->|"default / non-SF"| agency_code
    agency_code -->|"Yes"| agency_primary_user
    agency_code -->|"No"| past_due
    agency_primary_user -->|"No"| agency_not_primary_message
    agency_not_primary_message --> end_call
    agency_primary_user -->|"Yes"| agency_route_selector
    agency_route_selector -->|"AIC005 / AIC015"| aic_transfer
    agency_route_selector -->|"CBVDS1"| cbvds1_transfer
    agency_route_selector -->|"CBVDS2"| cbvds2_transfer
    agency_route_selector -->|"MCA001 / MCA002"| mca_transfer
    agency_route_selector -->|"LGL001 / LGL002"| lgl_transfer
    agency_route_selector -->|"TSI001 / TSI002 / TSI003"| tsi_transfer
    aic_transfer --> aic_queue
    cbvds1_transfer --> cbvds1_queue
    cbvds2_transfer --> cbvds2_queue
    mca_transfer --> mca_queue
    lgl_transfer --> lgl_queue
    tsi_transfer --> tsi_queue
    past_due -->|"No"| activate_card
    past_due -->|"Yes"| past_due_primary_user
    past_due_primary_user -->|"No"| agency_not_primary_message
    past_due_primary_user -->|"Yes"| past_due_message
    past_due_message --> payment_input
    payment_input -->|"Press 1"| payment_transfer
    payment_transfer --> payment_queue
    payment_input -->|"press 2"| activate_card
    activate_card_inputs --> activate_card
    activate_card --> activate_result
    activate_result -->|"Fail"| activate_fail_message
    activate_fail_message --> activate_fail_csr
    activate_fail_csr --> activate_fail_queue
    activate_result -->|"Success"| premenu_option
    premenu_option -->|"0"| premenu_zero_message
    premenu_zero_message --> premenu_zero_csr
    premenu_zero_csr --> premenu_zero_queue
    premenu_option -->|"1"| credit_limit
    credit_limit --> account_summary

