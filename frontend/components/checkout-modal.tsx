"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  X,
  ShieldCheck,
  Truck,
  CreditCard,
  Phone,
  User,
  MapPin,
  Building,
  KeyRound,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Plus,
  Check,
  Edit2,
  Trash2,
  Home,
  ExternalLink,
  Lock,
  AlertCircle,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { initiatePayment } from "@/lib/payment-api";

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: (orderId: string) => void;
}

// Backend AddressRead schema
interface SavedAddress {
  id: string;
  user_id: string;
  recipient_name: string;
  phone: string;
  division: string;
  district: string;
  upazila: string | null;
  area: string | null;
  address_line: string;
  postal_code: string | null;
  is_default: boolean;
  created_at: string;
}

// Inline address schema (matching backend OrderAddressCreate)
interface InlineAddress {
  recipient_name: string;
  phone: string;
  division: string;
  district: string;
  upazila?: string;
  area?: string;
  address_line: string;
  postal_code?: string;
  address_type?: "delivery" | "billing" | "both";
}

type AddressMode = "saved" | "new";

export function CheckoutModal({ open, onClose, onSuccess }: Props) {
  const [savedAddresses, setSavedAddresses] = useState<SavedAddress[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [addressMode, setAddressMode] = useState<AddressMode>("new");
  const [inlineAddress, setInlineAddress] = useState<InlineAddress>({
    recipient_name: "",
    phone: "",
    division: "",
    district: "",
    address_line: "",
  });

  const [paymentMethod, setPaymentMethod] = useState("cod");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // OTP Stage for Cash on Delivery
  const [otpStage, setOtpStage] = useState(false);
  const [orderId, setOrderId] = useState("");
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpAttempts, setOtpAttempts] = useState(0);

  const loadSavedAddresses = useCallback(async () => {
    try {
      const data = await apiFetch<SavedAddress[]>("/users/me/addresses");
      setSavedAddresses(data ?? []);
      // Auto-select default address if available
      const defaultAddr = data?.find((a) => a.is_default);
      if (defaultAddr && !selectedAddressId) {
        setSelectedAddressId(defaultAddr.id);
        setAddressMode("saved");
      } else if (data && data.length > 0 && !selectedAddressId) {
        setSelectedAddressId(data[0].id);
        setAddressMode("saved");
      }
    } catch {
      // Ignore error - user might not be logged in or no addresses
    }
  }, [selectedAddressId]);

  // Load saved addresses on open
  useEffect(() => {
    if (open) {
      loadSavedAddresses();
    }
  }, [open, loadSavedAddresses]);

  if (!open) return null;

  const handleCheckout = async () => {
    setLoading(true);
    setError(null);
    try {
      let payload: Record<string, unknown> = {
        payment_method: paymentMethod,
      };

      if (addressMode === "saved" && selectedAddressId) {
        payload.delivery_address_id = selectedAddressId;
      } else if (addressMode === "new") {
        // Validate required fields for inline address
        if (!inlineAddress.recipient_name || !inlineAddress.phone || !inlineAddress.district || !inlineAddress.address_line) {
          setError("Please fill in all required address fields.");
          setLoading(false);
          return;
        }
        payload.address = inlineAddress;
      }

      const resp = await apiFetch<{ order_id: string; status: string }>(
        "/orders/checkout",
        { method: "POST", body: JSON.stringify(payload) }
      );
      setOrderId(resp.order_id);

      if (paymentMethod === "cod") {
        setOtpStage(true);
      } else if (paymentMethod === "amarpay") {
        // Initiate AmarPay payment and redirect to processing page
        try {
          const paymentResult = await initiatePayment({ order_id: resp.order_id });
          // Store payment URL in sessionStorage for the processing page
          sessionStorage.setItem(`amarpay_url_${paymentResult.payment_id}`, paymentResult.payment_url);
          // Close modal and redirect to payment processing page
          onClose();
          window.location.href = `/payment/processing/${paymentResult.payment_id}`;
        } catch (paymentErr: any) {
          setError(paymentErr.message || "Failed to initiate online payment. Please try again.");
        }
      } else {
        onSuccess(resp.order_id);
        onClose();
      }
    } catch (e: any) {
      setError(e.message || "Failed to process order. Please try again.");
    } finally {
      setLoading(false);
    }
  };

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
      setOtpError(e.message || "Invalid OTP code.");
      if (attempts >= 3) {
        setError("Maximum 3 verification attempts reached. Please re-initiate checkout.");
        setOtpStage(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedAddress = savedAddresses.find((a) => a.id === selectedAddressId);

  const formatAddress = (addr: SavedAddress) => {
    const parts = [addr.address_line];
    if (addr.area) parts.push(addr.area);
    if (addr.upazila) parts.push(addr.upazila);
    parts.push(addr.district, addr.division);
    if (addr.postal_code) parts.push(addr.postal_code);
    return parts.join(", ");
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-md animate-in fade-in duration-300"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-lg rounded-3xl border border-gold-500/35 bg-[#0d1017] shadow-[0_0_50px_rgba(0,0,0,0.9)] overflow-hidden z-10 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-5 bg-gradient-to-r from-[#141822] to-[#0d1017]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gold-500/20 border border-gold-400/40 flex items-center justify-center text-gold-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif text-lg font-bold text-white">
                {otpStage ? "Verify Cash on Delivery" : "Secure Checkout"}
              </h2>
              <p className="text-[11px] text-zinc-400">
                {otpStage ? "Enter SMS verification code" : "Official Flagship Delivery Details"}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300 leading-relaxed">
              {error}
            </div>
          )}

          {!otpStage ? (
            <>
              {/* Address Mode Selector */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gold-300">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Delivery Address</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setAddressMode("saved")}
                    disabled={savedAddresses.length === 0}
                    className={`flex flex-col p-3 rounded-xl border cursor-pointer transition-all text-left ${
                      addressMode === "saved"
                        ? "bg-gold-500/15 border-gold-400/80 text-white shadow-gold"
                        : savedAddresses.length === 0
                        ? "bg-[#141824]/50 border-white/5 text-zinc-600 cursor-not-allowed"
                        : "bg-[#141824] border-white/5 text-zinc-400 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold">Saved Address</span>
                      {savedAddresses.length > 0 && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-black/60 text-gold-300 font-mono">
                          {savedAddresses.length} saved
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-zinc-400">
                      {savedAddresses.length > 0 ? "Select from your saved addresses" : "No saved addresses"}
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setAddressMode("new")}
                    className={`flex flex-col p-3 rounded-xl border cursor-pointer transition-all text-left ${
                      addressMode === "new"
                        ? "bg-gold-500/15 border-gold-400/80 text-white shadow-gold"
                        : "bg-[#141824] border-white/5 text-zinc-400 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold">New Address</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-black/60 text-gold-300 font-mono">
                        Enter manually
                      </span>
                    </div>
                    <span className="text-xs text-zinc-400">Enter a new delivery address</span>
                  </button>
                </div>

                {/* Saved Address Selection */}
                {addressMode === "saved" && savedAddresses.length > 0 && (
                  <div className="space-y-2">
                    {savedAddresses.map((addr) => (
                      <label
                        key={addr.id}
                        className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                          selectedAddressId === addr.id
                            ? "bg-gold-500/10 border-gold-400/60"
                            : "bg-[#141824] border-white/5 hover:border-gold-400/30"
                        }`}
                      >
                        <input
                          type="radio"
                          name="saved-address"
                          checked={selectedAddressId === addr.id}
                          onChange={() => setSelectedAddressId(addr.id)}
                          className="accent-gold-400"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm text-white">{addr.recipient_name}</span>
                            {addr.is_default && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-gold-500/20 text-gold-300 font-mono">
                                Default
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-zinc-400 truncate">{formatAddress(addr)}</p>
                          <p className="text-[10px] text-zinc-500">{addr.phone}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}

                {/* Inline Address Form */}
                {addressMode === "new" && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="relative">
                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                          placeholder="Recipient Full Name *"
                          value={inlineAddress.recipient_name}
                          onChange={(e) => setInlineAddress({ ...inlineAddress, recipient_name: e.target.value })}
                          className="w-full h-11 pl-10 pr-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                        />
                      </div>

                      <div className="relative">
                        <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                          placeholder="Phone (01XXXXXXXXX) *"
                          value={inlineAddress.phone}
                          onChange={(e) => setInlineAddress({ ...inlineAddress, phone: e.target.value })}
                          className="w-full h-11 pl-10 pr-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <input
                        placeholder="Division (e.g. Dhaka)"
                        value={inlineAddress.division}
                        onChange={(e) => setInlineAddress({ ...inlineAddress, division: e.target.value })}
                        className="w-full h-11 px-3.5 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                      />
                      <input
                        placeholder="District / City *"
                        value={inlineAddress.district}
                        onChange={(e) => setInlineAddress({ ...inlineAddress, district: e.target.value })}
                        className="w-full h-11 px-3.5 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <input
                        placeholder="Upazila / Thana"
                        value={inlineAddress.upazila || ""}
                        onChange={(e) => setInlineAddress({ ...inlineAddress, upazila: e.target.value })}
                        className="w-full h-11 px-3.5 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                      />
                      <input
                        placeholder="Area / Road"
                        value={inlineAddress.area || ""}
                        onChange={(e) => setInlineAddress({ ...inlineAddress, area: e.target.value })}
                        className="w-full h-11 px-3.5 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                      />
                    </div>

                    <textarea
                      placeholder="Street Address, House/Apartment No, Area Details *"
                      value={inlineAddress.address_line}
                      onChange={(e) => setInlineAddress({ ...inlineAddress, address_line: e.target.value })}
                      rows={2}
                      className="w-full p-3 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400 resize-none"
                    />

                    <input
                      placeholder="Postal Code"
                      value={inlineAddress.postal_code || ""}
                      onChange={(e) => setInlineAddress({ ...inlineAddress, postal_code: e.target.value })}
                      className="w-full h-11 px-3.5 rounded-xl bg-[#141824] border border-white/10 text-xs text-white placeholder:text-zinc-500 focus:outline-none focus:border-gold-400"
                    />
                  </div>
                )}
              </div>

              {/* Payment Methods */}
              <div className="pt-2">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gold-300 mb-2.5">
                  <CreditCard className="w-3.5 h-3.5" />
                  <span>Payment Method</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {[
                    { value: "cod", label: "Cash on Delivery", badge: "Safe OTP", icon: Truck },
                    { value: "amarpay", label: "AmarPay Online", badge: "Cards/NetBanking", icon: CreditCard },
                  ].map((opt) => (
                    <label
                      key={opt.value}
                      className={`flex flex-col p-3 rounded-xl border cursor-pointer transition-all ${
                        paymentMethod === opt.value
                          ? "bg-gold-500/15 border-gold-400/80 text-white shadow-gold"
                          : "bg-[#141824] border-white/5 text-zinc-400 hover:text-white"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <input
                          type="radio"
                          name="payment"
                          value={opt.value}
                          checked={paymentMethod === opt.value}
                          onChange={() => setPaymentMethod(opt.value)}
                          className="accent-gold-400"
                        />
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-black/60 text-gold-300 font-mono">
                          {opt.badge}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <opt.icon className="w-4 h-4 text-gold-400" />
                        <span className="text-xs font-bold">{opt.label}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Confirm Button */}
              <button
                onClick={handleCheckout}
                disabled={loading || (addressMode === "saved" && !selectedAddressId) || (addressMode === "new" && (!inlineAddress.recipient_name || !inlineAddress.phone || !inlineAddress.district || !inlineAddress.address_line))}
                className="w-full mt-2 h-12 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing Order...</span>
                  </>
                ) : (
                  <>
                    <span>Confirm Order & Place Delivery</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </>
          ) : otpStage ? (
            <>
              {/* OTP Stage */}
              <div className="py-4 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-gold-500/20 border border-gold-400/40 flex items-center justify-center text-gold-400 mx-auto">
                  <KeyRound className="w-6 h-6" />
                </div>
                <h3 className="font-serif text-base font-bold text-white">
                  Enter 4-Digit OTP Code
                </h3>
                <p className="text-xs text-zinc-400 max-w-xs mx-auto">
                  A verification code has been dispatched to your phone number for Cash on Delivery confirmation.
                </p>

                <input
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 4))}
                  maxLength={4}
                  placeholder="● ● ● ●"
                  className="w-48 h-14 mx-auto rounded-2xl bg-[#141824] border border-gold-400/60 text-center text-2xl tracking-[0.5em] font-mono text-gold-200 focus:outline-none focus:ring-2 focus:ring-gold-400/50"
                />

                {otpError && (
                  <p className="text-xs text-rose-400 font-medium">
                    {otpError} (Attempt {otpAttempts}/3)
                  </p>
                )}

                <button
                  onClick={handleVerifyOtp}
                  disabled={loading || otp.length < 4}
                  className="w-full mt-4 h-12 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 disabled:opacity-40 transition-all flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Verifying Code...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Verify & Complete Order</span>
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Default Checkout Form */}
            </>
          )}
        </div>
      </div>
    </div>
  );
}