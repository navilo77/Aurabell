import React, { useState } from "react";
import { Modal, Button, Input, RadioGroup, Radio } from "@/ui/design-system"; // adjust imports
import { CheckoutPreview, checkoutOrder, verifyCodOtp } from "../utils/api";

interface Props {
  open: boolean;
  onClose: () => void;
  preview: CheckoutPreview | null;
  onSuccess: (orderId: string) => void;
  userId: string;
  sessionId: string;
}
  open: boolean;
  onClose: () => void;
  preview: CheckoutPreview | null;
  onSuccess: (orderId: string) => void;
}

export const CheckoutModal: React.FC<Props> = ({ open, onClose, preview, onSuccess, userId, sessionId }) => {
  const [address, setAddress] = useState({ name: "", phone: "", division: "", district: "", details: "" });
  const [paymentMethod, setPaymentMethod] = useState("cod");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [otpStage, setOtpStage] = useState(false);
  const [orderId, setOrderId] = useState<string>("");
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpAttempts, setOtpAttempts] = useState(0);

  const handleCheckout = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        user_id: "", // will be filled in page component
        session_id: "",
        address,
        payment_method: paymentMethod,
        // you may also send cart preview data if needed
      };
      const resp = await checkoutOrder(payload);
      if (resp.error) throw new Error(resp.error);
      setOrderId(resp.data.order_id);
      if (paymentMethod === "cod") {
        setOtpStage(true);
      } else {
        onSuccess(resp.data.order_id);
        onClose();
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!orderId) return;
    setLoading(true);
    setOtpError(null);
    try {
      const resp = await verifyCodOtp(orderId, otp);
      if (resp.error) throw new Error(resp.error);
      onSuccess(orderId);
      setOtpStage(false);
      onClose();
    } catch (e: any) {
      const attempts = otpAttempts + 1;
      setOtpAttempts(attempts);
      setOtpError(e.message);
      if (attempts >= 3) {
        setError("Maximum OTP attempts reached. Please restart checkout.");
        setOtpStage(false);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Checkout (চেকআউট)">
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {!otpStage ? (
        <div className="space-y-4">
          <Input placeholder="নাম" value={address.name} onChange={e => setAddress({ ...address, name: e.target.value })} />
          <Input placeholder="ফোন" value={address.phone} onChange={e => setAddress({ ...address, phone: e.target.value })} />
          <Input placeholder="Division" value={address.division} onChange={e => setAddress({ ...address, division: e.target.value })} />
          <Input placeholder="District" value={address.district} onChange={e => setAddress({ ...address, district: e.target.value })} />
          <Input placeholder="অতিরিক্ত ঠিকানা" value={address.details} onChange={e => setAddress({ ...address, details: e.target.value })} />
          <RadioGroup label="পেমেন্ট পদ্ধতি" value={paymentMethod} onChange={v => setPaymentMethod(v as string)}>
            <Radio value="cod">Cash on Delivery (COD)</Radio>
            <Radio value="bkash">bKash</Radio>
            <Radio value="ssl">SSLCommerz</Radio>
          </RadioGroup>
          <Button onClick={handleCheckout} loading={loading} className="w-full">Confirm Order</Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>Enter OTP (৪ অংকের কোড)</div>
          <Input value={otp} onChange={e => setOtp(e.target.value)} maxLength={4} />
          {otpError && <div className="text-red-600">{otpError}</div>}
          <Button onClick={handleVerifyOtp} loading={loading} className="w-full">Verify OTP</Button>
        </div>
      )}
    </Modal>
  );
};
