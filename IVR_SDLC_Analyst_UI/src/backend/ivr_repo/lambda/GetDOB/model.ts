export interface Event {
    Details: {
        Parameters: {
            accountId: string
            customerType: string
            customerId:string
        }
    }
}

export interface FinalResponse {
    statusCode: number;
    message?: string;
    dateOfBirth?: string;
    accountId?: string;
    customerType?: string;
}

export interface ApiResponse {
    statusCode: number
    accountInformation: AccountInformation
}

export interface AccountInformation {
    customerList: CustomerList[]
}

export interface CustomerList {
    dateOfBirth: string
    accountId: string
    customerType: string
    customerId:string
}