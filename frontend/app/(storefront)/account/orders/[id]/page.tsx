"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Package,
  ShoppingCart,
  Truck,
  Clock,
  MapPin,
  ChevronLeft,
  Loader2,
  XCircle,
  AlertCircle,
  CheckCircle,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { OrderRead, OrderItemRead, OrderTimelineEntry } from "@/lib/types";

function OrderStatusBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    pending: "bg-warning/10 text-warning border-warning/20",
    confirmed: "bg-primary/10 text-primary border-primary/20",
    processing: "bg-blue/10 text-blue border-blue/20",
    shipped: "bg-purple/10 text-purple border-purple/20",
    delivered: "bg-success/10 text-success border-success/20",
    cancelled: "bg-destructive/10 text-destructive border-destructive/20",
    refunded: "bg-muted/10 text-muted border-muted/20",
  };
  return (
    <Badge variant="outline" className={cn("text-xs", variants[status] || variants.pending)}>
      {status}
    </Badge>
  );
}

function TimelineIcon({ status }: { status: string }) {
  const icons: Record<string, React.ReactNode> = {
    pending: <Clock className="h-4 w-4 text-warning" />,
    confirmed: <CheckCircle className="h-4 w-4 text-primary" />,
    processing: <RotateCcw className="h-4 w-4 text-blue-400" />,
    shipped: <Truck className="h-4 w-4 text-purple-400" />,
    delivered: <Package className="h-4 w-4 text-success" />,
    cancelled: <XCircle className="h-4 w-4 text-destructive" />,
    refunded: <AlertCircle className="h-4 w-4 text-muted-foreground" />,
  };
  return icons[status] || <Clock className="h-4 w-4 text-muted-foreground" />;
}

const statusLabel: Record<string, string> = {
  pending: "পেন্ডিং",
  confirmed: "কনফার্মড",
  processing: "প্রসেসিং",
  shipped: "শিপ করা হয়েছে",
  delivered: "ডেলিভার্ড",
  cancelled: "বাতিল",
  refunded: "রিফান্ডেড",
};

