"use client";

import React, { useState } from "react";
import { apiFetch } from "@/lib/api";

// চেকআউট মোডাল — ঠিকানা, পেমেন্ট পদ্ধতি, COD OTP ভেরিফিকেশন
interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: (orderId: string) => void;
}

export function CheckoutModal({ open, onClose, onSuccess }: Props) {
  // ঠিকানা ফর্ম
  const [address, setAddress] = useState({
    name: "",
    phone: "",
    division: "",
    district: "",
    details: "",
  });
  // পেমেন্ট পদ্ধতি — cod, bkash, ssl
  const [paymentMethod, setPaymentMethod] = useState("cod");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OTP স্টেজ — COD হলে অর্ডারের পর OTP দিতে হবে
  const [otpStage, setOtpStage] = useState(false);
  const [orderId, setOrderId] = useState("");
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpAttempts, setOtpAttempts] = useState(0);

  if (!open) return null;

  // অর্ডার তৈরি করা
  const handleCheckout = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { address, payment_method: paymentMethod };
      const resp = await apiFetch<{ order_id: string; status: string }>(
        "/orders/checkout",
        { method: "POST", body: JSON.stringify(payload) }
      );
      setOrderId(resp.order_id);
      if (paymentMethod === "cod") {
        // COD হলে OTP ভেরিফিকেশন দরকার
        setOtpStage(true);
      } else {
        onSuccess(resp.order_id);
        onClose();
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // OTP যাচাই করা (সর্বোচ্চ ৩ বার)
  const handleVerifyOtp = async () => {
    if (!orderId) return;
    setLoading(true);
    setOtpError(null);
    try {
      await apiFetch(`/orders/${orderId}/verify-cod`, {
        method: "POST",
        body: JSON.stringify({ otp }),
      });
      onSuccess(orderId);
      setOtpStage(false);
      onClose();
    } catch (e: any) {
      const attempts = otpAttempts + 1;
      setOtpAttempts(attempts);
      setOtpError(e.message);
      if (attempts >= 3) {
        setError("সর্বোচ্চ ৩ বার চেষ্টা করা হয়েছে। আবার চেকআউট করুন।");
        setOtpStage(false);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* ব্যাকড্রপ */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* মোডাল বডি */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-lg border border-border bg-card shadow-xl">
          {/* হেডার */}
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <h2 className="text-lg font-semibold text-foreground">
              {otpStage ? "OTP যাচাই" : "চেকআউট (Checkout)"}
            </h2>
            <button
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground hover:bg-accent"
            >
              ✕
            </button>
          </div>

          {/* বডি */}
          <div className="px-6 py-4 space-y-4">
            {error && (
              <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {!otpStage ? (
              <>
                {/* ঠিকানা ফর্ম */}
                <input
                  placeholder="নাম (Name)"
                  value={address.name}
                  onChange={(e) => setAddress({ ...address, name: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <input
                  placeholder="ফোন (Phone)"
                  value={address.phone}
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <input
                  placeholder="বিভাগ (Division)"
                  value={address.division}
                  onChange={(e) => setAddress({ ...address, division: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <input
                  placeholder="জেলা (District)"
                  value={address.district}
                  onChange={(e) => setAddress({ ...address, district: e.target.value })}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <textarea
                  placeholder="বিস্তারিত ঠিকানা"
                  value={address.details}
                  onChange={(e) => setAddress({ ...address, details: e.target.value })}
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                />

                {/* পেমেন্ট পদ্ধতি */}
                <div>
                  <p className="text-sm font-medium text-foreground mb-2">
                    পেমেন্ট পদ্ধতি
                  </p>
                  <div className="space-y-2">
                    {[
                      { value: "cod", label: "Cash on Delivery (COD)" },
                      { value: "bkash", label: "bKash" },
                      { value: "ssl", label: "SSLCommerz" },
                    ].map((opt) => (
                      <label
                        key={opt.value}
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <input
                          type="radio"
                          name="payment"
                          value={opt.value}
                          checked={paymentMethod === opt.value}
                          onChange={() => setPaymentMethod(opt.value)}
                          className="accent-primary"
                        />
                        <span className="text-sm text-foreground">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleCheckout}
                  disabled={loading || !address.name || !address.phone || !address.district}
                  className="w-full rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? "প্রক্রিয়াকরণ হচ্ছে..." : "অর্ডার কনফার্ম করুন"}
                </button>
              </>
            ) : (
              <>
                {/* OTP ভেরিফিকেশন */}
                <p className="text-sm text-muted-foreground">
                  আপনার ফোনে পাঠানো ৪ অংকের OTP কোড লিখুন
                </p>
                <input
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 4))}
                  maxLength={4}
                  placeholder="● ● ● ●"
                  className="w-full rounded-md border border-input bg-background px-3 py-3 text-center text-2xl tracking-[0.5em] font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
                {otpError && (
                  <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                    {otpError} (চেষ্টা {otpAttempts}/3)
                  </div>
                )}
                <button
                  onClick={handleVerifyOtp}
                  disabled={loading || otp.length < 4}
                  className="w-full rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? "যাচাই হচ্ছে..." : "OTP যাচাই করুন"}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
