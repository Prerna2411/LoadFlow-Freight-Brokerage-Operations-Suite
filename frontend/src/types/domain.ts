export type AccountType = 'broker' | 'carrier' | 'shipper';

export type User = {
  id: number;
  email: string;
  name: string;
  account_type: AccountType;
  organization_id: number | null;
  organization_name: string | null;
  role: string | null;
  is_admin: boolean;
  permissions: string[];
};

export type LoadStatus =
  | 'Posted'
  | 'Carrier Assigned'
  | 'Rate Confirmed'
  | 'Dispatched'
  | 'In Transit'
  | 'Delivered'
  | 'POD Verified'
  | 'Invoiced/Closed';
