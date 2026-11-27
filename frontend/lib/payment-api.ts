import { apiFetch, apiFetchOptional } from "@/lib/api";
import type {
  PaymentInitiateRequest,
  PaymentInitiateResponse,
  PaymentRead,
  PaymentVerifyResponse,
  PaymentStatus,
} from "@/lib/types";

export async function initiatePayment(data: PaymentInitiateRequest): Promise<PaymentInitiateResponse> {
  return apiFetch<PaymentInitiateResponse>("/payments/initiate", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getPayment(paymentId: string): Promise<PaymentRead> {
  return apiFetch<PaymentRead>(`/payments/${paymentId}`);
}

export async function verifyPayment(paymentId: string): Promise<PaymentVerifyResponse> {
  return apiFetch<PaymentVerifyResponse>(`/payments/${paymentId}/verify`, {
    method: "POST",
  });
}

export async function getPaymentOptional(paymentId: string): Promise<PaymentRead | null> {
  return apiFetchOptional<PaymentRead>(`/payments/${paymentId}`);
}

export function isPaymentPaid(status: string): boolean {
  return status === "paid";
}

export function isPaymentPending(status: string): boolean {
  return status === "pending" || status === "authorized";
}

export function isPaymentFailed(status: string): boolean {
  return status === "failed";
}

export function isPaymentRefunded(status: string): boolean {
  return status === "partially_refunded" || status === "refunded";
}

export function getPaymentStatusDisplay(status: string): { label: string; variant: "default" | "success" | "warning" | "destructive" | "info" } {
  switch (status) {
    case "paid":
      return { label: "Paid", variant: "success" };
    case "pending":
      return { label: "Pending", variant: "warning" };
    case "authorized":
      return { label: "Authorized", variant: "info" };
    case "failed":
      return { label: "Failed", variant: "destructive" };
    case "partially_refunded":
      return { label: "Partially Refunded", variant: "warning" };
    case "refunded":
      return { label: "Refunded", variant: "destructive" };
    default:
      return { label: status, variant: "default" };
  }
}