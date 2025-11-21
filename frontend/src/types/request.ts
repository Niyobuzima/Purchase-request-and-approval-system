/**
 * Purchase request types and interfaces.
 * Defines request status, items, and data structures.
 */

import { User } from './user';

export type RequestStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED';

export interface RequestItem {
  id?: string;
  name: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface VendorInfo {
  name: string;
  contact?: string;
  email?: string;
  address?: string;
}

export interface ProformaData {
  vendor: VendorInfo;
  invoice_number?: string;
  date?: string;
  items: RequestItem[];
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
  payment_terms?: string;
}

export interface PurchaseRequest {
  id: string;
  title: string;
  description?: string;
  status: RequestStatus;
  created_by: User;
  created_at: string;
  updated_at: string;
  proforma_file?: string;
  proforma_extracted_data?: ProformaData;
  purchase_order_file?: string;
  purchase_order_data?: any;
  receipt_file?: string;
  receipt_validation?: any;
}

export interface CreateRequestData {
  title: string;
  description?: string;
  items?: RequestItem[];
}

export interface UpdateRequestData {
  title?: string;
  description?: string;
  items?: RequestItem[];
}
