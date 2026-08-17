
export interface EventType {
    Details: {
        Parameters: {
            accountId: string;
            customerId: string;
        };
    };
}

export interface FinalResponse {
    statusCode: number;
    message?: string;
    accountStatus?: string;
    agencyCode?: string;
    codeFlag?: boolean;
    creditAllowed?: boolean;
    clientProductCode?: string;
    openedDate?: string;
}


export interface ApiResponse {
    statusCode: string
    accountInformation: AccountInformation
}

export interface AccountInformation {
    meta: Meta
    collAgencyCode: string
    product: Product
}

//Change for CCR-827
export interface Product {
    productCode: string
    providerId: string
    clientProductCode: string
}

export interface Meta {
    status: Status[]
}

export interface Status {
    description: string
    reason: string
    code: string
}
