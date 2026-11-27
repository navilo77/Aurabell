"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetchOptional } from "@/lib/api";
import { Header } from "@/components/header";
import { MobileBottomBar } from "@/components/mobile-bottom-bar";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  RotateCcw,
  ExternalLink,
  Home,
  Package,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getPaymentOptional, verifyPayment, isPaymentPaid, isPaymentFailed, getPaymentStatusDisplay } from "@/lib/payment-api";
import type { PaymentRead } from "@/lib/types";

export default function PaymentProcessingPage() {
  const params = useParams();
  const router = useRouter();
  const paymentId = params.paymentId as string;

  const [payment, setPayment] = useState<PaymentRead | null>(null);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [polling, setPolling] = useState(false);
  const [openedPaymentTab, setOpenedPaymentTab] = useState(false);

  const loadPayment = useCallback(async () => {
    if (!paymentId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getPaymentOptional(paymentId);
      if (data) {
        setPayment(data);
      } else {
        setError("Payment not found");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load payment");
    } finally {
      setLoading(false);
    }
  }, [paymentId]);

  const handleVerify = async () => {
    if (!paymentId) return;
    setVerifying(true);
    try {
      const result = await verifyPayment(paymentId);
      setPayment((prev) => prev ? { ...prev, status: result.status, paid_at: result.status === "paid" ? new Date().toISOString() : prev.paid_at } : null);
      if (result.status === "paid") {
        router.push(`/account/orders/${result.order_id}`);
      }
    } catch (err: any) {
      setError(err.message || "Verification failed");
    } finally {
      setVerifying(false);
    }
  };

  const openPaymentTab = useCallback(() => {
    if (paymentUrl && !openedPaymentTab) {
      window.open(paymentUrl, "_blank", "noopener,noreferrer");
      setOpenedPaymentTab(true);
    }
  }, [paymentUrl, openedPaymentTab]);

  // Poll for payment status (UI update only - NO auto-redirect)
  // Redirect ONLY happens after successful verifyPayment call
  useEffect(() => {
    if (!paymentId || isPaymentPaid(payment?.status || "") || isPaymentFailed(payment?.status || "")) {
      return;
    }

    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const data = await getPaymentOptional(paymentId);
        if (data) {
          setPayment(data);
          // NOTE: We do NOT auto-redirect here.
          // Redirect ONLY happens after successful verifyPayment (handleVerify)
          // This prevents payment spoofing via local DB manipulation.
        }
      } catch {
        // Ignore polling errors
      }
    }, 3000);

    return () => {
      clearInterval(interval);
      setPolling(false);
    };
  }, [paymentId, payment?.status]);

  useEffect(() => {
    loadPayment();
    // Get payment URL from sessionStorage
    const storedUrl = sessionStorage.getItem(`amarpay_url_${paymentId}`);
    if (storedUrl) {
      setPaymentUrl(storedUrl);
      sessionStorage.removeItem(`amarpay_url_${paymentId}`);
    }
  }, [loadPayment, paymentId]);

  // Auto-open payment tab on load
  useEffect(() => {
    if (paymentUrl && !openedPaymentTab) {
      openPaymentTab();
    }
  }, [paymentUrl, openedPaymentTab, openPaymentTab]);

  const paymentStatus = payment?.status || "pending";
  const statusInfo = getPaymentStatusDisplay(paymentStatus);
  const isPaid = isPaymentPaid(paymentStatus);
  const isFailed = isPaymentFailed(paymentStatus);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090b0e] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-gold-400" />
          <p className="mt-4 text-zinc-400">Loading payment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090b0e] pb-20 md:pb-0">
      <Header activeTab="home" />

      <main className="max-w-2xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className={cn(
            "mx-auto mb-4 w-16 h-16 rounded-2xl flex items-center justify-center",
            isPaid && "bg-success/20 border border-success/40 text-success",
            isFailed && "bg-rose-500/20 border border-rose-500/40 text-rose-400",
            !isPaid && !isFailed && "bg-gold-500/20 border border-gold-400/40 text-gold-400"
          )}>
            {isPaid && <CheckCircle2 className="w-8 h-8" />}
            {isFailed && <XCircle className="w-8 h-8" />}
            {!isPaid && !isFailed && <Loader2 className="w-8 h-8 animate-spin" />}
          </div>

          <h1 className="font-serif text-2xl font-bold text-white mb-2">
            {isPaid ? "Payment Successful" : isFailed ? "Payment Failed" : "Payment Processing"}
          </h1>
          <p className="text-zinc-400">
            {isPaid
              ? "Your order has been confirmed and is being prepared."
              : isFailed
              ? "Your payment could not be processed. Please try again or choose another method."
              : "Complete your payment on AmarPay. Click 'Check Payment Status' after payment to verify."}
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-300">
            {error}
          </div>
        )}

        {payment && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Payment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Payment ID</p>
                  <p className="text-sm font-mono text-zinc-300 truncate">{payment.id.slice(0, 12)}...</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Order ID</p>
                  <p className="text-sm font-mono text-zinc-300 truncate">{payment.order_id.slice(0, 12)}...</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Amount</p>
                  <p className="text-sm font-bold text-white">৳{payment.amount.toFixed(2)} {payment.currency_code}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Status</p>
                  <span className={cn(
                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                    statusInfo.variant === "success" && "bg-success/20 text-success border border-success/30",
                    statusInfo.variant === "warning" && "bg-warning/20 text-warning border border-warning/30",
                    statusInfo.variant === "destructive" && "bg-rose-500/20 text-rose-400 border border-rose-500/30",
                    statusInfo.variant === "info" && "bg-blue-500/20 text-blue-400 border border-blue-500/30",
                    "bg-muted/50 text-muted-foreground border border-white/10"
                  )}>
                    {statusInfo.label}
                    {polling && <Loader2 className="ml-1.5 h-3 w-3 animate-spin" />}
                  </span>
                </div>
              </div>

              {payment.provider_reference && (
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Transaction ID</p>
                  <p className="text-sm font-mono text-zinc-300">{payment.provider_reference}</p>
                </div>
              )}

              {payment.paid_at && (
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wider">Paid At</p>
                  <p className="text-sm text-zinc-300">{new Date(payment.paid_at).toLocaleString("bn-BD")}</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="space-y-3">
          {isPaid && (
            <div className="space-y-3">
              <Button
                asChild
                className="w-full"
                size="lg"
              >
                <a href={`/account/orders/${payment?.order_id}`}>
                  <Package className="mr-2 h-4 w-4" />
                  View Order Details
                </a>
              </Button>
              <Button
                variant="outline"
                asChild
                className="w-full"
                size="lg"
              >
                <a href="/account/orders">
                  <Home className="mr-2 h-4 w-4" />
                  Back to Orders
                </a>
              </Button>
            </div>
          )}

          {isFailed && (
            <div className="space-y-3">
              <Button
                onClick={handleVerify}
                disabled={verifying}
                className="w-full"
                size="lg"
              >
                {verifying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying Payment...
                  </>
                ) : (
                  <>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Retry Verification
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                asChild
                className="w-full"
                size="lg"
              >
                <a href="/shop/cart">
                  <Home className="mr-2 h-4 w-4" />
                  Return to Cart
                </a>
              </Button>
            </div>
          )}

          {!isPaid && !isFailed && (
            <div className="space-y-3">
              <Button
                onClick={openPaymentTab}
                disabled={!paymentUrl}
                className="w-full"
                size="lg"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                {openedPaymentTab ? "Payment Opened in New Tab" : "Open AmarPay Payment"}
              </Button>
              <Button
                onClick={handleVerify}
                disabled={verifying}
                variant="outline"
                className="w-full"
                size="lg"
              >
                {verifying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Check Payment Status
                  </>
                )}
              </Button>
              <p className="text-center text-xs text-zinc-500">
                Complete payment on AmarPay, then click &ldquo;Check Payment Status&rdquo; to verify.
              </p>
            </div>
          )}

          {!payment && (
            <Button
              variant="outline"
              asChild
              className="w-full"
              size="lg"
            >
              <a href="/shop/cart">
                <Home className="mr-2 h-4 w-4" />
                Return to Cart
              </a>
            </Button>
          )}
        </div>
      </main>

      <MobileBottomBar />
    </div>
  );
}