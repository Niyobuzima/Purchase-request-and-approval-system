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

export interface PurchaseOrderData {
  po_number: string;
  date: string;
  request_id: string;
  vendor: VendorInfo;
  buyer: {
    name: string;
    address: string;
    contact: string;
    email: string;
  };
  items: RequestItem[];
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
  payment_terms: string;
  delivery_terms: string;
  approved_by: {
    name: string;
    email: string;
    role: string;
    date: string;
  };
  notes?: string;
}

export interface Discrepancy {
  type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  field: string;
  expected?: number | string;
  actual?: number | string;
  difference?: number;
  tolerance?: number;
  item_name?: string;
  message: string;
}

export interface ReceiptValidation {
  is_valid: boolean;
  validation_date: string;
  po_number?: string;
  receipt_number?: string;
  discrepancies_count: number;
  discrepancies: Discrepancy[];
  receipt_data?: {
    vendor_name?: string;
    receipt_number?: string;
    date?: string;
    items: RequestItem[];
    subtotal: number;
    tax: number;
    total: number;
    currency: string;
  };
  summary: string;
  severity_breakdown?: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  type_breakdown?: Record<string, number>;
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
  purchase_order_data?: PurchaseOrderData;
  receipt_file?: string;
  receipt_validation?: ReceiptValidation;
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
