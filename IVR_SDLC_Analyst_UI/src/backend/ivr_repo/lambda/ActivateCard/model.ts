export interface EventType {
    Details: {
        ContactData: { 
            CustomerEndpoint: { 
                Address: string; 
                Type: string; 
            } 
        },
        Parameters: { 
            accountId: string; 
            customerId: string; 
            action: string;
        }
    }
}

export interface FinalResponse { 
    statusCode?: string;
    status?: string; 
    message?: string; 
    confirmationNumber?: string
    referenceNumber?: string 
}