const CANCELLABLE_STATUSES = ["pending", "confirmed"];

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams();
  const orderId = params.id as string;
  const [order, setOrder] = useState<OrderRead | null>(null);
  const [timeline, setTimeline] = useState<OrderTimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  const fetchOrder = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<OrderRead>(`/orders/${orderId}`);
      setOrder(data);
    } catch (err: any) {
      setError(err.message || "অর্ডার লোড করতে সমস্যা হচ্ছে");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  const fetchTimeline = useCallback(async () => {
    setTimelineLoading(true);
    try {
      const data = await apiFetch<OrderTimelineEntry[]>(`/orders/${orderId}/timeline`);
      setTimeline(data ?? []);
    } catch {
      // Timeline is optional, don't show error
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  }, [orderId]);

  const handleCancel = async () => {
    if (!CANCELLABLE_STATUSES.includes(order?.order_status || "")) return;
    setCancelling(true);
    setCancelError(null);
    try {
      const data = await apiFetch<OrderRead>(`/orders/${orderId}/cancel`, {
        method: "POST",
      });
      setOrder(data);
      setCancelError(null);
      // Refresh timeline after cancellation
      fetchTimeline();
    } catch (err: any) {
      setCancelError(err.message || "অর্ডার বাতিল করতে সমস্যা হচ্ছে");
    } finally {
      setCancelling(false);
    }
  };

  useEffect(() => {
    fetchOrder();
    fetchTimeline();
  }, [fetchOrder, fetchTimeline]);

  const toNum = (v: unknown): number => (typeof v === "number" ? v : Number(v)) || 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center text-center">
        <h2 className="text-2xl font-bold text-destructive">{error || "অর্ডার পাওয়া যায়নি"}</h2>
        <Button onClick={() => router.back()} className="mt-4">
          ফিরে যান
        </Button>
      </div>
    );
  }

  const subtotal = toNum(order.subtotal);
  const discount_total = toNum(order.discount_total);
  const delivery_total = toNum(order.delivery_total);
  const grand_total = toNum(order.grand_total);
  const canCancel = CANCELLABLE_STATUSES.includes(order.order_status);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <nav className="flex items-center gap-1 text-sm text-muted-foreground mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1 hover:text-primary transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            স্পর্শ করে ফিরে যান
          </button>
          <span>/</span>
          <span className="text-foreground">অর্ডার #{order.order_number.slice(-8)}</span>
        </nav>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <div>
              <CardTitle className="text-lg">অর্ডার #{order.order_number.slice(-8)}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {new Date(order.created_at).toLocaleDateString("bn-BD", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
            <OrderStatusBadge status={order.order_status} />
          </CardHeader>

          <CardContent className="pt-0">
{/* অর্ডার সারাংশ */}
            <div className="border-b border-border pb-6 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    সাবটোটাল
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    ৳{subtotal.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    ডিসকাউন্ট
                  </p>
                  <p className="text-sm font-medium text-green-600">
                    −৳{discount_total.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    ডেলিভারি ফি
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    ৳{delivery_total.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">
                    গ্রैंड টোটাল
                  </p>
                  <p className="text-lg font-bold text-primary">
                    ৳{grand_total.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            {/* ডেলিভারি ঠিকানা (স্ন্যাপশট) */}
            {order.delivery_address && (
              <div className="border-b border-border pb-6 mb-6">
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground" />
                  ডেলিভারি ঠিকানা
                </h3>
                <div className="bg-muted/30 rounded-lg p-4">
                  <p className="font-medium text-foreground">{order.delivery_address.recipient_name}</p>
                  <p className="text-sm text-muted-foreground">{order.delivery_address.phone}</p>
                  <p className="text-sm text-foreground mt-1">
                    {order.delivery_address.address_line}
                    {order.delivery_address.area && `, ${order.delivery_address.area}`}
                    {order.delivery_address.upazila && `, ${order.delivery_address.upazila}`}
                    {order.delivery_address.district && `, ${order.delivery_address.district}`}
                    {order.delivery_address.division && `, ${order.delivery_address.division}`}
                    {order.delivery_address.postal_code && ` - ${order.delivery_address.postal_code}`}
                  </p>
                </div>
              </div>
            )}

            {/* অর্ডার আইটেম */}
            <h3 className="text-sm font-semibold text-foreground mb-3">অর্ডার করা পণ্য</h3>
            <div className="space-y-3">
              {order.order_items.map((item) => (
                <div key={item.id} className="flex items-center gap-4 p-3 rounded-lg border border-border/50 bg-background/50">
                  <div className="w-16 h-16 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
                    <Package className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {item.product_name_snapshot}
                    </p>
                    <p className="text-xs text-muted-foreground">SKU: {item.sku_snapshot}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-foreground">
                      ৳{toNum(item.line_total).toFixed(2)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.quantity} × ৳{toNum(item.unit_price).toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* অর্ডার টাইমলাইন */}
            {(timeline.length > 0 || timelineLoading) && (
              <div className="mt-6 border-t border-border pt-6">
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  অর্ডার টাইমলাইন
                </h3>
                {timelineLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : timeline.length === 0 ? (
                  <p className="text-sm text-muted-foreground">টাইমলাইন ডেটা পাওয়া যায়নি</p>
                ) : (
                  <div className="space-y-4">
                    {timeline.map((entry, index) => (
                      <div
                        key={`${entry.created_at}-${index}`}
                        className="flex gap-3 items-start"
                      >
                        <div className="flex flex-col items-center">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <TimelineIcon status={entry.new_status} />
                          </div>
                          {index < timeline.length - 1 && (
                            <div className="w-0.5 h-full bg-border mt-1 flex-1" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0 pt-1">
                          <div className="flex items-center gap-2">
                            <OrderStatusBadge status={entry.new_status} />
                            <span className="text-xs text-muted-foreground">
                              {new Date(entry.created_at).toLocaleString("bn-BD", {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          {entry.note && (
                            <p className="text-xs text-muted-foreground mt-1">{entry.note}</p>
                          )}
                          {entry.changed_by && (
                            <p className="text-[10px] text-muted-foreground mt-0.5">
                              দ্বারা: {entry.changed_by}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ক্যান্সেল বাটন */}
            {canCancel && (
              <div className="mt-6 pt-6 border-t border-border">
                <div className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-destructive">এই অর্ডার বাতিল করা যাবে</p>
                    <p className="text-xs text-muted-foreground">
                      বাতিল করার পর এটি জমা দিতে পারবেন না।
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleCancel}
                    disabled={cancelling}
                    className="flex-shrink-0"
                  >
                    {cancelling ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-1" />
                        বাতিল হচ্ছে...
                      </>
                    ) : (
                      "বাতিল করুন"
                    )}
                  </Button>
                </div>
                {cancelError && (
                  <p className="text-sm text-destructive mt-2">{cancelError}</p>
                )}
              </div>
            )}
          </CardContent>

          <CardFooter className="pt-0">
            <div className="flex items-center gap-3">
              <Truck className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">অর্ডার কনফার্মের পর শিপ করা হবে</span>
            </div>
          </CardFooter>
        </Card>

        <div className="mt-8 flex gap-3">
          <Button variant="outline" onClick={() => router.back()} className="flex-1">
            অর্ডার তালিকায় ফিরে যান
          </Button>
          <Button asChild className="flex-1">
            <a href="/shop">নতুন অর্ডার করুন</a>
          </Button>
        </div>
      </div>
    </div>
  );
}