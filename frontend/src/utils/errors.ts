/**
 * Unified error handling utilities.
 * Provides consistent error messages and handling across the frontend.
 */

import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  field?: string;
  code?: string;
}

export interface ValidationError {
  [field: string]: string[];
}

/**
 * Extract user-friendly error message from API error response.
 */
export function getErrorMessage(error: unknown): string {
  if (!error) {
    return 'An unexpected error occurred';
  }

  // Handle Axios errors
  if (isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string;
      message?: string;
      error?: string;
      non_field_errors?: string[];
    }>;

    // Network errors
    if (!axiosError.response) {
      return 'Network error. Please check your connection.';
    }

    const { status, data } = axiosError.response;

    // Handle specific HTTP status codes
    if (status === 401) {
      return 'Authentication required. Please log in.';
    }
    if (status === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (status === 404) {
      return 'The requested resource was not found.';
    }
    if (status === 500) {
      return 'Server error. Please try again later.';
    }

    // Extract error message from response
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;
    if (data?.error) return data.error;
    if (data?.non_field_errors?.[0]) return data.non_field_errors[0];

    return `Request failed with status ${status}`;
  }

  // Handle Error objects
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  return 'An unexpected error occurred';
}

/**
 * Extract field validation errors from API error response.
 */
export function getValidationErrors(error: unknown): ValidationError {
  if (!isAxiosError(error)) {
    return {};
  }

  const axiosError = error as AxiosError<Record<string, string | string[]>>;
  const data = axiosError.response?.data;

  if (!data || typeof data !== 'object') {
    return {};
  }

  const validationErrors: ValidationError = {};

  for (const [field, messages] of Object.entries(data)) {
    // Skip non-validation error fields
    if (['detail', 'message', 'error'].includes(field)) {
      continue;
    }

    // Normalize messages to array format
    if (Array.isArray(messages)) {
      validationErrors[field] = messages;
    } else if (typeof messages === 'string') {
      validationErrors[field] = [messages];
    }
  }

  return validationErrors;
}

/**
 * Type guard to check if error is an AxiosError.
 */
function isAxiosError(error: unknown): error is AxiosError {
  return (error as AxiosError).isAxiosError === true;
}
